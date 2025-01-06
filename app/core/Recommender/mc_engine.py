"""
Recommendation engine by Mattéo, using neo4j database.
"""
from . import recommender_engine
import numpy as np


class MC_engine(recommender_engine):
    """
    Monte Carlo-based recommendation engine for suggesting users to follow, posts to view, and threads to join.
    Generates recommendations based on shared interests, mutual connections, and engagement patterns.

    Methods:
        recommend_users(user_id: str, follow_weight: float = 0.5, interest_weight: float = 0.5) -> list[str]:
            Recommends users to follow based on common followers and shared interests.

        recommend_posts(user_id: str, interest_weight: float = 0.7, interaction_weight: float = 0.3) -> list[str]:
            Recommends posts based on shared interests and past interactions.

        recommend_threads(user_id: str, member_weight: float = 0.6, interest_weight: float = 0.4) -> list[str]:
            Recommends threads to join based on shared memberships and relevant interests.
    """

    def recommend_users(self, user_id: str, follow_weight: float = 0.5, interest_weight: float = 0.5, limit: int = 10) -> list[str]:
        """
        Recommends users to follow based on common followers and shared interests.

        Parameters:
            user_id (str): The ID of the user for whom recommendations are being generated.
            follow_weight (float, optional): Weight assigned to the influence of common followers in the recommendation score.
            interest_weight (float, optional): Weight assigned to the influence of shared interests in the recommendation score.

        Returns:
            list[str]: A list of recommended user IDs, sorted by relevance.
        """
        if not np.isclose(follow_weight + interest_weight, 1.0, rtol=1e-09, atol=1e-09):
            raise ValueError('The sum of arguments follow_weight and interest_weight must be 1.0')
        with self.db.neo4j_driver.session() as session:
            scores = session.run("""
                MATCH (u:users {idUser: $user_id})-[:INTERESTED_BY]->(i:interests)<-[:INTERESTED_BY]-(u2:users)
                WHERE u2.idUser <> $user_id
                WITH u2, COUNT(i) AS common_interests
                MATCH (u)-[:FOLLOWS]->(f:users)<-[:FOLLOWS]-(u2)
                WITH u2, common_interests, COUNT(f) AS common_follows
                RETURN u2.idUser AS user_id,
                       ($follow_weight * common_follows + $interest_weight * common_interests) AS score
                ORDER BY score DESC
                LIMIT $limit
            """, user_id=user_id, follow_weight=follow_weight, interest_weight=interest_weight, limit=limit)
            return scores.values()


    def recommend_posts(self, user_id: str, interest_weight: float = 0.7, interaction_weight: float = 0.3, limit: int = 10) -> list[str]:
        """
        Recommends posts based on shared interests and user interactions.

        Parameters:
            user_id (str): The ID of the user for whom recommendations are being generated.
            interest_weight (float, optional): Weight assigned to the influence of shared interests in the recommendation score.
            interaction_weight (float, optional): Weight assigned to the influence of user interactions (e.g., likes, comments) in the recommendation score.

        Returns:
            list[str]: A list of recommended post IDs, sorted by relevance.
        """
        if not np.isclose(interaction_weight + interest_weight, 1.0, rtol=1e-09, atol=1e-09):
            raise ValueError('The sum of arguments interaction_weight and interest_weight must be 1.0')
        with self.db.neo4j_driver.session() as session:
            scores = session.run("""
                MATCH (u:users {idUser: $user_id})-[:INTERESTED_BY]->(i:interests)<-[:HAS_KEY]-(p:Post)
                WITH p, COUNT(i) AS interest_score
                OPTIONAL MATCH (u)-[:LIKES|:COMMENTED_ON]->(p)
                WITH p, interest_score, COUNT(u) AS interaction_score
                RETURN p.id_post AS post_id,
                       ($interest_weight * interest_score + $interaction_weight * interaction_score) AS score
                ORDER BY score DESC
                LIMIT $limit
            """, user_id=user_id, interest_weight=interest_weight, interaction_weight=interaction_weight, limit=limit)
            return [record.value()[0] for record in scores]

    def recommend_threads(self, user_id: str, member_weight: float = 0.6, interest_weight: float = 0.4, limit: int = 10) -> list[str]:
        """
        Recommends threads to join based on shared memberships and user interests.

        Parameters:
            user_id (str): The ID of the user for whom recommendations are being generated.
            member_weight (float, optional): Weight assigned to the influence of shared memberships in the recommendation score.
            interest_weight (float, optional): Weight assigned to the influence of shared interests in the recommendation score.

        Returns:
            list[str]: A list of recommended thread IDs, sorted by relevance.
        """
        if not np.isclose(member_weight + interest_weight, 1.0, rtol=1e-09, atol=1e-09):
            raise ValueError('The sum of arguments member_weight and interest_weight must be 1.0')
        with self.db.neo4j_driver.session() as session:
            scores = session.run("""
                MATCH (u:users {idUser: $user_id})-[:MEMBER_OF]->(t:Thread)<-[:MEMBER_OF]-(u2:users)
                WITH t, COUNT(u2) AS member_score
                MATCH (u)-[:INTERESTED_BY]->(i:interests)<-[:HAS_KEY]-(t)
                WITH t, member_score, COUNT(i) AS interest_score
                RETURN t.id_thread AS thread_id,
                       ($member_weight * member_score + $interest_weight * interest_score) AS score
                ORDER BY score DESC
                LIMIT $limit
            """, user_id=user_id, member_weight=member_weight, interest_weight=interest_weight, limit=limit)
            return [record.value()[0] for record in scores]
