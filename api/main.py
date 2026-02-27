from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.dependencies import initialize_app
from api.routes import upload, query

app = FastAPI(title="RAG PDF API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_app(app)

app.include_router(upload.router)
app.include_router(query.router)

@app.get("/")
def root():
    return {"message": "RAG PDF API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}