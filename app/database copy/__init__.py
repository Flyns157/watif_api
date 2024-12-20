"""
This module provides a class for managing database connections and synchronizing data between MongoDB and Neo4j.
"""
from pymongo import MongoClient
from neo4j import GraphDatabase
from contextlib import closing

from .auth_database import AuthDatabase
from .synchronizer import Synchronizer

from ..utils.config import Config


class Database(AuthDatabase):
    """
    A class for managing database connections and synchronizing data between MongoDB and Neo4j.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes the `Database` instance with optional MongoDB and Neo4j connections.

        Parameters:
            mongo_uri (str, optional): URI for connecting to MongoDB.
            mongo_db (str, optional): Database name for MongoDB.
            neo4j_uri (str, optional): URI for connecting to Neo4j.
            neo4j_user (str, optional): Username for Neo4j authentication.
            neo4j_password (str, optional): Password for Neo4j authentication.
            config (Config, optional): A Config object containing the database connection settings.
        """
        super().__init__()
        config = kwargs.get('config', args[0] if len(args) == 1 and isinstance(args[0], Config) else None)
        if config:
            self.configurate(config)
        else:
            self.initialize(*args, **kwargs)


    def initialize(self, mongo_uri: str = None, mongo_db: str = None, neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None, db_name: str = 'database') -> None:
        """
        Initializes the `Database` instance with optional MongoDB and Neo4j connections.

        Parameters:
            mongo_uri (str, optional): URI for connecting to MongoDB.
            mongo_db (str, optional): Database name for MongoDB.
            neo4j_uri (str, optional): URI for connecting to Neo4j.
            neo4j_user (str, optional): Username for Neo4j authentication.
            neo4j_password (str, optional): Password for Neo4j authentication.
        """
        try:
            if mongo_uri and mongo_db:
                self.mongo_client = MongoClient(mongo_uri)
                self.mongo_db = self.mongo_client[mongo_db]
            if neo4j_uri:
                self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            self.sync = Synchronizer(self.mongo_db, self.neo4j_driver) if mongo_uri and mongo_db and neo4j_uri else Synchronizer()
            super().__init__(db_name)
        except Exception as e:
            print(f"Erreur d'initialisation des connexions : {e}")


    def configurate(self, config: Config = None) -> None:
        """
        Initializes the `Database` instance using a Config object for optional
        MongoDB and Neo4j connections.

        Parameters:
            config (Config, optional): A Config object containing the database connection settings.
        """
        try:
            if config:
                if config.MONGO_URI and config.MONGO_DB:
                    self.mongo_client = MongoClient(config.MONGO_URI)
                    self.mongo_db = self.mongo_client[config.MONGO_DB]
                if config.NEO4J_URI:
                    self.neo4j_driver = GraphDatabase.driver(
                        config.NEO4J_URI,
                        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
                    )
                self.sync = Synchronizer(self.mongo_db, self.neo4j_driver) if config.MONGO_URI and config.MONGO_DB and config.NEO4J_URI else Synchronizer()
                super().__init__(config.DB_NAME)
            else:
                self.sync = Synchronizer()
                super().__init__()
        except Exception as e:
            print(f"Error initializing connections: {e}")


    def close(self) -> None:
        """
        Closes the database connections for MongoDB and Neo4j.

        This method closes both the MongoDB and Neo4j connections and also calls the parent class's `close` method to handle any additional cleanup.
        """
        try:
            super().close()
            with closing(self.mongo_client):
                self.mongo_client.close()
            with closing(self.neo4j_driver):
                self.neo4j_driver.close()
        except Exception as e:
            print(f"Erreur lors de la fermeture des connexions : {e}")


def get_database() -> Database:
    return Database(config=Config)
