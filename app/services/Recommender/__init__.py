"""
This module defines the structure and implementation of a recommendation engine for social networks,
focused on suggesting users, posts, and threads based on shared connections and interests. It
provides an abstract base class `recommender_engine` with unimplemented recommendation methods,
and two concrete classes, `MC_engine` and `JA_engine`, each with distinct recommendation strategies.

Classes:
    recommender_engine: Abstract base class for building a recommendation engine. Provides method
        templates for recommending users, posts, and threads.
    MC_engine: Monte Carlo-based implementation of `recommender_engine`. Suggests users, posts, and
        threads based on mutual connections and engagement patterns.
    JA_engine: A recommendation engine implementation that uses a combination of mutual follows and
        interest-based scores. Provides additional methods for fetching user hashtags and calculating
        recommendation scores.

Usage:
    Create an instance of `Database`, pass it to an `MC_engine` or `JA_engine` instance, and call the
    relevant recommendation methods. For example, `recommend_users(user_id)`, `recommend_posts(user_id)`,
    or `recommend_threads(user_id)`.
"""

from ..database import Database

import numpy as np
import random

class recommender_engine:
    """
    Base class for a recommendation engine in a social network, providing a structure for generating
    recommendations of users, posts, and threads based on various criteria. This class must be extended
    with implementations of the recommendation methods.

    Attributes:
        db (Database): Database instance used for Neo4j interactions.
    """
    
    def __init__(self, db: Database) -> None:
        """
        Initializes the recommender engine with a database connection.

        Parameters:
            db (Database): The Database instance for accessing Neo4j data.
        """
        self.db = db
    
    def recommend_users(self, user_id: str) -> list[str]:
        """
        Recommends users for a specified user to follow. To be implemented in a subclass.

        Parameters:
            user_id (str): The unique identifier of the user for whom recommendations are being generated.

        Returns:
            list[int]: List of recommended user IDs.
        
        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError('Must be implemented in subclass / child class.')

    def recommend_posts(self, user_id: str) -> list[str]:
        """
        Recommends posts for a specified user based on interests and content engagement. To be implemented in a subclass.

        Parameters:
            user_id (str): The unique identifier of the user for whom recommendations are being generated.

        Returns:
            list[str]: List of recommended post IDs.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError('Must be implemented in subclass / child class.')
    
    def recommend_threads(self, user_id: str) -> list[str]:
        """
        Recommends threads for a specified user to join based on shared memberships. To be implemented in a subclass.

        Parameters:
            user_id (str): The unique identifier of the user for whom recommendations are being generated.

        Returns:
            list[str]: List of recommended thread IDs.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError('Must be implemented in subclass / child class.')

from .mc_engine import MC_engine
from .mc_engine import MC_engine
from .ja_engine import JA_engine
