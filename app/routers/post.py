from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Depends,
    Body,
    status,
)
from pymongo import ReturnDocument
from datetime import datetime

from ..models.post import (
    PostCreate,
    PostRead,
    PostUpdate,
    PostCollection,
    Post,
)
from ..security.auth import (
    current_user_likes,
    current_user,
    corresponds,
    NOT_AUTHORIZED_ERROR,
)
from .. import mongodb

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post(
    "/",
    response_description="Create a new post",
    response_model=PostRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate = Body(...),
    current_user=Depends(
        current_user_likes(
            {"permission": "posts:create:all"},
            {"permission": "posts:create:own"}
        )),
):
    """
    Create a new post authored by the current user.
    """
    if not post.id_author or not corresponds(current_user, permission="posts:create:all"):
        post.id_author = current_user.uuid

    result = await mongodb.db.posts.insert_one(post.model_dump())
    created_post = await mongodb.db.posts.find_one({"_id": result.inserted_id})
    return created_post


@router.get(
    "/",
    response_description="List all posts",
    response_model=PostCollection,
)
async def list_posts(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    title: str = Query(None, description="Filter by post title"),
    author: str = Query(None, description="Filter by author ID"),
):
    """
    List all posts with optional pagination and filtering.
    """
    query = {}
    if title:
        query["title"] = {"$regex": title, "$options": "i"}
    if author:
        query["id_author"] = author

    posts = await mongodb.db.posts.find(query).skip(skip).limit(limit).to_list(limit)
    return PostCollection(posts=posts)


@router.get(
    "/{id}",
    response_description="Get a single post",
    response_model=PostRead,
)
async def get_post(id: str):
    """
    Retrieve a post by its ID.
    """
    post = await mongodb.db.posts.find_one({"id": id})
    if post:
        return post
    raise HTTPException(status_code=404, detail="Post not found")


@router.put(
    "/{id}",
    response_description="Update a post",
    response_model=PostRead,
)
async def update_post(
    id: str,
    post: PostUpdate = Body(...),
    current_user=Depends(current_user),
):
    """
    Update fields of an existing post.
    """
    existing_post = await mongodb.db.posts.find_one({"id": id})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if existing_post["id_author"] != current_user.uuid:
        raise NOT_AUTHORIZED_ERROR

    post_data = {k: v for k, v in post.dict().items() if v is not None}
    if post_data:
        post_data["updated_at"] = datetime.now()

        updated_post = await mongodb.db.posts.find_one_and_update(
            {"id": id},
            {"$set": post_data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_post:
            return updated_post

    raise HTTPException(status_code=500, detail="Failed to update post")


@router.delete(
    "/{id}",
    response_description="Delete a post",
    response_model=PostRead,
)
async def delete_post(
    id: str,
    current_user=Depends(current_user),
):
    """
    Delete a post by ID.
    """
    post = await mongodb.db.posts.find_one({"id": id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post["id_author"] != current_user.uuid:
        raise NOT_AUTHORIZED_ERROR

    deleted = await mongodb.db.posts.delete_one({"id": id})
    if deleted.deleted_count == 1:
        return post

    raise HTTPException(status_code=500, detail="Failed to delete post")


@router.post(
    "/{id}/like",
    response_description="Like a post",
    response_model=PostRead,
)
async def like_post(
    id: str,
    current_user=Depends(current_user),
):
    """
    Add the current user's like to a post.
    """
    post = await mongodb.db.posts.find_one({"id": id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.uuid in post.get("likes", []):
        raise HTTPException(status_code=400, detail="Post already liked")
 
    updated_post = await mongodb.db.posts.find_one_and_update(
        {"id": id},
        {"$addToSet": {"likes": current_user.uuid}},
        return_document=ReturnDocument.AFTER,
    )
    return updated_post


@router.post(
    "/{id}/unlike",
    response_description="Unlike a post",
    response_model=PostRead,
)
async def unlike_post(
    id: str,
    current_user=Depends(current_user),
):
    """
    Remove the current user's like from a post.
    """
    post = await mongodb.db.posts.find_one({"id": id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user.uuid not in post.get("likes", []):
        raise HTTPException(status_code=400, detail="Post not liked")

    updated_post = await mongodb.db.posts.find_one_and_update(
        {"id": id},
        {"$pull": {"likes": current_user.uuid}},
        return_document=ReturnDocument.AFTER,
    )
    return updated_post
