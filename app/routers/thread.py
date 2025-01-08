from fastapi import (
    APIRouter, 
    HTTPException, 
    Query, 
    Depends, 
    Body, 
    status
)
from pymongo import ReturnDocument
from datetime import datetime

from ..data.models.thread import (
    ThreadCreate, 
    ThreadRead, 
    ThreadUpdate, 
    ThreadCollection, 
    Thread
)
from ..security.auth import (
    current_user, 
    corresponds, 
    NOT_AUTHORIZED_ERROR
)
from .. import mongodb

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post(
    "/",
    response_description="Create a new thread",
    response_model=ThreadRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    thread: ThreadCreate = Body(...),
    current_user = Depends(current_user),
):
    """
    Insert a new thread record.
    """
    if not thread.id_owner or corresponds(user=current_user, permission="threads:create:all"):
        thread.id_owner = current_user.uuid

    try:
        result = await mongodb.db.threads.insert_one(thread.model_dump())
        created_thread = await mongodb.db.threads.find_one({"uuid": result.inserted_id})
        return created_thread
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating thread: {e}")


@router.get(
    "/",
    response_description="List all threads",
    response_model=ThreadCollection,
)
async def list_threads(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    name: str = Query(None, description="Filter by thread name"),
    public: bool = Query(None, description="Filter by public status"),
    current_user = Depends(current_user) | None,
):
    """
    List all threads with pagination and optional filters.
    """
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if public is not None:
        query["public"] = public

    threads = await mongodb.db.threads.find(query).skip(skip).limit(limit).to_list(limit)
    if not corresponds(user=current_user, permission="threads:read:private:all"):
        threads = [t for t in threads if not t["private"] or t["id_owner"] == current_user.uuid]
    return ThreadCollection(threads=threads)


@router.get(
    "/{id}",
    response_description="Get a single thread",
    response_model=ThreadRead,
)
async def get_thread(id: str):
    """
    Retrieve a thread by ID.
    """
    thread = await mongodb.db.threads.find_one({"id": id})
    if thread:
        return thread
    raise HTTPException(status_code=404, detail="Thread not found")


@router.put(
    "/{id}",
    response_description="Update a thread",
    response_model=ThreadRead,
)
async def update_thread(
    id: str,
    thread: ThreadUpdate = Body(...),
    current_user = Depends(current_user),
):
    """
    Update fields of an existing thread.
    """
    existing_thread = await mongodb.db.threads.find_one({"id": id})
    if not existing_thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if existing_thread["id_owner"] != current_user.uuid:
        raise NOT_AUTHORIZED_ERROR

    thread_data = {k: v for k, v in thread.model_dump.items() if v is not None}
    if thread_data:
        thread_data["updated_at"] = datetime.now()

        updated_thread = await mongodb.db.threads.find_one_and_update(
            {"id": id},
            {"$set": thread_data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_thread:
            return updated_thread

    raise HTTPException(status_code=500, detail="Failed to update thread")


@router.delete(
    "/{id}",
    response_description="Delete a thread",
    response_model=ThreadRead,
)
async def delete_thread(
    id: str,
    current_user = Depends(current_user),
):
    """
    Delete a thread by ID.
    """
    thread = await mongodb.db.threads.find_one({"id": id})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if thread["id_owner"] != current_user.uuid:
        raise NOT_AUTHORIZED_ERROR

    deleted = await mongodb.db.threads.delete_one({"id": id})
    if deleted.deleted_count == 1:
        return thread

    raise HTTPException(status_code=500, detail="Failed to delete thread")
