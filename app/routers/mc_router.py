"""
This file contains the API routes for the Monte Carlo-based recommendation engine.
"""
from fastapi import APIRouter, HTTPException, Query

from ..services.Recommender.mc_engine import MC_engine
from ..data.databases import get_database
from .. import main_logger


router = APIRouter(prefix="/recommend/MC", tags=["Monte Carlo-based Recommendation"])


@router.get("/users")
async def recommend_users(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    follow_weight: float = Query(0.5, description="Weight for mutual followers in scoring."),
    interest_weight: float = Query(0.5, description="Weight for shared interests in scoring."),
    limit: int = Query(10, description="Size of the recommendation."),
) -> dict[str, list[str]]:
    """
    Recommend user profiles based on shared interests and mutual connections.

    Returns:
        JSON: A JSON response containing a list of recommended user IDs or an error message.
    """

    try:
        recommendations = MC_engine(get_database()).recommend_users(user_id, follow_weight, interest_weight, limit)
        return {"recommended_users": recommendations}
    except Exception as e:
        main_logger.error(f"Error in recommend_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def recommend_posts(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    interest_weight: float = Query(0.7, description="Weight for shared interests in scoring."),
    interaction_weight: float = Query(0.3, description="Weight for user interactions in scoring."),
    limit: int = Query(10, description="Size of the recommendation."),
) -> dict[str, list[str]]:
    """
    Recommend posts based on shared interests and user interactions.

    Returns:
        JSON: A JSON response containing a list of recommended post IDs or an error message.
    """

    try:
        recommendations = MC_engine(get_database()).recommend_posts(user_id, interest_weight, interaction_weight, limit)
        return {"recommended_posts": recommendations}
    except Exception as e:
        main_logger.error(f"Error in recommend_posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads")
async def recommend_threads(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    member_weight: float = Query(0.6, description="Weight for shared memberships in scoring."),
    interest_weight: float = Query(0.4, description="Weight for shared interests in scoring."),
    limit: int = Query(10, description="Size of the recommendation."),
) -> dict[str, list[str]]:
    """
    Recommend threads for a user based on shared memberships and interests.

    Returns:
        JSON: A JSON response containing a list of recommended thread IDs or an error message.
    """

    try:
        recommendations = MC_engine(get_database()).recommend_threads(user_id, member_weight, interest_weight, limit)
        return {"recommended_threads": recommendations}
    except Exception as e:
        main_logger.error(f"Error in recommend_threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
