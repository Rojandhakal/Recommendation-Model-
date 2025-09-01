import os
import pickle
import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from app import crud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Globals
# -----------------------------
GLOBAL_DATASET = None
GLOBAL_MODEL = None
GLOBAL_ITEM_FEATURES_MATRIX = None

# -----------------------------
# Model path setup
# -----------------------------
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "lightfm_model.pkl")
print(f"Model will be saved/loaded from: {MODEL_PATH}")

# -----------------------------
# Initialize / Load Model
# -----------------------------
def initialize_model(db, force_retrain=False):
    """
    Initialize or retrain LightFM model and save it as a .pkl file.
    """
    global GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX

    if not force_retrain and os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX = pickle.load(f)
            print(f"Loaded saved LightFM model from {MODEL_PATH}!")
            return
        except Exception as e:
            print("Failed to load model, retraining:", e)

    # Step 1: Build dataset
    dataset, interactions_matrix, item_features_matrix = build_dataset(db)
    print(f"Step 1: Dataset ready with {interactions_matrix.shape[0]} users and {interactions_matrix.shape[1]} items")

    # Step 2: Train model
    model = train_model(interactions_matrix, item_features_matrix)

    # Update globals
    GLOBAL_DATASET = dataset
    GLOBAL_MODEL = model
    GLOBAL_ITEM_FEATURES_MATRIX = item_features_matrix

    # Step 3: Save model as .pkl
    try:
        print(f"Step 3: Saving model to {MODEL_PATH}...")
        with open(MODEL_PATH, "wb") as f:
            pickle.dump((GLOBAL_DATASET, GLOBAL_MODEL, GLOBAL_ITEM_FEATURES_MATRIX), f)
        print("Step 4: Model saved successfully!")
    except Exception as e:
        print("Failed to save model:", e)


# -----------------------------
# Build item features
# -----------------------------
def build_item_features(db):
    products = crud.get_all_products(db)
    item_features = []

    for p in products:
        features = []
        for attr in ['color', 'category', 'subcategory', 'description', 'condition', 'brand', 'size']:
            val = getattr(p, attr, None)
            if val:
                features.append(f"{attr}:{val}")
        item_features.append((p.id, features))

    return item_features

# -----------------------------
# Build dataset
# -----------------------------
def build_dataset(db):
    users = [u.id for u in crud.get_all_users(db)]
    products = [p.id for p in crud.get_all_products(db)]

    interactions = []
    for user_id in users:
        liked_products = crud.get_user_likes(db, user_id)
        liked_products = [p[0] for p in liked_products]
        for product_id in liked_products:
            interactions.append((user_id, product_id))

    item_features = build_item_features(db)
    feature_list = list({f for _, f_list in item_features for f in f_list})

    dataset = Dataset()
    dataset.fit(users=users, items=products, item_features=feature_list)

    item_features_matrix = dataset.build_item_features(item_features)
    interactions_matrix, _ = dataset.build_interactions(interactions)

    print(f"Interactions matrix shape: {interactions_matrix.shape}")
    return dataset, interactions_matrix, item_features_matrix

# -----------------------------
# Train model
# -----------------------------
def train_model(interactions_matrix, item_features_matrix, epochs=10):
    print("Step 2: Training model...")
    model = LightFM(loss='logistic') 
    model.fit(interactions_matrix, item_features=item_features_matrix, epochs=epochs, num_threads=1)
    print("Step 2: Model training completed.")
    return model



# -----------------------------
# Content-based recommendations
# -----------------------------
def recommend_content_based(liked_ids, db, top_k=4):
    products = crud.get_all_products(db)
    if not liked_ids or not products:
        return []

    corpus = {p.id: f"{p.color} {p.category} {p.subcategory} {p.description or ''}" for p in products}
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(corpus.values())
    id_list = list(corpus.keys())

    liked_indices = [id_list.index(pid) for pid in liked_ids if pid in id_list]
    if not liked_indices:
        return []

    liked_vec = X[liked_indices].mean(axis=0)
    sim_matrix = cosine_similarity(liked_vec.A, X).flatten()  # Add .A to convert matrix to array
    ranked_idx = np.argsort(-sim_matrix)

    ranked_ids = [id_list[i] for i in ranked_idx if id_list[i] not in liked_ids]
    return ranked_ids[:top_k]

# -----------------------------
# Random recommendations
# -----------------------------
def recommend_random(db, exclude_ids=[], top_k=3):
    all_products = [p.id for p in crud.get_all_products(db) if p.id not in exclude_ids]
    if not all_products:
        return []
    return list(np.random.choice(all_products, size=min(top_k, len(all_products)), replace=False))

# -----------------------------
# Recommend products (40/30/30 mix)
# -----------------------------
def recommend_products(user_id, num_recs=10, db=None):
    global GLOBAL_MODEL, GLOBAL_DATASET, GLOBAL_ITEM_FEATURES_MATRIX
    if not GLOBAL_MODEL or not GLOBAL_DATASET:
        print("Model not loaded yet.")
        return []

    user_map, _, item_map, _ = GLOBAL_DATASET.mapping()
    if user_id not in user_map:
        return recommend_random(db, top_k=num_recs)

    internal_user_id = user_map[user_id]
    _, n_items = GLOBAL_DATASET.interactions_shape()

    scores = GLOBAL_MODEL.predict(internal_user_id, np.arange(n_items), item_features=GLOBAL_ITEM_FEATURES_MATRIX)
    collab_ranked = np.argsort(-scores)
    reverse_item_map = {v: k for k, v in item_map.items()}
    collab_ids = [reverse_item_map[i] for i in collab_ranked]

    liked_products = [p[0] for p in crud.get_user_likes(db, user_id)]

    content_ids = recommend_content_based(liked_products, db, top_k=4)
    collab_ids = [p for p in collab_ids if p not in content_ids and p not in liked_products][:3]
    exclude = set(content_ids + collab_ids + liked_products)
    random_ids = recommend_random(db, exclude_ids=list(exclude), top_k=3)

    final_recs = content_ids + collab_ids + random_ids
    return final_recs[:num_recs]
