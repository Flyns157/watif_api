"""
Recommendation engine by Mattéo, using embedding on the MongoDB database.
"""
import numpy as np
from torch import cosine_similarity
from ..database import Database
from . import recommender_engine
from .embedding import MC_embedder
from .. import main_logger


class EM_engine(recommender_engine):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.embedder = MC_embedder(db, logger=main_logger)

    def _get_embedding(self, entity_type: str, entity_id: int |str | bytes) -> np.ndarray:
        """
        Retrieve the embedding vector for a given entity from MongoDB.
        
        Args:
            entity_type (str): The type of entity (e.g., 'user', 'post', 'thread').
            entity_id (str): The ID of the entity.
        
        Returns:
            np.ndarray: The embedding vector for the entity.
        """
        self.embedder.encode(entity_type, entity_id)

    def recommend_users(self, id_user, top_n=50):
        """
        Recommend users based on similarity of embeddings.
        
        Args:
            id_user (str): The ID of the user.
            top_n (int): The number of recommendations to return.

        Returns:
            list: A list of recommended user IDs.
        """
        user_embedding = self._get_embedding("users", id_user)
        if user_embedding is None:
            return []
        
        # Fetch all users' embeddings except the target user
        users = list(self.db.mongo_db["users"].find({"_id": {"$ne": id_user}}, {"_id": 1, "embedding": 1}))
        
        user_ids = []
        user_embeddings = []
        for user in users:
            user_ids.append(user["_id"])
            user_embeddings.append(np.array(self._get_embedding("user", user["_id"])))

        # Calculate cosine similarity between the target user and all other users
        user_embeddings = np.vstack(user_embeddings)
        similarities = cosine_similarity([user_embedding], user_embeddings).flatten()
        
        # Get top N similar users
        recommended_ids = [user_ids[i] for i in np.argsort(similarities)[-top_n:][::-1]]
        return recommended_ids

    def recommend_posts(self, id_user, top_n=50):
        """
        Recommend posts based on similarity of embeddings between user and posts.
        
        Args:
            id_user (str): The ID of the user.
            top_n (int): The number of posts to recommend.

        Returns:
            list: A list of recommended post IDs.
        """
        user_embedding = self._get_embedding("user", id_user)
        if user_embedding is None:
            return []
        
        # Fetch all posts' embeddings
        posts = list(self.db.mongo_db["posts"].find({}, {"_id": 1, "embedding": 1}))
        
        post_ids = []
        post_embeddings = []
        for post in posts:
            post_ids.append(post["_id"])
            post_embeddings.append(np.array(self._get_embedding("post", post["_id"])))

        # Calculate cosine similarity between the user and all posts
        post_embeddings = np.vstack(post_embeddings)
        similarities = cosine_similarity([user_embedding], post_embeddings).flatten()
        
        # Get top N similar posts
        recommended_ids = [post_ids[i] for i in np.argsort(similarities)[-top_n:][::-1]]
        return recommended_ids

    def recommend_threads(self, id_user, top_n=50):
        """
        Recommend threads based on similarity of embeddings between user and threads.
        
        Args:
            id_user (str): The ID of the user.
            top_n (int): The number of threads to recommend.

        Returns:
            list: A list of recommended thread IDs.
        """
        user_embedding = self._get_embedding("user", id_user)
        if user_embedding is None:
            return []
        
        # Fetch all threads' embeddings
        threads = list(self.db.mongo_db["threads"].find({}, {"_id": 1, "embedding": 1}))
        
        thread_ids = []
        thread_embeddings = []
        for thread in threads:
            if "embedding" in thread:
                thread_ids.append(thread["_id"])
                thread_embeddings.append(np.array(self._get_embedding("thread", thread["_id"])))

        # Calculate cosine similarity between the user and all threads
        thread_embeddings = np.vstack(thread_embeddings)
        similarities = cosine_similarity([user_embedding], thread_embeddings).flatten()
        
        # Get top N similar threads
        recommended_ids = [thread_ids[i] for i in np.argsort(similarities)[-top_n:][::-1]]
        return recommended_ids
