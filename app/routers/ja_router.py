"""
This file contains the API routes for Jean-Alexis Recommendation Engine.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from ..core.Recommender.ja_engine import JA_engine
from ..database import get_database
from ..utils.config import Config

from .. import main_logger


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(prefix="/recommend/JA", tags=["Jean-Alexis Recommendation"])


def get_current_user(token: str = Depends(oauth2_scheme)):
    # This function would contain the logic to verify the user token
    # For now, we just simulate it by returning the token as the user
    if Config.NO_AUTH:
        return None
    return token

@router.get("/users")
async def recommend_users(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    follow_weight: float = Query(0.5, description="The weight given to mutual followers in scoring."),
    interest_weight: float = Query(0.5, description="The weight given to shared interests in scoring."),
    # current_user: str = Depends(get_current_user)
) -> dict[str, list[str]]:
    """
    Recommend user profiles based on shared interests and mutual connections.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id parameter")

    try:
        recommendations = JA_engine(get_database()).recommend_users(user_id, follow_weight, interest_weight)
        return {"recommended_users": recommendations}
    except Exception as e:
        main_logger.error(f"Error in recommend_users: {e}")
        # recommendations = JA_engine(get_database()).recommend_users(user_id, follow_weight, interest_weight)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def recommend_posts(
    user_id: str = Query(..., description="The ID of the user requesting recommendations."),
    interest_weight: float = Query(0.7, description="The weight given to shared interests in scoring."),
    interaction_weight: float = Query(0.3, description="The weight given to user interactions (likes, comments) in scoring."),
    # current_user: str = Depends(get_current_user)
) -> dict[str, list[str]]:
    """
    Recommend posts based on shared interests and user interactions.
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id parameter")

    try:
        recommendations = JA_engine(get_database()).recommend_posts(user_id)
        return {"recommended_posts": recommendations}
    except Exception as e:
        main_logger.error(f"Error in recommend_posts: {e}")
        # recommendations = JA_engine(get_database()).recommend_posts(user_id)
        raise HTTPException(status_code=500, detail=str(e))
