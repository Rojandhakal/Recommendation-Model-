import os
import pickle
import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text

GLOBAL_DATASET = None
GLOBAL_MODEL = None
GLOBAL_ITEM_FEATURES_MATRIX = None

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "lightfm_model.pkl")
print(f"Model will be saved/loaded from: {MODEL_PATH}")


def fetch_users(db):
    """Fetch all active users' GUIDs."""
    rows = db.execute(text(
        "SELECT USER_GUID FROM USERS WHERE STATUS='active'"
    )).fetchall()
    return [r[0] for r in rows]

def get_recommendations(user_guid: str, db=None):
    return recommend_products(user_guid, db=db)

def fetch_products(db):
    """Fetch all active products with relevant attributes."""
    rows = db.execute(text(
        "SELECT PRODUCT_GUID, COLOR, CATEGORY_SLUG, SUB_CATEGORY_ID, DESCRIPTION, BRAND, SIZE "
        "FROM PRODUCT WHERE ACTIVE=1 AND DELETED_TIME IS NULL"
    )).fetchall()

    products = []
    for r in rows:
        products.append({
            "id": r[0],        
            "color": r[1],
            "category": r[2],
            "subcategory": r[3],
            "description": r[4],
            "brand": r[5],
            "size": r[6]
        })
    return products


def fetch_swipes(db):
    """Fetch all likes as (user_guid, product_guid) tuples."""
    rows = db.execute(text(
        "SELECT user_guid, product_guid FROM SWIPES WHERE direction='like'"
    )).fetchall()
    return [(r[0], r[1]) for r in rows]

def build_item_features(db):
    """Build features for each product."""
    products = fetch_products(db)
    item_features = []

    for p in products:
        features = []
        for attr in ['color', 'category', 'subcategory', 'description', 'brand', 'size']:
            val = p.get(attr)
            if val:
                features.append(f"{attr}:{val}")
        item_features.append((p['id'], features))

    return item_features


def build_dataset(db):
    """Create dataset, interactions matrix, and item features matrix."""
    users = fetch_users(db)
    products = [p['id'] for p in fetch_products(db)]
    interactions = fetch_swipes(db)
    item_features = build_item_features(db)

    feature_list = list({f for _, f_list in item_features for f in f_list})
    dataset = Dataset()
    dataset.fit(users=users, items=products, item_features=feature_list)

    item_features_matrix = dataset.build_item_features(item_features)
    interactions_matrix, _ = dataset.build_interactions(interactions)

    print(f"Interactions matrix shape: {interactions_matrix.shape}")
    return dataset, interactions_matrix, item_features_matrix


def train_model(interactions_matrix, item_features_matrix, epochs=10):
    print("Training LightFM model...")
    model = LightFM(loss='logistic')
    model.fit(interactions_matrix, item_features=item_features_matrix, epochs=epochs, num_threads=1)
    print("Model training completed.")
    return model


def initialize_model(db, force_retrain=True):
    global GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX

    if not force_retrain and os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX = pickle.load(f)
            print(f"Loaded saved LightFM model from {MODEL_PATH}!")
            return
        except Exception as e:
            print("Failed to load model, retraining:", e)

    dataset, interactions_matrix, item_features_matrix = build_dataset(db)
    model = train_model(interactions_matrix, item_features_matrix)

    GLOBAL_DATASET = dataset
    GLOBAL_MODEL = model
    GLOBAL_ITEM_FEATURES_MATRIX = item_features_matrix

    with open(MODEL_PATH, "wb") as f:
        pickle.dump((GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX), f)
    print("Model saved successfully!")

def recommend_content_based(liked_ids, db, top_k=4):
    """Recommend products based on content similarity of liked products."""
    products = fetch_products(db)
    if not liked_ids or not products:
        return []

    corpus = {p['id']: f"{p['color']} {p['category']} {p['subcategory']} {p['description'] or ''}" for p in products}
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus.values())
    id_list = list(corpus.keys())

    liked_indices = [id_list.index(pid) for pid in liked_ids if pid in id_list]
    if not liked_indices:
        return []

    liked_vec = X[liked_indices].mean(axis=0)
    sim_matrix = cosine_similarity(liked_vec.A, X).flatten()
    ranked_idx = np.argsort(-sim_matrix)
    ranked_ids = [id_list[i] for i in ranked_idx if id_list[i] not in liked_ids]
    return ranked_ids[:top_k]


def recommend_random(db, exclude_ids=[], top_k=3):
    """Randomly recommend products excluding already seen ones."""
    all_products = [p['id'] for p in fetch_products(db) if p['id'] not in exclude_ids]
    if not all_products:
        return []
    return list(np.random.choice(all_products, size=min(top_k, len(all_products)), replace=False))


def recommend_products(user_guid, num_recs=10, db=None):
    """Return final recommendations for a user (LightFM + content-based + random)."""
    global GLOBAL_MODEL, GLOBAL_DATASET, GLOBAL_ITEM_FEATURES_MATRIX
    if not GLOBAL_MODEL or not GLOBAL_DATASET:
        print("Model not loaded yet.")
        return []

    user_map, _, item_map, _ = GLOBAL_DATASET.mapping()
    if user_guid not in user_map:
        return recommend_random(db, top_k=num_recs)

    internal_user_id = user_map[user_guid]
    _, n_items = GLOBAL_DATASET.interactions_shape()
    scores = GLOBAL_MODEL.predict(internal_user_id, np.arange(n_items), item_features=GLOBAL_ITEM_FEATURES_MATRIX)
    collab_ranked = np.argsort(-scores)
    reverse_item_map = {v: k for k, v in item_map.items()}
    collab_ids = [reverse_item_map[i] for i in collab_ranked]

    swipes = db.execute(text(
        "SELECT product_guid FROM SWIPES WHERE user_guid = :uid AND direction='like'"
    ), {"uid": user_guid}).fetchall()
    liked_products = [p[0] for p in swipes]

    content_ids = recommend_content_based(liked_products, db, top_k=4)

    collab_ids = [p for p in collab_ids if p not in content_ids and p not in liked_products][:3]

    exclude = set(content_ids + collab_ids + liked_products)
    random_ids = recommend_random(db, exclude_ids=list(exclude), top_k=3)

    final_recs = content_ids + collab_ids + random_ids
    return final_recs[:num_recs]
