"""
This file contains the API routes for the EM-based (embedding) recommendation engine.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from ..core.Recommender.em_engine import EM_engine
from ..database import get_database
from .. import main_logger


router = APIRouter(prefix="/recommend/EM", tags=["EM-based Recommendation (embedding)"])


@router.get("/users")
async def recommend_users(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    limit: int = Query(10, description="The size of the recommendation.")
) -> list[str]:
    """
    Recommend user profiles based on shared interests and mutual connections.

    Returns:
        JSON: A JSON response containing a list of recommended user IDs or an error message.
        Status Code:
            200: Success, returns recommended users.
            400: Bad request, missing required parameters.
            500: Server error, failed to generate recommendations.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id parameter")

    try:
        recommendations = EM_engine(get_database()).recommend_users(user_id, limit)
        return JSONResponse(content={"recommended_users": recommendations})
    except Exception as e:
        main_logger.error(f"Error in recommend_users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def recommend_posts(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    limit: int = Query(10, description="The size of the recommendation.")
) -> list[str]:
    """
    Recommend posts based on shared interests and user interactions.

    Returns:
        JSON: A JSON response containing a list of recommended post IDs or an error message.
        Status Code:
            200: Success, returns recommended posts.
            400: Bad request, missing required parameters.
            500: Server error, failed to generate recommendations.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id parameter")

    try:
        recommendations = EM_engine(get_database()).recommend_posts(user_id, limit)
        return JSONResponse(content={"recommended_posts": recommendations})
    except Exception as e:
        main_logger.error(f"Error in recommend_posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads")
async def recommend_threads(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    limit: int = Query(10, description="The size of the recommendation.")
) -> list[str]:
    """
    Recommend threads for a user based on shared memberships and interests.

    Returns:
        JSON: A JSON response containing a list of recommended thread IDs or an error message.
        Status Code:
            200: Success, returns recommended threads.
            400: Bad request, missing required parameters.
            500: Server error, failed to generate recommendations.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id parameter")

    try:
        recommendations = EM_engine(get_database()).recommend_threads(user_id, limit)
        return JSONResponse(content={"recommended_threads": recommendations})
    except Exception as e:
        main_logger.error(f"Error in recommend_threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
