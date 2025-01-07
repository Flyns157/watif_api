import logging
from threading import Lock, current_thread, local
from time import perf_counter
import numpy as np
from Recommender.utils import array_avg
from . import watif_integrated_embedder
from ...database import Database  
from datetime import datetime, timedelta
from contextlib import contextmanager


class MC_embedder(watif_integrated_embedder):
    """
    Embedder class responsible for generating and managing embeddings for social media entities such as users, posts, threads, and interests.
    The embeddings are weighted based on configurable attributes like followings, interests, descriptions, and content. 

    Attributes:
        db (Database): A database instance to interact with MongoDB collections.
        model (sentence-transformers.Model): A model instance used for encoding textual information into embeddings.
        
    Methods:
        get_user_embedding(id_user, follow_weight, interest_weight, description_weight, *args, **kwargs):
            Generates a weighted user embedding based on user interests, followings, and description.
        
        get_post_embedding(id_post, key_weight, title_weight, content_weight, author_weight, *args, **kwargs):
            Generates a weighted post embedding based on the post's keys, title, content, and author.

        get_thread_embedding(id_thread, author_weight, name_weight, member_weight, post_weight, *args, **kwargs):
            Generates a weighted thread embedding based on thread's author, name, members, and posts.

        get_key_embedding(id_key, *args, **kwargs):
            Retrieves or generates an embedding for a key entity.

        get_interest_embedding(id_interest, *args, **kwargs):
            Retrieves or generates an embedding for an interest entity.

        get_user_embeddings(*args, **kwargs):
            Retrieves embeddings for all users in the database.

        get_post_embeddings(*args, **kwargs):
            Retrieves embeddings for all posts in the database.

        get_thread_embeddings(*args, **kwargs):
            Retrieves embeddings for all threads in the database.

        get_interest_embeddings(*args, **kwargs):
            Retrieves embeddings for all interests in the database.

        get_key_embeddings(*args, **kwargs):
            Retrieves embeddings for all keys in the database.

        _get_embedding(entity_type, entity_id):
            Retrieves the embedding for a specific entity from the database.

        encode(entity_type, entity_id, show_progress_bar=True, *args, **kwargs):
            Encodes an entity based on its type and ID, with configurable arguments and weights for generating embeddings.
    """
    def __init__(self, db: Database, update_time_hours: int = 2, model: str = 'all-MiniLM-L6-v2', logger: logging.Logger = None, *args, **kwargs) -> None:
        """
        Initializes the MC embedder with database access, the amount of hours before update the embedding and the logger.

        Args:
            db (Database): Database instance.
            update_time_hours (int): the life duration of an embedding.
            model (str): Model name for SentenceTransformer.
            logger (logging.Logger): The logger to stream logs.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        # Setup logging
        self.logger = logger or self._setup_logger()
        self.logger.info("Initializing MC_embedder with configuration: model=%s, update_time_hours=%d", model, update_time_hours)
        
        try:
            super().__init__(db, model, *args, **kwargs)
            self.update_time = timedelta(hours=update_time_hours)
            # Thread-local storage for tracking processing users
            self._thread_local = local()
            # Lock for database operations
            self._db_lock = Lock()
            
            self.logger.info("Successfully initialized MC_embedder instance")
            self.logger.debug("Database connection established, thread-local storage and locks initialized")
        except Exception as e:
            self.logger.error("Failed to initialize MC_embedder: %s", str(e), exc_info=True)
            raise

    def _setup_logger(self) -> logging.Logger:
        """Sets up and configures the logger."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(threadName)s] %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @property
    def _processing_users(self):
        """Thread-local set of users being processed."""
        if not hasattr(self._thread_local, 'processing_users'):
            self._thread_local.processing_users = set()
            self.logger.debug("[Thread %s] Initialized processing_users set", 
                            current_thread().name)
        return self._thread_local.processing_users

    @contextmanager
    def _track_user_processing(self, id_user):
        """
        Thread-safe context manager for tracking user processing state.
        
        Args:
            id_user: The ID of the user being processed
            
        Yields:
            bool: True if this is a cyclic reference, False otherwise
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        is_cycle = id_user in self._processing_users
        
        self.logger.debug(  "[Thread %s] Beginning user tracking for %s (cycle detected: %s)", 
                            thread_name, id_user, is_cycle)
        
        if not is_cycle:
            self._processing_users.add(id_user)
            
        try:
            yield is_cycle
        finally:
            if not is_cycle:
                self._processing_users.remove(id_user)
                duration = perf_counter() - start_time
                self.logger.debug("[Thread %s] Completed user tracking for %s in %.2f seconds", 
                                thread_name, id_user, duration)

    def get_user_embedding( self, id_user: str | int | bytes, follow_weight: float = 0.4, 
                            interest_weight: float = 0.4, description_weight: float = 0.2, 
                            *args, **kwargs) -> np.ndarray:
        """
        Thread-safe method to generate a weighted user embedding based on interests, followings, and description.
        Handles circular dependencies in the social graph by detecting cycles and falling back
        to a base embedding when needed.

        Args:
            id_user (str | int | bytes): User ID.
            follow_weight (float): Weight for followings.
            interest_weight (float): Weight for interests.
            description_weight (float): Weight for description.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: The generated user embedding as a NumPy array.
        
        Raises:
            ValueError: If the sum of weights is not equal to 1 or if user doesn't exist.
        """
        start_time = perf_counter()
        thread_name = current_thread().name
        
        self.logger.info("[Thread %s] Starting embedding generation for user %s", 
                        thread_name, id_user)
        
        try:
            # Check if user exists and get current embedding
            with self._db_lock:
                self.logger.debug("[Thread %s] Acquiring database lock for user %s", 
                                thread_name, id_user)
                entity = self._get_embedding('users', id_user)
                if not entity:
                    self.logger.error("[Thread %s] User %s not found in database", 
                                    thread_name, id_user)
                    raise ValueError(f"User {id_user} doesn't exist: impossible to generate an embedding")
                
                # Return cached embedding if valid
                if "embedding" in entity:
                    embed_date = datetime.fromisoformat(entity['embedding']['date'])
                    if (datetime.now() - embed_date) < self.update_time:
                        self.logger.info("[Thread %s] Retrieved valid cached embedding for user %s", 
                                        thread_name, id_user)
                        return np.array(entity["embedding"]['vector'])
                    else:
                        self.logger.debug("[Thread %s] Cached embedding expired for user %s", 
                                        thread_name, id_user)
            
            # Validate weights
            if not np.isclose(follow_weight + interest_weight + description_weight, 1.0, rtol=1e-09, atol=1e-09):
                self.logger.error("[Thread %s] Invalid weights for user %s: follow=%.2f, interest=%.2f, description=%.2f", 
                                thread_name, id_user, follow_weight, interest_weight, description_weight)
                raise ValueError('The sum of arguments follow_weight, interest_weight and description_weight must be 1.0')
            
            # Get user data
            with self._db_lock:
                self.logger.debug("[Thread %s] Retrieving user data for %s", 
                                thread_name, id_user)
                user = self.db.mongo_db['users'].find_one({"_id": id_user})
            
            # Process user embedding with cycle detection
            with self._track_user_processing(id_user) as is_cycle:
                if is_cycle:
                    self.logger.info("[Thread %s] Generating base embedding for user %s due to circular dependency", 
                                    thread_name, id_user)
                    return self._generate_base_user_embedding(
                        user, 
                        interest_weight/(interest_weight + description_weight),
                        description_weight/(interest_weight + description_weight),
                        *args, **kwargs
                    )
                
                self.logger.debug("[Thread %s] Generating full embedding for user %s", 
                                thread_name, id_user)
                embedded_user = self._generate_full_user_embedding(
                    user, follow_weight, interest_weight, description_weight,
                    *args, **kwargs
                )
                
                # Store the embedding
                with self._db_lock:
                    self.logger.debug("[Thread %s] Storing new embedding for user %s", 
                                    thread_name, id_user)
                    self.db.mongo_db['users'].update_one(
                        {'_id': id_user},
                        {'$set': {
                            'embedding': {
                                'date': datetime.now().isoformat(),
                                'vector': embedded_user.tolist()
                            }
                        }}
                    )
                
                return embedded_user
                
        except Exception as e:
            self.logger.error("[Thread %s] Error generating embedding for user %s: %s", 
                            thread_name, id_user, str(e), exc_info=True)
            raise
        finally:
            duration = perf_counter() - start_time
            self.logger.info(   "[Thread %s] Completed embedding generation for user %s in %.2f seconds", 
                                thread_name, id_user, duration)
    
    def _generate_base_user_embedding(  self, user: dict, normalized_interest_weight: float,
                                        normalized_description_weight: float, *args, **kwargs) -> np.ndarray:
        """
        Generates a base user embedding without follow relationships to break circular dependencies.
        Thread-safe as it doesn't modify shared state.
        
        Args:
            user (dict): User document from database.
            normalized_interest_weight (float): Adjusted weight for interests.
            normalized_description_weight (float): Adjusted weight for description.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
            
        Returns:
            np.ndarray: Base user embedding.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.debug(  "[Thread %s] Generating base embedding for user %s with %d interests", 
                            thread_name, user['_id'], len(user['interests']))
        
        try:
            result = array_avg(
                array_avg(
                    self.get_interest_embedding(
                        id_interest,
                        *args, **kwargs
                    )
                    for id_interest in user['interests']
                ) * normalized_interest_weight,
                self.model.encode(
                    user['description'],
                    *args, **kwargs
                ) * normalized_description_weight
            )
            
            duration = perf_counter() - start_time
            self.logger.debug("[Thread %s] Generated base embedding for user %s in %.2f seconds", 
                            thread_name, user['_id'], duration)
            return result
            
        except Exception as e:
            self.logger.error("[Thread %s] Error generating base embedding for user %s: %s", 
                            thread_name, user['_id'], str(e), exc_info=True)
            raise


    def _generate_full_user_embedding(self, user: dict, follow_weight: float,
                                    interest_weight: float, description_weight: float,
                                    *args, **kwargs) -> np.ndarray:
        """
        Generates a complete user embedding including follow relationships.
        Thread-safe as it doesn't modify shared state.
        
        Args:
            user (dict): User document from database.
            follow_weight (float): Weight for followings.
            interest_weight (float): Weight for interests.
            description_weight (float): Weight for description.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
            
        Returns:
            np.ndarray: Complete user embedding.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.debug(  "[Thread %s] Generating full embedding for user %s with %d interests and %d follows", 
                            thread_name, user['_id'], len(user['interests']), len(user['follow']))
        
        try:
            result = array_avg(
                array_avg(
                    self.get_interest_embedding(
                        id_interest,
                        *args, **kwargs
                    )
                    for id_interest in user['interests']
                ) * interest_weight,
                self.model.encode(
                    user['description'],
                    *args, **kwargs
                ) * description_weight,
                array_avg(
                    self.get_user_embedding(
                        id_follow,
                        follow_weight=follow_weight,
                        interest_weight=interest_weight,
                        description_weight=description_weight,
                        *args, **kwargs
                    )
                    for id_follow in user['follow']
                ) * follow_weight
            )
            
            duration = perf_counter() - start_time
            self.logger.debug("[Thread %s] Generated full embedding for user %s in %.2f seconds", 
                            thread_name, user['_id'], duration)
            return result
            
        except Exception as e:
            self.logger.error("[Thread %s] Error generating full embedding for user %s: %s", 
                            thread_name, user['_id'], str(e), exc_info=True)
            raise


    def get_post_embedding(self, id_post: str | int | bytes, key_weight: float = 0.35, title_weight: float = 0.35, content_weight: float = 0.2, author_weight: float = 0.1, *args, **kwargs) -> np.ndarray:
        """
        Generates a weighted post embedding based on the post's keys, title, content, and author.

        Args:
            id_post (str | int | bytes): Post ID.
            key_weight (float): Weight for keys associated with the post.
            title_weight (float): Weight for the title of the post.
            content_weight (float): Weight for the content of the post.
            author_weight (float): Weight for the author of the post.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: The generated post embedding as a NumPy array.
        
        Raises:
            ValueError: If the sum of `key_weight`, `title_weight`, `content_weight`, and `author_weight` is not equal to 1.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.info("[Thread %s] Starting post embedding generation for %s", thread_name, id_post)
        self.logger.debug(  "[Thread %s] Weights configuration - key: %.2f, title: %.2f, content: %.2f, author: %.2f", 
                            thread_name, key_weight, title_weight, content_weight, author_weight)
        
        try:
            with self._db_lock:
                self.logger.debug("[Thread %s] Acquiring database lock for post %s", thread_name, id_post)
                entity = self._get_embedding('posts', id_post)
                
                if not entity:
                    self.logger.error("[Thread %s] Post %s not found in database", thread_name, id_post)
                    raise ValueError(f"Post {id_post} doesn't exist: impossible to generate an embedding")
                
                # Return cached embedding if it exists and is fresh
                if "embedding" in entity:
                    embed_date = datetime.fromisoformat(entity['embedding']['date'])
                    age = datetime.now() - embed_date
                    self.logger.debug("[Thread %s] Found existing embedding for post %s (age: %s)", 
                                    thread_name, id_post, age)
                    if age < self.update_time:
                        self.logger.info("[Thread %s] Using cached embedding for post %s", thread_name, id_post)
                        return np.array(entity["embedding"]['vector'])
                    self.logger.debug("[Thread %s] Cached embedding expired for post %s", thread_name, id_post)
            
            weights_sum = key_weight + title_weight + content_weight + author_weight
            if not np.isclose(weights_sum, 1.0, rtol=1e-09, atol=1e-09):
                self.logger.error("[Thread %s] Invalid weights sum for post %s: %.3f", 
                                thread_name, id_post, weights_sum)
                raise ValueError('The sum of weights must be 1.0')
            
            with self._db_lock:
                self.logger.debug("[Thread %s] Retrieving post data for %s", thread_name, id_post)
                post = self.db.mongo_db['posts'].find_one({"_id": id_post})
                self.logger.debug("[Thread %s] Found post %s with %d keys", 
                                thread_name, id_post, len(post['keys']))
            
            self.logger.debug("[Thread %s] Generating embeddings for post components", thread_name)
            embedded_post = array_avg(
                array_avg(
                    self.get_key_embedding(
                        id_key, 
                        *args, **kwargs
                    )
                    for id_key in post['keys']
                ) * key_weight,
                self.model.encode(
                    sentences = post['title'],
                    prompt = 'Titre:\n',
                    *args, **kwargs
                ) * title_weight,
                self.model.encode(
                    sentences = post['content'],
                    prompt = 'Content:\n',
                    *args, **kwargs
                ) * content_weight,
                self.get_user_embedding(
                    post['id_author'],
                    *args, **kwargs
                ) * author_weight
            )
            
            # Store the embedding in the database
            with self._db_lock:
                self.logger.debug("[Thread %s] Storing new embedding for post %s", thread_name, id_post)
                self.db.mongo_db['posts'].update_one(
                    {'_id': id_post},
                    {'$set': {
                        'embedding': {
                            'date': datetime.now().isoformat(),
                            'vector': embedded_post.tolist()
                        }
                    }}
                )
            
            return embedded_post
            
        except Exception as e:
            self.logger.error("[Thread %s] Failed to generate embedding for post %s: %s", 
                            thread_name, id_post, str(e), exc_info=True)
            raise
        finally:
            duration = perf_counter() - start_time
            self.logger.info("[Thread %s] Completed post embedding generation for %s in %.2f seconds", 
                            thread_name, id_post, duration)


    def get_thread_embedding(self, id_thread: str | int | bytes, author_weight: float = 0.1, name_weight: float = 0.1, member_weight: float = 0.4, post_weight: float = 0.4, *args, **kwargs) -> np.ndarray:
        """
        Generates a weighted thread embedding based on author, name, members, and posts in the thread.

        Args:
            id_thread (str | int | bytes): Thread ID.
            author_weight (float): Weight for the thread's author.
            name_weight (float): Weight for the thread's name.
            member_weight (float): Weight for the members of the thread.
            post_weight (float): Weight for posts in the thread.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: The generated thread embedding as a NumPy array.
        
        Raises:
            ValueError: If the sum of `author_weight`, `name_weight`, `member_weight`, and `post_weight` is not equal to 1.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.info("[Thread %s] Starting thread embedding generation for %s", thread_name, id_thread)
        self.logger.debug(  "[Thread %s] Weights configuration - author: %.2f, name: %.2f, member: %.2f, post: %.2f",
                            thread_name, author_weight, name_weight, member_weight, post_weight)
        
        try:
            entity = self._get_embedding('threads', id_thread)
            
            if not entity:
                self.logger.error("[Thread %s] Thread %s not found in database", thread_name, id_thread)
                raise ValueError(f"Thread {id_thread} doesn't exist: impossible to generate an embedding")
            
            # Return cached embedding if it exists and is fresh
            if "embedding" in entity:
                embed_date = datetime.fromisoformat(entity['embedding']['date'])
                age = datetime.now() - embed_date
                self.logger.debug("[Thread %s] Found existing embedding for thread %s (age: %s)",
                                thread_name, id_thread, age)
                if age < self.update_time:
                    return np.array(entity["embedding"]['vector'])
            
            weights_sum = author_weight + name_weight + member_weight + post_weight
            if not np.isclose(weights_sum, 1.0, rtol=1e-09, atol=1e-09):
                self.logger.error("[Thread %s] Invalid weights sum for thread %s: %.3f",
                                thread_name, id_thread, weights_sum)
                raise ValueError('The sum of weights must be 1.0')
            
            self.logger.debug("[Thread %s] Retrieving thread data and generating embeddings", thread_name)
            thread = self.db.mongo_db['threads'].find_one({"_id": id_thread})
            
            embedded_thread = array_avg(
                self.get_user_embedding(
                    thread['id_author'], 
                    *args, **kwargs
                ) * author_weight,
                self.model.encode(
                    sentences = thread['name'],
                    prompt = 'Discussion name:\n',
                    *args, **kwargs
                ) * name_weight,
                array_avg(
                    self.get_user_embedding(
                        id_member,
                        *args, **kwargs
                    )
                    for id_member in thread['members']
                ) * member_weight,
                array_avg(
                    self.get_post_embedding(
                        post['idPost'],
                        *args, **kwargs
                    )
                    for post in self.db.mongo_db['posts'].find({"id_thread": id_thread})
                ) * post_weight
            )
            
            # Store the embedding in the database
            with self._db_lock:
                self.logger.debug("[Thread %s] Storing new embedding for thread %s", thread_name, id_thread)
                self.db.mongo_db['threads'].update_one(
                    {'_id': id_thread},
                    {'$set': {
                        'embedding': {
                            'date': datetime.now().isoformat(),
                            'vector': embedded_thread.tolist()
                        }
                    }}
                )
            
            return embedded_thread
            
        except Exception as e:
            self.logger.error("[Thread %s] Failed to generate embedding for thread %s: %s",
                            thread_name, id_thread, str(e), exc_info=True)
            raise
        finally:
            duration = perf_counter() - start_time
            self.logger.info("[Thread %s] Completed thread embedding generation for %s in %.2f seconds",
                            thread_name, id_thread, duration)


    def get_key_embedding(self, id_key: str | int | bytes, *args, **kwargs) -> np.ndarray:
        """
        Retrieves or generates an embedding for a key entity.

        Args:
            id_key (str | int | bytes): Key ID.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: The generated or retrieved key embedding as a NumPy array.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.info("[Thread %s] Starting key embedding generation for %s", thread_name, id_key)
        
        try:
            entity = self._get_embedding('keys', id_key)
            
            if not entity:
                self.logger.error("[Thread %s] Key %s not found in database", thread_name, id_key)
                raise ValueError(f"Key {id_key} doesn't exist: impossible to generate an embedding")
            
            # Return cached embedding if it exists and is fresh
            if "embedding" in entity:
                embed_date = datetime.fromisoformat(entity['embedding']['date'])
                age = datetime.now() - embed_date
                self.logger.debug("[Thread %s] Found existing embedding for key %s (age: %s)",
                                thread_name, id_key, age)
                if age < self.update_time:
                    return np.array(entity["embedding"]['vector'])
            
            self.logger.debug("[Thread %s] Generating new embedding for key %s", thread_name, id_key)
            embedded_key = self.model.encode(entity['name'], *args, **kwargs)
            
            # Store the embedding in the database
            with self._db_lock:
                self.logger.debug("[Thread %s] Storing new embedding for key %s", thread_name, id_key)
                self.db.mongo_db['keys'].update_one(
                    {'_id': id_key},
                    {'$set': {
                        'embedding': {
                            'date': datetime.now().isoformat(),
                            'vector': embedded_key.tolist()
                        }
                    }}
                )
            
            return embedded_key
            
        except Exception as e:
            self.logger.error("[Thread %s] Failed to generate embedding for key %s: %s",
                            thread_name, id_key, str(e), exc_info=True)
            raise
        finally:
            duration = perf_counter() - start_time
            self.logger.info("[Thread %s] Completed key embedding generation for %s in %.2f seconds",
                            thread_name, id_key, duration)


    def get_interest_embedding(self, id_interest: str | int | bytes, *args, **kwargs) -> np.ndarray:
        """
        Retrieves or generates an embedding for an interest entity.

        Args:
            id_interest (str | int | bytes): Interest ID.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: The generated or retrieved interest embedding as a NumPy array.
        """
        thread_name = current_thread().name
        start_time = perf_counter()
        
        self.logger.info("[Thread %s] Starting interest embedding generation for %s", thread_name, id_interest)
        
        try:
            with self._db_lock:
                self.logger.debug("[Thread %s] Acquiring database lock for interest %s", thread_name, id_interest)
                entity = self._get_embedding('interest', id_interest)
                
                if not entity:
                    self.logger.error("[Thread %s] Interest %s not found in database", thread_name, id_interest)
                    raise ValueError(f"Interest {id_interest} doesn't exist: impossible to generate an embedding")
                
                self.logger.debug("[Thread %s] Retrieved interest data: %s (name length: %d)", 
                                thread_name, id_interest, len(entity['name']))
                
                # Check for cached embedding
                if "embedding" in entity:
                    embed_date = datetime.fromisoformat(entity['embedding']['date'])
                    age = datetime.now() - embed_date
                    self.logger.debug("[Thread %s] Found existing embedding for interest %s (age: %s)", 
                                    thread_name, id_interest, age)
                    
                    if age < self.update_time:
                        self.logger.info("[Thread %s] Using cached embedding for interest %s (age: %s < threshold: %s)", 
                                        thread_name, id_interest, age, self.update_time)
                        cached_vector = np.array(entity["embedding"]['vector'])
                        self.logger.debug("[Thread %s] Retrieved cached embedding for interest %s (shape: %s)", 
                                        thread_name, id_interest, cached_vector.shape)
                        return cached_vector
                    
                    self.logger.debug("[Thread %s] Cached embedding expired for interest %s (age: %s >= threshold: %s)", 
                                    thread_name, id_interest, age, self.update_time)
            
            self.logger.debug(  "[Thread %s] Generating new embedding for interest %s using model", 
                                thread_name, id_interest)
            embedded_interest = self.model.encode(entity['name'], *args, **kwargs)
            self.logger.debug(  "[Thread %s] Generated embedding for interest %s (shape: %s)", 
                                thread_name, id_interest, embedded_interest.shape)
            
            # Store the embedding in the database
            with self._db_lock:
                self.logger.debug("[Thread %s] Storing new embedding for interest %s", thread_name, id_interest)
                update_result = self.db.mongo_db['interest'].update_one(
                    {'_id': id_interest},
                    {'$set': {
                        'embedding': {
                            'date': datetime.now().isoformat(),
                            'vector': embedded_interest.tolist()
                        }
                    }}
                )
                self.logger.debug(  "[Thread %s] Database update for interest %s completed (modified: %s)", 
                                    thread_name, id_interest, update_result.modified_count > 0)
            
            return embedded_interest
            
        except Exception as e:
            self.logger.error(  "[Thread %s] Failed to generate embedding for interest %s: %s", 
                                thread_name, id_interest, str(e), exc_info=True)
            raise
        finally:
            duration = perf_counter() - start_time
            self.logger.info("[Thread %s] Completed interest embedding generation for %s in %.2f seconds", 
                            thread_name, id_interest, duration)


    def get_user_embeddings(self, *args, **kwargs) -> dict:
        """
        Retrieves embeddings for all users in the database.

        Args:
            *args: Additional arguments to pass to the embedding generation process.
            **kwargs: Additional keyword arguments for embedding generation.

        Returns:
            dict: A dictionary with user IDs as keys and their embeddings (np.ndarray) as values.
        """
        return {user:
                self.get_user_embeddings(user, *args, **kwargs)
                for user in self.db.mongo_db['users'].find(projection={'_id': 1})}


    def get_post_embeddings(self, *args, **kwargs) -> dict:
        """
        Retrieves embeddings for all posts in the database.

        Args:
            *args: Additional arguments to pass to the embedding generation process.
            **kwargs: Additional keyword arguments for embedding generation.

        Returns:
            dict: A dictionary with post IDs as keys and their embeddings (np.ndarray) as values.
        """
        return {post:
                self.get_post_embedding(post, *args, **kwargs)
                for post in self.db.mongo_db['posts'].find(projection={'_id': 1})}


    def get_thread_embeddings(self, *args, **kwargs) -> dict:
        """
        Retrieves embeddings for all threads in the database.

        Args:
            *args: Additional arguments to pass to the embedding generation process.
            **kwargs: Additional keyword arguments for embedding generation.

        Returns:
            dict: A dictionary with thread IDs as keys and their embeddings (np.ndarray) as values.
        """
        return {post:
                self.get_post_embedding(post, *args, **kwargs)
                for post in self.db.mongo_db['threads'].find(projection={'_id': 1})}


    def get_interest_embeddings(self, *args, **kwargs) -> dict:
        """
        Retrieves embeddings for all interests in the database.

        Args:
            *args: Additional arguments to pass to the embedding generation process.
            **kwargs: Additional keyword arguments for embedding generation.

        Returns:
            dict: A dictionary with interest IDs as keys and their embeddings (np.ndarray) as values.
        """
        return {interest:
                self.get_interest_embedding(interest, *args, **kwargs)
                for interest in self.db.mongo_db['interests'].find(projection={'_id': 1})}


    def get_key_embeddings(self, *args, **kwargs) -> dict:
        """
        Retrieves embeddings for all keywords in the database.

        Args:
            *args: Additional arguments to pass to the embedding generation process.
            **kwargs: Additional keyword arguments for embedding generation.

        Returns:
            dict: A dictionary with keyword IDs as keys and their embeddings (np.ndarray) as values.
        """
        return {key:
                self.get_key_embedding(key, *args, **kwargs)
                for key in self.db.mongo_db['keys'].find(projection={'_id': 1})}


    def _get_embedding(self, entity_type: str, entity_id: str | int | bytes) -> np.ndarray | None:
        """
        Retrieves embedding for a specific entity from the database.

        Args:
            entity_type (str): Type of entity (e.g., 'user', 'post', 'thread').
            entity_id (str | int | bytes): Entity ID.

        Returns:
            np.ndarray | None: Retrieved embedding or None if not found.
        """
        entity = self.db.mongo_db[entity_type].find_one({"_id": entity_id}, {"embedding": 1})
        return np.array(entity.get("embedding")) if entity else None


    def encode(self, entity_type: str, entity_id: str | int | bytes, show_progress_bar: bool = True, *args, **kwargs) -> np.ndarray:
        """
        Encodes an entity based on type and ID, using specified weights if needed.

        Args:
            entity_type (str): Type of entity.
            entity_id (str | int | bytes): Entity ID.
            show_progress_bar (bool): Display progress bar.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            np.ndarray: Encoded embedding.
        """
        match entity_type.lower():
            case 'key':
                return self.get_key_embedding(entity_id, *args, **kwargs)
            case 'interest':
                return self.get_interest_embedding(entity_id, *args, **kwargs)
            case 'user':
                return self.get_user_embedding(entity_id, *args, **kwargs)
            case 'post':
                return self.get_post_embedding(entity_id, *args, **kwargs)
            case 'thread':
                return self.get_thread_embedding(entity_id, *args, **kwargs)
            case 'keys':
                return self.get_key_embeddings(*args, **kwargs)
            case 'interests':
                return self.get_interest_embeddings(*args, **kwargs)
            case 'users':
                return self.get_user_embeddings(*args, **kwargs)
            case 'posts':
                return self.get_post_embeddings(*args, **kwargs)
            case 'threads':
                return self.get_thread_embeddings(*args, **kwargs)
            case _:
                return self.model.encode(entity_id, show_progress_bar=show_progress_bar, *args, **kwargs)
