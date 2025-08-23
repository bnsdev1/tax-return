from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import returns, artifacts, review, challan, rules, export, settings_llm

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
app.include_router(challan.router)
app.include_router(rules.router)
app.include_router(export.router)
app.include_router(settings_llm.router)


@app.get("/")
async def root():
    return {"message": "Tax Return Processing API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}