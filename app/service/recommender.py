import numpy as np
import pickle
from typing import List, Dict, Any, Set
from contextlib import contextmanager
from lightfm import LightFM
from lightfm.data import Dataset
from sqlalchemy.orm import Session, joinedload
from app.db.models import User, Product, ViewCount, Wishlist, WishlistItem, Swipe, SwipeDirection
from app.core.logging import get_logger
from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.redis import get_redis

settings = get_settings()
logger = get_logger("recommender")

class LightFMRecommendationEngine:
    def __init__(self):
        self.model = None
        self.dataset = None
        self.user_id_map = {}
        self.item_id_map = {}
        self.reverse_user_map = {}
        self.reverse_item_map = {}
        self.user_features = None
        self.item_features = None
        self.interactions_matrix = None
        self.is_trained = False
        self.model_version = "2.0.0"

    @contextmanager
    def _get_db_session(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _get_redis(self):
        try:
            return get_redis()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None

    def _get_price_range(self, price: float) -> str:
        """Categorize price into ranges."""
        if price < 300:
            return "ultra_budget"
        elif price < 800:
            return "budget"
        elif price < 1500:
            return "mid_range"
        elif price < 3000:
            return "premium"
        else:
            return "luxury"

    def prepare_data(self, db: Session):
        """Prepare training data for the recommendation model."""
        logger.info("Preparing training data...")

        users = db.query(User).filter(User.STATUS == "ACTIVE").all()
 
        products = db.query(Product).filter(
            Product.ACTIVE == True,
            Product.DELETED_TIME.is_(None)
        ).all()

        if len(users) < 2 or len(products) < 2:
            raise ValueError("Need at least 2 users and 2 products to train the model")

        self.dataset = Dataset()
        user_ids = [str(user.USER_GUID) for user in users]
        item_ids = [str(product.PRODUCT_GUID) for product in products]

        self.dataset.fit(user_ids, item_ids)

        self.user_id_map = {uid: idx for idx, uid in enumerate(user_ids)}
        self.item_id_map = {iid: idx for idx, iid in enumerate(item_ids)}
        self.reverse_user_map = {idx: uid for uid, idx in self.user_id_map.items()}
        self.reverse_item_map = {idx: iid for iid, idx in self.item_id_map.items()}

        interactions = self._build_interactions(db)
 
        if interactions:
            self.interactions_matrix, _ = self.dataset.build_interactions(interactions)
        else:
            dummy_interactions = [(user_ids[0], item_ids[0], 1.0)]
            self.interactions_matrix, _ = self.dataset.build_interactions(dummy_interactions)

        logger.info(f"Prepared {len(interactions)} interactions for {len(user_ids)} users and {len(item_ids)} items")

    def _build_interactions(self, db: Session) -> List[tuple]:
        """Build interaction tuples from database data."""
        interactions = []
 
        try:
            view_counts = db.query(ViewCount).all()
            for vc in view_counts:
                user_id_str = str(vc.user_id) 
                product_id_str = str(vc.product_id) 
                if user_id_str in self.user_id_map and product_id_str in self.item_id_map:
                    weight = min(vc.count / 10.0, 2.0) + 1.0 
                    interactions.append((user_id_str, product_id_str, weight))
            logger.info(f"Processed {len(view_counts)} view counts")
        except Exception as e:
            logger.warning(f"Error processing view counts: {e}")
 
        try:
            wishlist_items = (db.query(WishlistItem)
                            .join(Wishlist)
                            .options(joinedload(WishlistItem.wishlist))
                            .all())
 
            for wi in wishlist_items:
                user_id_str = str(wi.wishlist.user_id)  
                product_id_str = str(wi.product_id)  
                if (user_id_str in self.user_id_map and
                    product_id_str in self.item_id_map):
                    interactions.append((user_id_str, product_id_str, 3.0))
            logger.info(f"Processed {len(wishlist_items)} wishlist items")
        except Exception as e:
            logger.warning(f"Error processing wishlist items: {e}")
 
        try:
            swipes = db.query(Swipe).all()
            for swipe in swipes:
                user_id_str = str(swipe.user_guid)
                product_id_str = str(swipe.product_guid)
                if user_id_str in self.user_id_map and product_id_str in self.item_id_map:
                    if swipe.direction == SwipeDirection.LIKE:
                        weight = 2.5
                    elif swipe.direction == SwipeDirection.CART:
                        weight = 4.0 
                    else:  
                        weight = 0.1  
                    interactions.append((user_id_str, product_id_str, weight))
            logger.info(f"Processed {len(swipes)} swipes")
        except Exception as e:
            logger.warning(f"Error processing swipes: {e}")
 
        return interactions

    def prepare_features(self, db: Session):
        """Prepare user and item features for the model."""
        logger.info("Preparing features...")

        try:
            item_features = self._build_item_features(db)
            user_features = self._build_user_features(db)

            all_item_features = set()
            for _, features in item_features:
                all_item_features.update(features)
            
            all_user_features = set()
            for _, features in user_features:
                all_user_features.update(features)

            if all_item_features or all_user_features:
                self.dataset.fit_partial(
                    item_features=list(all_item_features),
                    user_features=list(all_user_features)
                )

            if item_features:
                self.item_features = self.dataset.build_item_features(item_features)
            if user_features:
                self.user_features = self.dataset.build_user_features(user_features)

            logger.info(f"Built features for {len(item_features)} items and {len(user_features)} users")
            logger.info(f"Item features: {len(all_item_features)}, User features: {len(all_user_features)}")
        except Exception as e:
            logger.warning(f"Feature preparation failed: {e}")
            self.item_features = None
            self.user_features = None

    def _build_item_features(self, db: Session) -> List[tuple]:
        """Build item features from product data."""
        item_features = []
 
        products = db.query(Product).filter(
            Product.ACTIVE == True,
            Product.DELETED_TIME.is_(None)
        ).all()

        for product in products:
            product_id_str = str(product.PRODUCT_GUID)
            if product_id_str in self.item_id_map:
                features = []
 
                if product.CATEGORY_SLUG:
                    features.append(f"category:{product.CATEGORY_SLUG.lower()}")
                if product.BRAND:
                    features.append(f"brand:{product.BRAND.lower()}")
                if product.GENDER:
                    features.append(f"gender:{product.GENDER.lower()}")
                if product.PRICE:
                    features.append(f"price_range:{self._get_price_range(product.PRICE)}")

                if features:
                    item_features.append((product_id_str, features))
 
        return item_features

    def _build_user_features(self, db: Session) -> List[tuple]:
        """Build user features from user activity data."""
        user_features = []
 
        users = (db.query(User)
                .filter(User.STATUS == "ACTIVE")
                .options(joinedload(User.view_counts))
                .all())

        for user in users:
            user_id_str = str(user.USER_GUID)
            if user_id_str in self.user_id_map:
                features = []
 
                total_views = sum(vc.count for vc in user.view_counts) 
 
                if total_views > 50:
                    features.append("activity:high")
                elif total_views > 10:
                    features.append("activity:medium")
                else:
                    features.append("activity:low")

                try:
                    user_swipes = db.query(Swipe).filter(Swipe.user_guid == user_id_str).all()
                    like_count = sum(1 for s in user_swipes if s.direction == SwipeDirection.LIKE)
                    dislike_count = sum(1 for s in user_swipes if s.direction == SwipeDirection.DISLIKE)
                    
                    if like_count > dislike_count * 2:
                        features.append("preference:positive")
                    elif dislike_count > like_count * 2:
                        features.append("preference:negative")
                    else:
                        features.append("preference:balanced")
                except Exception as e:
                    logger.warning(f"Error processing user swipes for features: {e}")

                if features:
                    user_features.append((user_id_str, features))
 
        return user_features

    def train_model(self):
        """Train the LightFM recommendation model."""
        with self._get_db_session() as db:
            logger.info("Training LightFM model...")
            self.prepare_data(db)
            self.prepare_features(db)

            self.model = LightFM(
                loss='warp',
                learning_rate=settings.MODEL_LEARNING_RATE,
                item_alpha=settings.MODEL_ITEM_ALPHA,
                user_alpha=settings.MODEL_USER_ALPHA,
                max_sampled=settings.MODEL_MAX_SAMPLED,
                random_state=settings.MODEL_RANDOM_STATE
            )

            self.model.fit(
                interactions=self.interactions_matrix,
                user_features=self.user_features,
                item_features=self.item_features,
                epochs=settings.MODEL_EPOCHS,
                num_threads=settings.MODEL_NUM_THREADS,
                verbose=True
            )

            self.is_trained = True
            logger.info("Model training completed successfully")

    def get_recommendations(self, user_id: str, num_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Get recommendations for a user."""
        redis_client = self._get_redis()
        cache_key = f"recommendations:{user_id}:{num_recommendations}"
    
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    return pickle.loads(cached.encode('latin-1'))
            except Exception as e:
                logger.warning(f"Cache retrieval failed: {e}")

        if not self.is_trained:
            try:
                self.train_model()
            except Exception as e:
                logger.error(f"Model training failed: {e}")
                with self._get_db_session() as db:
                    result = self._get_popular_items(db, num_recommendations)
                    logger.info(f"Using popular items fallback: {result}")
                    return result

        with self._get_db_session() as db:
            if user_id not in self.user_id_map:
                result = self._get_popular_items(db, num_recommendations)
                logger.info(f"User not in map, using popular items: {result}")
            else:
                result = self._generate_recommendations(db, user_id, num_recommendations)
                logger.info(f"Generated recommendations: {result}")

            if redis_client and result:
                try:
                    redis_client.setex(
                        cache_key,
                        settings.RECOMMENDATION_CACHE_TTL,
                        pickle.dumps(result).decode('latin-1')
                    )
                except Exception as e:
                    logger.warning(f"Cache storage failed: {e}")
    
            return result

    def _generate_recommendations(self, db: Session, user_id: str, num_recommendations: int) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for a user."""
        user_idx = self.user_id_map[user_id]
        item_indices = list(range(len(self.item_id_map)))

        try:
            scores = self.model.predict(
                user_ids=user_idx,
                item_ids=item_indices,
                user_features=self.user_features,
                item_features=self.item_features,
                num_threads=settings.MODEL_NUM_THREADS
            )

            top_indices = np.argsort(scores)[::-1][:num_recommendations * 3]
            user_interactions = self._get_user_interactions(db, user_id)

            recommendations = []
            for idx in top_indices:
                if len(recommendations) >= num_recommendations:
                    break

                product_id = self.reverse_item_map[idx]
                if product_id not in user_interactions:
                    product = db.query(Product).filter(Product.PRODUCT_GUID == product_id).first()
                    if product and product.ACTIVE and product.DELETED_TIME is None:
                        recommendations.append({
                            'PRODUCT_GUID': product_id,
                            'PRODUCT_NAME': product.PRODUCT_NAME, 
                            'DESCRIPTION': product.DESCRIPTION,  
                            'PRICE': product.PRICE,  
                            'IMAGE_PATH': product.IMAGE_PATH,  
                            'BRAND': product.BRAND,  
                            'CATEGORY_SLUG': product.CATEGORY_SLUG  
                            })

            return recommendations or self._get_popular_items(db, num_recommendations)
 
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return self._get_popular_items(db, num_recommendations)

    def _get_user_interactions(self, db: Session, user_id: str) -> Set[str]:
        """Get all products the user has already interacted with."""
        user_interactions = set()

        try:
            viewed_products = db.query(ViewCount.product_id).filter(
                ViewCount.user_id == user_id  
            ).all()
            user_interactions.update(str(vc[0]) for vc in viewed_products)
        except Exception as e:
            logger.warning(f"Error getting viewed products: {e}")

        try:
            wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()  
            if wishlist:
                wishlist_items = db.query(WishlistItem.product_id).filter(
                    WishlistItem.wishlist_id == wishlist.id 
                ).all()
                user_interactions.update(str(wi[0]) for wi in wishlist_items)
        except Exception as e:
            logger.warning(f"Error getting wishlist products: {e}")

        try:
            swipe_products = db.query(Swipe.product_guid).filter(
                Swipe.user_guid == user_id
            ).all()
            user_interactions.update(str(sp[0]) for sp in swipe_products)
        except Exception as e:
            logger.warning(f"Error getting swiped products: {e}")

        return user_interactions

    def _get_popular_items(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular items based on wishlist count and swipes"""
        try:
            popular_items = db.query(Product).filter(
                Product.ACTIVE == True,
                Product.DELETED_TIME.is_(None)
            ).order_by(
                Product.WISHLIST_COUNT.desc()
            ).limit(limit).all()
    
            return [{
                'PRODUCT_GUID': str(item.PRODUCT_GUID),  
                'PRODUCT_NAME': item.PRODUCT_NAME,       
                'DESCRIPTION': item.DESCRIPTION,        
                'PRICE': item.PRICE,                     
                'IMAGE_PATH': item.IMAGE_PATH,          
                'BRAND': item.BRAND,                     
                'CATEGORY_SLUG': item.CATEGORY_SLUG     
            } for item in popular_items]
        except Exception as e:
            logger.error(f"Failed to get popular items: {e}")
            return []

    def save_model(self, filepath: str):
        """Save the trained model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        try:
            import os
            from pathlib import Path
            
            directory = Path(filepath).parent
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'dataset': self.dataset,
                'user_id_map': self.user_id_map,
                'item_id_map': self.item_id_map,
                'reverse_user_map': self.reverse_user_map,
                'reverse_item_map': self.reverse_item_map,
                'user_features': self.user_features,
                'item_features': self.item_features,
                'interactions_matrix': self.interactions_matrix,
                'model_version': self.model_version,
                'is_trained': self.is_trained
            }

            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise

    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            required_keys = ['model', 'dataset', 'user_id_map', 'item_id_map',
                        'reverse_user_map', 'reverse_item_map']
            
            if not all(key in data for key in required_keys):
                raise ValueError("Invalid model file format")
            
            self.model = data['model']
            self.dataset = data['dataset']
            self.user_id_map = data['user_id_map']
            self.item_id_map = data['item_id_map']
            self.reverse_user_map = data['reverse_user_map']
            self.reverse_item_map = data['reverse_item_map']
            self.user_features = data.get('user_features')
            self.item_features = data.get('item_features')
            self.interactions_matrix = data.get('interactions_matrix')
            self.model_version = data.get('model_version', '2.0.0')
            self.is_trained = data.get('is_trained', True)
            
            logger.info(f"Model loaded from {filepath}")
            
        except FileNotFoundError:
            logger.warning(f"Model file {filepath} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

recommendation_engine = LightFMRecommendationEngine()