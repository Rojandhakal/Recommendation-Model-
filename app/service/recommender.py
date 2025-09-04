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


NEW_SWIPES_COUNT = 0
RETRAIN_THRESHOLD = 10 

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "lightfm_model.pkl")

def fetch_users(db):
    rows = db.execute(text("SELECT USER_GUID FROM USERS WHERE STATUS='active'")).fetchall()
    return [r[0] for r in rows]

def fetch_products(db):
    rows = db.execute(text(
        "SELECT PRODUCT_GUID, PRODUCT_NAME, CATEGORY_SLUG, SUB_CATEGORY_ID, DESCRIPTION, BRAND, SIZE, COLOR, USER_GUID, ACTIVE, PRICE "
        "FROM PRODUCT WHERE ACTIVE=1 AND DELETED_TIME IS NULL"
    )).fetchall()

    products = []
    for r in rows:
        products.append({
            "product_guid": r[0],
            "name": r[1],
            "category": r[2],
            "subcategory": r[3],
            "description": r[4],
            "brand": r[5],
            "size": r[6],
            "color": r[7],
            "seller": r[8],
            "condition": r[9],
            "price": r[10]
        })
    return products

def fetch_swipes(db):
    rows = db.execute(text("SELECT user_guid, product_guid FROM SWIPES WHERE direction='like'")).fetchall()
    return [(r[0], r[1]) for r in rows]

def build_item_features(db):
    products = fetch_products(db)
    item_features = []
    for p in products:
        features = []
        for attr in ['color', 'category', 'subcategory', 'description', 'brand', 'size', 'price']:
            val = p.get(attr)
            if val:
                features.append(f"{attr}:{val}")
        item_features.append((p['product_guid'], features))
    return item_features

def build_dataset(db):
    users = fetch_users(db)
    products = fetch_products(db)
    product_ids = set(p['product_guid'] for p in products)

    interactions = [(u, p) for u, p in fetch_swipes(db) if u in users and p in product_ids]

    item_features = build_item_features(db)
    feature_list = list({f for _, f_list in item_features for f in f_list})

    dataset = Dataset()
    dataset.fit(users=users, items=list(product_ids), item_features=feature_list)

    item_features_matrix = dataset.build_item_features(item_features)
    interactions_matrix, _ = dataset.build_interactions(interactions)

    return dataset, interactions_matrix, item_features_matrix

def train_model(interactions_matrix, item_features_matrix, epochs=10):
    model = LightFM(loss='logistic')
    model.fit(interactions_matrix, item_features=item_features_matrix, epochs=epochs, num_threads=1)
    return model

def initialize_model(db, force_retrain=False):
    global GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX

    if not force_retrain and os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX = pickle.load(f)
            return
        except:
            pass

    dataset, interactions_matrix, item_features_matrix = build_dataset(db)
    model = train_model(interactions_matrix, item_features_matrix)

    GLOBAL_DATASET = dataset
    GLOBAL_MODEL = model
    GLOBAL_ITEM_FEATURES_MATRIX = item_features_matrix

    with open(MODEL_PATH, "wb") as f:
        pickle.dump((GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX), f)

def recommend_content_based(liked_ids, db, top_k=4):
    products = fetch_products(db)
    if not liked_ids or not products:
        return []
    corpus = {}
    for p in products:
        features = [
            p.get("color", ""),
            p.get("category", ""),
            p.get("subcategory", ""),
            p.get("description", ""),
            p.get("brand", ""),
            p.get("size", ""),
            str(p.get("price", ""))
        ]
        corpus[p["product_guid"]] = " ".join(str(f) for f in features if f)
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
    all_products = [p['product_guid'] for p in fetch_products(db) if p['product_guid'] not in exclude_ids]
    if not all_products:
        return []
    return list(np.random.choice(all_products, size=min(top_k, len(all_products)), replace=False))

def maybe_retrain_model(db):
    global NEW_SWIPES_COUNT
    if NEW_SWIPES_COUNT >= RETRAIN_THRESHOLD:
        print(f"Retraining model due to {NEW_SWIPES_COUNT} new swipes...")
        initialize_model(db, force_retrain=True)
        NEW_SWIPES_COUNT = 0

def recommend_products(user_guid, num_recs=10, db=None):
    global GLOBAL_MODEL, GLOBAL_DATASET, GLOBAL_ITEM_FEATURES_MATRIX
    maybe_retrain_model(db)

    if not GLOBAL_MODEL or not GLOBAL_DATASET:
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
    swipes = db.execute(text("SELECT product_guid FROM SWIPES WHERE user_guid = :uid AND direction='like'"), {"uid": user_guid}).fetchall()
    liked_products = [p[0] for p in swipes]
    content_ids = recommend_content_based(liked_products, db, top_k=4)
    collab_ids = [p for p in collab_ids if p not in content_ids and p not in liked_products][:3]
    exclude = set(content_ids + collab_ids + liked_products)
    random_ids = recommend_random(db, exclude_ids=list(exclude), top_k=3)
    final_recs = content_ids + collab_ids + random_ids
    return final_recs[:num_recs]

def get_recommendations(user_guid: str, db=None):
    return recommend_products(user_guid, db=db)
