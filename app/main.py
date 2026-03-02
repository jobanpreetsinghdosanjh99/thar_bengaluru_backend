from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables
from app.seed import seed_data
from app.routes import auth, feeds, accessories, merchandise, membership, tblr, cart, buy_sell

# Create FastAPI app
app = FastAPI(
    title="THAR Bengaluru Backend",
    description="Backend API for THAR 4x4 Club Management App",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
def startup():
    create_tables()
    seed_data()
    print("Database tables created and seeded")


# Include routers
app.include_router(auth.router)
app.include_router(feeds.router)
app.include_router(accessories.router)
app.include_router(merchandise.router)
app.include_router(membership.router)
app.include_router(tblr.router)
app.include_router(cart.router)
app.include_router(buy_sell.router)


@app.get("/", tags=["health"])
def read_root():
    """Health check endpoint."""
    return {
        "message": "THAR Bengaluru Backend API",
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check for deployment monitoring."""
    return {"status": "healthy"}
