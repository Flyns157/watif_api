from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI


# === Main application setup === #
app = FastAPI(
    title="Student Course API",
    summary="A sample application showing how to use FastAPI to add a ReST API to a MongoDB collection.",
)

# === Authentication === #
# TODO : Implement auth with the password context for hashing and verifying passwords


# === Routes for the API === #
from .routers.user import router
app.include_router(router)

# Mount the static files directory
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# @app.middleware("http") # TODO : Implement caching for static files
# async def add_cache_control_header(request, call_next):
#     response = await call_next(request)
#     response.headers["Cache-Control"] = "no-store" 
#     return response
