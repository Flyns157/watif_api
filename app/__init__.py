"""
This is the initialization application file.
"""
import logging
from contextlib import asynccontextmanager
import time
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

from .utils.config import Settings, Mode
from .routers import auth_router, users_router
from .data.databases.mongodb import MongoManager

__version__ = "0.1.0"


# === Set up logging and database === #
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()          # Also log to console
                    ])
main_logger = logging.getLogger(__name__)


async def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger for a given module.
    """
    return main_logger.getChild(name)



mongodb = MongoManager()

async def get_database() -> AsyncIOMotorDatabase:
    return mongodb.db


# === Main application setup === #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Defines application startup and shutdown actions.
    """
    await mongodb.connect_to_database()
    yield
    await mongodb.close_database_connection()


app = FastAPI(
    title="Watif Backend API",
    summary="A backend application to a social network named Watif.",
    lifespan=lifespan,
)


# === Middleware === #
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Add a header to the response with the processing time of the request.
    """
    start_time = time.perf_counter()
    # main_logger.info(f"Request: {request.method} {request.url}")  # Log the request method and URL
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    main_logger.info(
        "Processed %s %s in %.4f secs",
        request.method,
        request.url,
        process_time
    )  # Log the processing time
    return response


# === Routes for the API === #
app.include_router(auth_router)
app.include_router(users_router)

if Settings.MODE == Mode.MAIN:
    ...  # Add additional routes for the main app here


# === Mount static files directory === #
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
