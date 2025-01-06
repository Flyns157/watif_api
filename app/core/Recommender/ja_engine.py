"""
Recommendation engine by Jean-Alexis, using neo4j database.
"""
from . import recommender_engine
import random
import numpy as np


class JA_engine(recommender_engine):
    def get_hastags(self, id_user: str) -> set:
        """
        Retrieve hashtags used by a specific user.

        Args:
            id_user (str): The ID of the user.

        Returns:
            set: A set of hashtags used by the user.
        """
        with self.db.neo4j_driver.session() as session:
            hashtags = session.run(
                "MATCH (u:users),(p:posts),(k:keys) WHERE u.idUser = $id_user RETURN k.idKey AS ids",
                id_user=str(id_user)
            )
            hashtag_set = set()
            for record in hashtags:
                hashtag_set.update(record["ids"])
            return hashtag_set

    def recommend_users(self, id_user: str, follow_weight: float = 0.4, intrest_weight: float = 0.6) -> list[str]:
        """
        Generate profile recommendations for a specific user based on mutual follows and interests.

        Args:
            id_user (str): The ID of the user.
            follow_weight (float): The weight given to the follow score in the recommendation algorithm. Default is 0.4.
            intrest_weight (float): The weight given to the interest score in the recommendation algorithm. Default is 0.6.

        Returns:
            list[str]: A sorted list of recommended user IDs.

        Raises:
            ValueError: If the sum of follow_weight and intrest_weight is not equal to 1.0.

        Example:
            >>> recommender.recommend_users(123, follow_weight=0.5, intrest_weight=0.5)
            [456, 789, 1011]
        """
        if not np.isclose(follow_weight + intrest_weight, 1.0, rtol=1e-09, atol=1e-09):
            raise ValueError('The sum of arguments follow_weight and intrest_weight must be 1.0')
        with self.db.neo4j_driver.session() as session:
            user = session.run(
                "MATCH (u:users) WHERE u.idUser = $id_user RETURN u",
                id_user=str(id_user)
            ).single()

            users = session.run(
                "MATCH (u:users) WHERE u.idUser <> $id_user RETURN u",
                id_user=id_user
            )

            scores = {}
            user_follows = {rel for rel in session.run(
                "MATCH (u:users)-[f:FOLLOWS]->(f2:users) WHERE u.idUser = $id_user RETURN f2",
                id_user=id_user
            )}

            user_interests = {rel.value() for rel in session.run(
                "MATCH (u:users)-[ib:INTERESTED_BY]->(i:interests) WHERE u.idUser = $id_user RETURN i.idInterest",
                id_user=id_user
            )}

            for u in users:
                u_follows = {rel for rel in session.run(
                    "MATCH (u:users)-[f:FOLLOWS]->(f2:users) WHERE u.idUser = $id_user RETURN f2",
                    id_user=u["u"]["idUser"]
                )}

                follows_score = len(user_follows & u_follows) / len(user_follows | u_follows) if user_follows and u_follows else 0

                u_interests = {rel.value() for rel in session.run(
                    "MATCH (u:users)-[ib:INTERESTED_BY]->(i:interests) WHERE u.idUser = $id_user RETURN i.idInterest",
                    id_user=u["u"]["idUser"]
                )}

                interests_score = len(user_interests & u_interests) / len(user_interests | u_interests) if user_interests and u_interests else 0

                rec_score = ((follows_score*follow_weight) + (interests_score*intrest_weight)) / 2
                scores[u["u"]["idUser"]] = rec_score

            return sorted(scores, key=scores.get, reverse=True)

    def recommend_posts(self, id_user: str) -> list[str]:
        """
        Generate post recommendations for a specific user based on hashtags and interests.

        Args:
            id_user (str): The ID of the user.

        Returns:
            list: A sorted list of recommended post IDs.
        """
        with self.db.neo4j_driver.session() as session:
            posts = session.run(
                "MATCH (u:users),(p:posts) WHERE u.idUser <> $id_user RETURN p.idPost",
                id_user=str(id_user)
            ).value()

            user_hashtags = self.get_hastags(id_user)
            scores = {}
            print(user_hashtags)

            if not user_hashtags:
                user_interests = session.run(
                    "MATCH (u:users)-[ib:INTERESTED_BY]->(i:interests) WHERE u.idUser = $id_user RETURN i.idInterest AS interests",
                    id_user=id_user
                ).single()["interests"]

                for post in posts:
                    id_author = session.run(
                        "MATCH (u:users),(p:posts) WHERE u.idUser = $id_user RETURN u.idUser AS id",
                        id_user=post
                    ).single()["id"]

                    u = session.run(
                        "MATCH (u:users)-[ib:INTERESTED_BY]->(i:interests) WHERE u.idUser = $id_author RETURN i.idInterest AS interests",
                        id_author=id_author
                    ).single()["interests"]

                    interests_score = len(set(user_interests) & set(u)) / len(set(user_interests) | set(u))
                    scores[post] = interests_score
            else:
                for post in posts:
                    hashtags = session.run(
                        "MATCH (p:posts),(k:keys) WHERE p.idPost = $idPost RETURN k.idKey AS ids",
                        idPost=post
                    )
                    post_hashtags = set()
                    for record in hashtags:
                        post_hashtags.update(record["ids"])

                    score = len(user_hashtags & post_hashtags) / len(user_hashtags | post_hashtags)
                    scores[post] = score

            scores_tab = sorted(scores, key=scores.get, reverse=True)

            for s in range(len(scores_tab)):
                if random.random() >= 0.8:
                    scores_tab.insert(s, scores_tab[-1])
                    del scores_tab[-1]

            return scores_tab
