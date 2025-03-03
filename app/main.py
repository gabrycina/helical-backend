from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.routes import router 
from app.api.routes.workflows import lifespan 

settings = get_settings()

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan  
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create upload directory if it doesn't exist
    settings.UPLOAD_DIR.mkdir(exist_ok=True)

    # Include main router
    app.include_router(router, prefix=settings.API_V1_STR)

    return app

app = create_application()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 