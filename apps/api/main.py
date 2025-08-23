from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import returns, artifacts, review

app = FastAPI(title="Tax Return Processing API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(returns.router)
app.include_router(artifacts.router)
app.include_router(review.router)


@app.get("/")
async def root():
    return {"message": "Tax Return Processing API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}