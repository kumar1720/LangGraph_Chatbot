import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.agent.langgraph_agent import initialize_graph, close_graph
from app.api.api import api_router
from app.core.config import settings
from app.db.mongodb import db
from app.services.vector_store import MultiTenantVectorStore
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-emptively initialize both vector stores to ensure they exist and have correct indexes
    try:
        MultiTenantVectorStore(collection_name="multi_tenant_chat_history")
        MultiTenantVectorStore(collection_name="multi_tenant_rag_docs")
        logger.info("Successfully pre-emptively initialized all Qdrant vector store collections and indexes")
    except Exception as e:
        logger.warning(f"Error pre-emptively initializing Qdrant collections: {e}")

    await initialize_graph()
    
    # Connect to MongoDB Atlas
    db.connect_db()
    logger.info("Successfully connected to persistent MongoDB Atlas cluster")

    logger.info(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
    logger.info(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")

    yield

    # Disconnect MongoDB client
    db.close_db()
    logger.info("Successfully disconnected from MongoDB Atlas")
    await close_graph()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

# Mount React static files (JS, CSS, index.html)
base_dir = os.path.dirname(os.path.dirname(__file__))
frontend_dist = os.path.join(base_dir, "frontend", "dist")
frontend_build = os.path.join(base_dir, "frontend", "build")

# Check which folder exists (react-scripts build uses build, vite uses dist)
frontend_dir = frontend_build if os.path.exists(frontend_build) else frontend_dist

if os.path.exists(frontend_dir):
    # Mount Vite static assets (/assets)
    assets_dir = os.path.join(frontend_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        
    # Mount React App static assets (/static)
    static_dir = os.path.join(frontend_dir, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Catch-all endpoint to serve React index.html for client-side SPA routing (React Router fallback)
    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Ignore API calls or openapi documentation prefixes
        if catchall.startswith("api/") or catchall.startswith("docs") or catchall.startswith("redoc") or catchall.startswith("openapi.json"):
            return None
            
        # Check if the requested file exists in the root of frontend_dir (e.g. favicon.ico, manifest.json)
        file_path = os.path.join(frontend_dir, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
