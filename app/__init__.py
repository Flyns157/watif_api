from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
import logging
import time


__version__ = "0.1.0"


# === Set up logging === #
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("app.log"),  # Log to a file
                        logging.StreamHandler()          # Also log to console
                    ])
main_logger = logging.getLogger(__name__)


# === Main application setup === #
app = FastAPI(
    title="Student Course API",
    summary="A sample application showing how to use FastAPI to add a ReST API to a MongoDB collection.",
)

# === Middleware === #
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    # main_logger.info(f"Request: {request.method} {request.url}")  # Log the request method and URL
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    main_logger.info(f"Processed {request.method} {request.url} in {process_time:.4f} secs")  # Log the processing time
    return response


# === Routes for the API === #
from .routers import auth_router, users_router
app.include_router(auth_router)
app.include_router(users_router)

# Mount the static files directory
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
