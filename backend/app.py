"""
FastAPI application entry point for Face Access Control System.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes import recognition, users, logs, config
from database import init_database, SessionLocal
from core.face_engine import get_face_engine
from core.model_downloader import ModelDownloader
from utils.file_utils import ensure_directories
from utils.logger import setup_logger, get_logger

# Setup logging
setup_logger()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Face Access Control System",
    description="Web-based facial access control system with ULFD + ArcFace",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(recognition.router, tags=["Recognition"])
app.include_router(users.router, tags=["Users"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(config.router, tags=["Configuration"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize system on application startup."""
    logger.info("=" * 60)
    logger.info("🚀 Starting Face Access Control System")
    logger.info("=" * 60)

    try:
        # Step 1: Ensure directory structure exists
        logger.info("📁 Checking directory structure...")
        ensure_directories()
        logger.info("✓ Directories verified")

        # Step 2: Initialize database
        logger.info("🗄️  Initializing database...")
        init_database()
        logger.info("✓ Database initialized")

        # Step 3: Download models if needed
        logger.info("📦 Checking AI models...")
        ulfd_success, arcface_success = await ModelDownloader.download_all_models()

        if not (ulfd_success and arcface_success):
            logger.warning("⚠️  Some models are missing. System functionality may be limited.")
            if not ulfd_success:
                logger.warning("   - ULFD model: Not available (face detection disabled)")
            if not arcface_success:
                logger.warning("   - ArcFace model: Not available (feature extraction disabled)")
        else:
            logger.info("✓ All models ready")

        # Step 4: Initialize face engine
        logger.info("🤖 Initializing face recognition engine...")
        engine = get_face_engine()

        # Step 5: Load face database into memory
        logger.info("💾 Loading face database into memory...")
        db = SessionLocal()
        try:
            engine.load_face_database(db)
            logger.info(f"✓ Loaded {len(engine.face_database)} user features")
        finally:
            db.close()

        logger.info("=" * 60)
        logger.info("✅ System ready! Access API at http://localhost:8000")
        logger.info("📖 API docs available at http://localhost:8000/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Face Access Control System API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    engine = get_face_engine()
    return {
        "status": "healthy",
        "models_loaded": {
            "ulfd": engine.ulfd_session is not None,
            "arcface": engine.arcface_session is not None
        },
        "users_in_database": len(engine.face_database)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
