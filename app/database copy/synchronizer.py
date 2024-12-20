"""========================= /!\\ In Rework /!\\ ========================="""

from pymongo.database import Database as MongoDatabase
from neo4j import Driver as Neo4jDriver
import logging


logging.basicConfig(level=logging.INFO)

class Synchronizer:
    def __init__(self, mongo_db: MongoDatabase = None, neo4j_driver: Neo4jDriver = None) -> None:
        """
        Initializes the Synchronizer instance with optional MongoDB and Neo4j connections.

        Parameters:
            mongo_db (MongoDatabase, optional): The MongoDB database connection.
            neo4j_driver (Neo4jDriver, optional): The Neo4j driver connection.
        """
        self.set_conn(mongo_db=mongo_db, neo4j_driver=neo4j_driver)

    def set_conn(self, mongo_db: MongoDatabase, neo4j_driver: Neo4jDriver) -> None:
        """
        Sets the database connections for MongoDB and Neo4j.

        Parameters:
            mongo_db (MongoDatabase): The MongoDB database connection.
            neo4j_driver (Neo4jDriver): The Neo4j driver connection.
        """
        self.mongo_db = mongo_db
        self.neo4j_driver = neo4j_driver

    def _create_constraints(self):
        """Create necessary constraints in Neo4j."""
        with self.neo4j_driver.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.idUser IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Post) REQUIRE p.idPost IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Thread) REQUIRE t.idThread IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Key) REQUIRE k.idKey IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interest) REQUIRE i.idInterest IS UNIQUE"
            ]
            for constraint in constraints:
                session.run(constraint)
            logging.info("Constraints created successfully.")

    def _get_properties(self, entity, exclude_keys):
        return {k: v for k, v in entity.items() if k not in exclude_keys}

    def sync_users(self):
        """Synchronize users from MongoDB to Neo4j."""
        users = self.mongo_db['users'].find()
        
        with self.neo4j_driver.session() as session:
            for user in users:
                # Create user node
                properties = self._get_properties(user, ['_id', 'id_user', 'follow', 'blocked', 'interests', 'role'])
                session.run("""
                    MERGE (u:User {idUser: $id_user})
                    SET u += $properties
                """, id_user=str(user['_id']), properties=properties)

                session.run("""
                    MATCH (u:User {idUser: $user_id})
                    MATCH (r:Role {name: $role_name})
                    MERGE (u)-[:HAS_ROLE]->(r)
                    """, user_id=str(user['_id']), role_name=user['role'])

                # Create relationships
                if 'follow' in user:
                    for id_follows in user['follow']:
                        session.run("""
                        MATCH (u1:User {idUser: $user_id})
                        MATCH (u2:User {idUser: $id_follows})
                        MERGE (u1)-[:FOLLOWS]->(u2)
                        """, user_id=str(user['_id']), id_follows=id_follows)

                if 'blocked' in user:
                    for blocked_id in user['blocked']:
                        session.run("""
                        MATCH (u1:User {idUser: $user_id})
                        MATCH (u2:User {idUser: $blocked_id})
                        MERGE (u1)-[:BLOCKS]->(u2)
                        """, user_id=str(user['_id']), blocked_id=blocked_id)

                if 'interests' in user:
                    for interest_id in user['interests']:
                        session.run("""
                        MATCH (u:User {idUser: $user_id})
                        MATCH (k:Interest {idInterest: $id_key})
                        MERGE (u)-[:INTERESTED_BY]->(k)
                        """, user_id=str(user['_id']), id_key=interest_id)

            logging.info("User synchronization completed.")

    def sync_roles(self):
        """Synchronize roles from MongoDB to Neo4j."""
        roles = self.mongo_db['roles'].find()
        
        with self.neo4j_driver.session() as session:
            for role in roles:
                # Create role node
                properties = self._get_properties(role, ['_id', 'name', 'extend'])
                session.run("""
                    MERGE (r:Role {name: $name})
                    SET r += $properties
                """, name=role['name'], properties=properties)

                # Create extend relationships
                if 'extend' in role:
                    for extended_role in role['extend']:
                        session.run("""
                        MATCH (r1:Role {name: $role_name})
                        MATCH (r2:Role {name: $extended_name})
                        MERGE (r1)-[:EXTENDS]->(r2)
                        """, role_name=role['name'], extended_name=extended_role)

            logging.info("Role synchronization completed.")

    def sync_threads(self):
        """Synchronize threads from MongoDB to Neo4j."""
        threads = self.mongo_db['threads'].find()
        
        with self.neo4j_driver.session() as session:
            for thread in threads:
                # Create thread node
                properties = self._get_properties(thread, ['_id', 'id_thread', 'members', 'id_owner', 'admins'])
                session.run("""
                    MERGE (t:Thread {idThread: $id_thread})
                    SET t += $properties
                """, id_thread=str(thread['_id']), properties=properties)

                # Create relationships
                # Owner relationship
                session.run("""
                MATCH (u:User {idUser: $owner_id})
                MATCH (t:Thread {idThread: $id_thread})
                MERGE (u)-[:OWNS]->(t)
                """, owner_id=thread['id_owner'], id_thread=str(thread['_id']))

                # Members relationship
                for member_id in thread['members']:
                    session.run("""
                    MATCH (u:User {idUser: $member_id})
                    MATCH (t:Thread {idThread: $id_thread})
                    MERGE (u)-[:MEMBER_OF]->(t)
                    """, member_id=member_id, id_thread=str(thread['_id']))

                # Admins relationship
                for admin_id in thread['admins']:
                    session.run("""
                    MATCH (u:User {idUser: $admin_id})
                    MATCH (t:Thread {idThread: $id_thread})
                    MERGE (u)-[:ADMIN_OF]->(t)
                    """, admin_id=admin_id, id_thread=str(thread['_id']))

            logging.info("Thread synchronization completed.")

    def sync_posts(self):
        """Synchronize posts from MongoDB to Neo4j."""
        posts = self.mongo_db['posts'].find()
        
        with self.neo4j_driver.session() as session:
            for post in posts:
                # Create post node
                properties = self._get_properties(post, ['_id', 'idPost', 'id_thread', 'id_author', 'keys', 'likes', 'comments'])
                session.run("""
                    MERGE (p:Post {idPost: $idPost})
                    SET p += $properties
                """, idPost=str(post['_id']), properties=properties)

                # Create relationships
                # Author relationship
                session.run("""
                MATCH (u:User {idUser: $id_author})
                MATCH (p:Post {idPost: $id_post})
                MERGE (u)-[:WRITED_BY]->(p)
                """, id_author=post['id_author'], id_post=str(post['_id']))

                # Thread relationship
                session.run("""
                MATCH (t:Thread {idThread: $id_thread})
                MATCH (p:Post {idPost: $id_post})
                MERGE (p)-[:POSTED_IN]->(t)
                """, id_thread=post['id_thread'], id_post=str(post['_id']))

                # Keys relationship
                for id_key in post.get('keys', []):
                    session.run("""
                    MATCH (p:Post {idPost: $id_post})
                    MATCH (k:Key {idkey: $id_key})
                    MERGE (p)-[:HAS_KEY]->(k)
                    """, id_post=str(post['_id']), id_key=id_key)

                # Likes relationship
                for id_liker in post.get('likes', []):
                    session.run("""
                    MATCH (u:User {idUser: $id_liker})
                    MATCH (p:Post {idPost: $id_post})
                    MERGE (u)-[:LIKES]->(p)
                    """, id_liker=id_liker, id_post=str(post['_id']))

                # Comments relationship
                for id_commenter in post.get('comments', []):
                    session.run("""
                    MATCH (u:User {idUser: $id_commenter})
                    MATCH (p:Post {idPost: $id_post})
                    MERGE (u)-[:HAS_COMMENT]->(p)
                    """, id_commenter=id_commenter, id_post=str(post['_id']))

            logging.info("Post synchronization completed.")

    def sync_keys(self):
        """Synchronize keys from MongoDB to Neo4j."""
        keys = self.mongo_db['keys'].find()
        
        with self.neo4j_driver.session() as session:
            for key in keys:
                # Create key node
                properties = self._get_properties(key, ['_id', 'id_key'])
                session.run("""
                    MERGE (k:Key {idKey: $id_key})
                    SET k += $properties
                """, id_key=str(key['_id']), properties=properties)

            logging.info("Key synchronization completed.")

    def sync_interests(self):
        """Synchronize interests from MongoDB to Neo4j."""
        interests = self.mongo_db['interests'].find()
        
        with self.neo4j_driver.session() as session:
            for interest in interests:
                # Create interest node
                properties = self._get_properties(interest, ['_id', 'id_interest'])
                session.run("""
                    MERGE (i:Interest {idInterest: $id_interest})
                    SET i += $properties
                """, id_interest=str(interest['_id']), properties=properties)

            logging.info("Interest synchronization completed.")

    def erase_all_data(self):
        """
        Erase all data from the Neo4j database.
        """
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logging.info("All data erased from Neo4j database.")

    def synchronize(self):
        """Run the synchronization process for all entities."""
        self._create_constraints()
        self.sync_roles()
        self.sync_interests()
        self.sync_keys()
        self.sync_users()
        self.sync_threads()
        self.sync_posts()

    def sync_all(self, erase_data: bool = False) -> None:
        """
        Synchronizes data across all collections between MongoDB and Neo4j.

        This method calls `sync_posts`, `sync_roles`, `sync_threads`, and `sync_users`.
        """
        print("Data synchronization between MongoDB and Neo4j databases ", end='')
        if erase_data:
            self.erase_all_data()
        self._create_constraints()
        try:
            self.sync_roles()
            self.sync_interests()
            self.sync_keys()
            self.sync_users()
            self.sync_threads()
            self.sync_posts()
            print("[SUCCESS]")
            logging.info("Data synchronization between MongoDB and Neo4j completed successfully.")
        except Exception as e:
            print(f"[FAILED]\n - {e}")
            logging.error(f"Data synchronization failed: {e}")
