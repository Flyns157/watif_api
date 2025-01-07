"""
Embedding Module for Social Media Recommendation System

This module provides various classes to handle embeddings for entities within a social media platform.
The main purpose of these embeddings is to enable personalized recommendations by calculating 
similarities between users, posts, threads, interests, and other social media entities.

Classes:
    - embedder: A base class for generating embeddings using a specified language model.
    - local_embedder: A specialized embedder that saves and loads embeddings locally from files.
    - integrated_embedder: An embedder that integrates with a Database instance for retrieving entity embeddings.
    - watif_embedder: An abstract class defining methods for getting various types of embeddings 
      (e.g., user, post, thread) but leaves implementation to child classes.
    - watif_local_embedder: Combines functionality of local_embedder and watif_embedder, managing local embeddings for each type.
    - watif_integrated_embedder: Extends integrated_embedder and watif_embedder, handling embeddings that interact with a Database instance.
    - MC_embedder: A fully integrated embedder that retrieves and processes embeddings for users, posts, and threads with 
      configurable weights for different entity attributes (e.g., interests, follow connections) to create personalized embeddings.

Functions:
    - get_user_embedding: Generates an embedding for a user, weighted by interests, follow connections, and description.
    - get_post_embedding: Generates an embedding for a post, weighted by keys, title, content, and author.
    - get_thread_embedding: Generates an embedding for a thread, weighted by attributes like author, members, and related posts.
    - get_key_embedding: Retrieves the embedding for a specific keyword.
    - get_interest_embedding: Retrieves the embedding for a specific interest.
    - _get_embedding: Utility function to get an entity embedding from the database.

Examples:
    # Initialize an MC_embedder with a database instance and model
    mc_embedder = MC_embedder(db=database, model='all-MiniLM-L6-v2')

    # Generate and retrieve user embedding based on attributes and weighting
    user_embedding = mc_embedder.get_user_embedding(id_user='123', follow_weight=0.5, interest_weight=0.3, description_weight=0.2)

Requirements:
    - `numpy`: For handling embedding arrays.
    - `scikit-learn`: For cosine similarity calculations.
    - `sentence-transformers`: For the language model used to generate embeddings.

"""

from sentence_transformers import SentenceTransformer
import numpy as np
import os

from ...database import Database


class embedder(object):
    """Embedder using SentenceTransformer for encoding textual objects."""
    def __init__(self, model: str = 'all-MiniLM-L6-v2', *args, **kwargs) -> None:
        """
        Initializes the embedder with a specified model.

        Args:
            model (str): Model name for SentenceTransformer.
            *args: Additional arguments for SentenceTransformer.
            **kwargs: Additional keyword arguments for SentenceTransformer.
        """
        self.model = SentenceTransformer(model, *args, **kwargs)

    def encode(self, obj: object, show_progress_bar: bool = True, *args, **kwargs) -> np.ndarray:
        """
        Encodes an object to generate embeddings.

        Args:
            obj (object): Object to encode.
            show_progress_bar (bool): Display progress bar.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: Encoded embedding.
        """
        return self.model.encode(obj, show_progress_bar=show_progress_bar, *args, **kwargs)


class local_embedder:
    """Embedder class with local saving/loading capabilities for embeddings."""

    def __init__(self, model: str = 'all-MiniLM-L6-v2', *args, **kwargs) -> None:
        """
        Initializes the local embedder.

        Args:
            model (str): Model name for SentenceTransformer.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(model, *args, **kwargs)
        self.filext = '_embeddings.npy'

    def load_embeddings(self, path):
        """
        Loads embeddings from a file or returns an empty dictionary if the file doesn't exist.

        Args:
            path (str): Path to the embeddings file.

        Returns:
            dict: Loaded embeddings or an empty dictionary.
        """
        if os.path.exists(path):
            return np.load(path, allow_pickle=True).item()
        return {}

    def save_embeddings(self, embeddings, path):
        """
        Saves embeddings to a file.

        Args:
            embeddings (dict): Embeddings to save.
            path (str): Path to the output file.
        """
        np.save(path, embeddings)


class integrated_embedder(embedder):
    """Embedder that integrates with a database for storing embeddings."""

    def __init__(self, db: Database, model: str = 'all-MiniLM-L6-v2', *args, **kwargs) -> None:
        """
        Initializes the integrated embedder with database access.

        Args:
            db (Database): Database instance.
            model (str): Model name for SentenceTransformer.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(model, *args, **kwargs)
        self.db = db


class watif_embedder(object):
    """Abstract class defining methods to retrieve specific entity embeddings."""

    def get_user_embeddings(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_post_embeddings(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_thread_embeddings(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_interest_embeddings(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_key_embeddings(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_user_embedding(self, id_user: str | int | bytes, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_post_embedding(self, id_post: str | int | bytes, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_thread_embedding(self, id_thread: str | int | bytes, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_interest_embedding(self, id_interest: str | int | bytes, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def get_key_embedding(self, id_key: str | int | bytes, *args, **kwargs) -> np.ndarray:
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def encode(self, obj: object, *args, **kwargs) -> np.ndarray | dict:
        raise NotImplementedError('Must be implemented in subclass / child class.')


class watif_local_embedder(local_embedder, watif_embedder):
    """Combines local_embedder and watif_embedder to store and retrieve entity embeddings locally."""
    pass


class watif_integrated_embedder(integrated_embedder, watif_embedder):
    """Combines integrated_embedder and watif_embedder for entity embedding management with database integration."""
    pass

from .mc_core import MC_embedder
