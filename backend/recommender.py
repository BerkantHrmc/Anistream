import pickle
import numpy as np
import os
from models import Anime

class Recommender:
    def __init__(self, models_dir='../models'):
        self.models_dir = models_dir
        self.model = None
        self.id_mappings = None
        self.item_features = None
        self.train_matrix = None
        self.item_id_map = None      # mal_id -> internal_idx
        self.reverse_item_map = None # internal_idx -> mal_id
        self._load_models()

    def _load_models(self):
        try:
            import lightfm # Check if lightfm is installed
            
            with open(os.path.join(self.models_dir, 'hybrid_lightfm_model.pkl'), 'rb') as f:
                self.model = pickle.load(f)

            with open(os.path.join(self.models_dir, 'id_mappings.pkl'), 'rb') as f:
                mappings = pickle.load(f)
                if isinstance(mappings, dict):
                    self.item_id_map = mappings.get('anime_id_map', {})
                else:
                    self.item_id_map = mappings[1]
                # Build reverse map: internal_idx -> mal_id (as native int)
                self.reverse_item_map = {int(v): int(k) for k, v in self.item_id_map.items()}

            with open(os.path.join(self.models_dir, 'item_features.pkl'), 'rb') as f:
                features_data = pickle.load(f)
                if isinstance(features_data, dict) and 'item_features_matrix' in features_data:
                    self.item_features = features_data['item_features_matrix']
                else:
                    self.item_features = features_data

            with open(os.path.join(self.models_dir, 'train_test_matrices.pkl'), 'rb') as f:
                matrices = pickle.load(f)
                self.train_matrix = matrices['train'].tocsr()

            print(f"Successfully loaded LightFM hybrid model. "
                  f"Users: {self.train_matrix.shape[0]}, Items: {self.train_matrix.shape[1]}")
        except ImportError:
            print("Warning: LightFM is not installed. Recommendation engine will use fallback mode (top-rated).")
        except Exception as e:
            print(f"Warning: Could not load recommendation models. Error: {e}")

    def _find_nearest_neighbor_user(self, user_ratings_dict):
        """
        Find the most similar user in the training matrix based on
        the website user's ratings. Returns the internal user index.
        
        user_ratings_dict: {mal_id (int): rating (int), ...}
        """
        if not user_ratings_dict or self.train_matrix is None:
            return 0  # cold start: use user 0 as default

        # Build a sparse-like rating vector for the current user
        n_items = self.train_matrix.shape[1]
        user_vector = np.zeros(n_items, dtype=np.float32)
        rated_count = 0
        for mal_id, rating in user_ratings_dict.items():
            internal_idx = self.item_id_map.get(mal_id)
            if internal_idx is not None:
                user_vector[int(internal_idx)] = float(rating)
                rated_count += 1

        if rated_count == 0:
            return 0  # no overlap with model items

        # Normalize user vector
        user_norm = np.linalg.norm(user_vector)
        if user_norm == 0:
            return 0
        user_vector_norm = user_vector / user_norm

        # Compute dot product similarity against all training users
        # train_matrix is CSR: shape (275473, 16577)
        # This gives cosine-like similarity scores
        similarities = self.train_matrix.dot(user_vector_norm)
        
        # Normalize by training user norms
        train_norms = np.sqrt(self.train_matrix.power(2).sum(axis=1)).A1
        train_norms[train_norms == 0] = 1e-10
        similarities = similarities / train_norms

        # Return the internal index of the most similar user
        best_user_idx = int(np.argmax(similarities))
        best_sim = float(similarities[best_user_idx])
        print(f"[Recommender] Nearest neighbor: user_idx={best_user_idx}, similarity={best_sim:.4f}")
        return best_user_idx

    def get_recommendations(self, user_id, num_recs=12, survey_data=None, liked_anime_ids=None):
        recommendations = []

        if self.model is None or self.train_matrix is None:
            return self._fallback(num_recs)

        # 1. Get user's ratings from the web DB
        from models import Rating
        user_db_ratings = Rating.query.filter_by(user_id=user_id).all()
        user_ratings_dict = {r.anime_id: r.rating for r in user_db_ratings}

        # 2. Find the most similar user in the training data
        internal_user_id = self._find_nearest_neighbor_user(user_ratings_dict)

        # 3. Use LightFM's TRUE hybrid predict (CF + Content embeddings together)
        n_items = self.train_matrix.shape[1]
        item_ids = np.arange(n_items)
        scores = self.model.predict(
            internal_user_id,
            item_ids,
            item_features=self.item_features
        )

        # 4. Get top candidates
        top_items_internal = np.argsort(-scores)[:200]

        candidates = []
        for iid in top_items_internal:
            real_anime_id = self.reverse_item_map.get(int(iid))
            if real_anime_id is None:
                continue
            if liked_anime_ids and real_anime_id in liked_anime_ids:
                continue
            # Skip already rated anime by the user
            if real_anime_id in user_ratings_dict:
                continue
            anime = Anime.query.filter_by(mal_id=real_anime_id).first()
            if anime:
                # Hard filter: Ignore any anime with a score below 7.0 or no score
                if anime.score is None or anime.score < 7.0:
                    continue
                    
                candidates.append({
                    "anime_id": real_anime_id,
                    "title": anime.title,
                    "score": anime.score,
                    "genres": anime.genres,
                    "image_url": anime.image_url,
                    "model_score": float(scores[iid])
                })
            if len(candidates) >= num_recs * 3:
                break

        # 5. Apply soft survey weighting (bonus, not hard filter)
        if survey_data and candidates:
            preferred_genres = [g.strip() for g in survey_data.genres.split(',')] if survey_data.genres else []
            min_score = survey_data.min_score or 0
            for cand in candidates:
                weight = 1.0
                if cand["genres"] and preferred_genres:
                    cand_genres = [g.strip() for g in cand["genres"].split(',')]
                    match_count = len(set(cand_genres).intersection(set(preferred_genres)))
                    weight += match_count * 0.3
                if cand["score"] and cand["score"] >= min_score:
                    weight += 0.1
                cand["final_score"] = cand["model_score"] * weight
        else:
            for cand in candidates:
                cand["final_score"] = cand["model_score"]

        candidates.sort(key=lambda x: x["final_score"], reverse=True)
        recommendations = candidates[:num_recs]

        if not recommendations:
            return self._fallback(num_recs)

        return recommendations

    def _fallback(self, num_recs):
        """Return top-rated anime from DB as fallback."""
        top_animes = Anime.query.filter(Anime.score != None).order_by(Anime.score.desc()).limit(num_recs).all()
        return [
            {
                "anime_id": a.mal_id,
                "title": a.title,
                "score": a.score,
                "genres": a.genres,
                "image_url": a.image_url,
                "model_score": a.score or 0
            }
            for a in top_animes
        ]

    def get_similar_items(self, mal_id, num_recs=10):
        """
        Find similar anime using item representations from the hybrid LightFM model.
        Uses item embeddings (which encode both CF and content-based signals).
        """
        import re
        def is_same_franchise(title1, title2):
            if not title1 or not title2: return False
            t1 = re.sub(r'[^a-z0-9\s]', '', title1.lower())
            t2 = re.sub(r'[^a-z0-9\s]', '', title2.lower())
            words1, words2 = t1.split(), t2.split()
            if not words1 or not words2: return False
            match_len = min(2, len(words1), len(words2))
            if words1[:match_len] == words2[:match_len]: return True
            if len(t1) > 8 and t1 in t2: return True
            if len(t2) > 8 and t2 in t1: return True
            return False

        target_anime = Anime.query.filter_by(mal_id=mal_id).first()
        target_title = target_anime.title if target_anime else ""

        franchise_animes = []
        similar_animes = []

        if self.model is None or self.item_id_map is None:
            return {"franchise": [], "similar": self._fallback(num_recs)}

        internal_item_id = self.item_id_map.get(mal_id)
        if internal_item_id is None:
            internal_item_id = self.item_id_map.get(np.int64(mal_id))

        if internal_item_id is not None:
            internal_item_id = int(internal_item_id)
            # Get full item representations (latent + feature biases)
            _, item_embeddings = self.model.get_item_representations(self.item_features)
            target_embedding = item_embeddings[internal_item_id]

            # Cosine similarity
            dot_products = item_embeddings.dot(target_embedding)
            norms = np.linalg.norm(item_embeddings, axis=1) * np.linalg.norm(target_embedding)
            norms[norms == 0] = 1e-10
            cosine_sim = dot_products / norms

            top_items_internal = np.argsort(-cosine_sim)[:150]

            for iid in top_items_internal:
                if int(iid) == internal_item_id:
                    continue
                real_anime_id = self.reverse_item_map.get(int(iid))
                if real_anime_id is None:
                    continue
                anime = Anime.query.filter_by(mal_id=real_anime_id).first()
                if not anime:
                    continue
                item = {
                    "anime_id": real_anime_id,
                    "title": anime.title,
                    "score": anime.score,
                    "genres": anime.genres
                }
                if is_same_franchise(target_title, anime.title):
                    if len(franchise_animes) < num_recs:
                        franchise_animes.append(item)
                else:
                    if len(similar_animes) < num_recs:
                        similar_animes.append(item)

                if len(similar_animes) >= num_recs and len(franchise_animes) >= 5:
                    break

        if not similar_animes:
            similar_animes = self._fallback(num_recs)

        return {"franchise": franchise_animes[:num_recs], "similar": similar_animes[:num_recs]}

    def get_unrated_recommendations(self, user_id, num_recs=12, survey_data=None, liked_anime_ids=None):
        from models import Rating, Anime, db
        
        # Get the user's latest 5 ratings
        latest_ratings = Rating.query.filter_by(user_id=user_id).order_by(Rating.timestamp.desc()).limit(5).all()
        user_db_ratings = Rating.query.filter_by(user_id=user_id).all()
        user_ratings_dict = {r.anime_id: True for r in user_db_ratings}
        
        preferred_genres = set()
        
        # If user has rated at least 5 animes, use their genres dynamically
        if len(latest_ratings) >= 5:
            for r in latest_ratings:
                anime = Anime.query.filter_by(mal_id=r.anime_id).first()
                if anime and anime.genres:
                    for g in anime.genres.split(','):
                        preferred_genres.add(g.strip())
        else:
            # Fallback to survey data if they haven't rated enough
            if survey_data and survey_data.genres:
                for g in survey_data.genres.split(','):
                    preferred_genres.add(g.strip())
                    
        if not preferred_genres:
            return []
            
        # Fetch animes with no score or 0 score
        unrated_animes = Anime.query.filter(db.or_(Anime.score == None, Anime.score == 0.0)).limit(1000).all()
        
        candidates = []
        for anime in unrated_animes:
            if anime.mal_id in user_ratings_dict:
                continue
            if liked_anime_ids and anime.mal_id in liked_anime_ids:
                continue
                
            a_genres = [g.strip() for g in anime.genres.split(',')] if anime.genres else []
            match_count = len(set(a_genres).intersection(preferred_genres))
            
            if match_count > 0:
                candidates.append({
                    "anime_id": anime.mal_id,
                    "title": anime.title,
                    "score": anime.score,
                    "genres": anime.genres,
                    "image_url": anime.image_url,
                    "match_count": match_count
                })
                
        # Sort by match count descending
        candidates.sort(key=lambda x: x["match_count"], reverse=True)
        return candidates[:num_recs]
