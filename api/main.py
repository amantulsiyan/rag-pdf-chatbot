import time
import math

from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import initialize_app
from api.routes import upload, query, auth_routes


app = FastAPI(title="RAG PDF API")


# CORS Configuration
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
]


# Rate Limiting Configuration
RATE_LIMIT = 10000
WINDOW_SIZE = 60

CLIENT_TTL = 3600
CLEANUP_INTERVAL = 300


# Stores timestamps for every client
request_timestamps = {}

last_cleanup_time = time.monotonic()


# Paths exempted from rate limiting
EXEMPT_PATHS = {
    "/",
    "/health",
}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    global last_cleanup_time

    # Skip CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip exempt paths
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    # Identify client
    client = request.client
    client_ip = client.host if client else "unknown"

    current_time = time.monotonic()

    # Periodic cleanup of inactive clients
    if current_time - last_cleanup_time >= CLEANUP_INTERVAL:

        expired_clients = [
            ip
            for ip, data in request_timestamps.items()
            if current_time - data["last_seen"] >= CLIENT_TTL
        ]

        for ip in expired_clients:
            del request_timestamps[ip]

        last_cleanup_time = current_time

    # Initialize client if seeing it for the first time
    if client_ip not in request_timestamps:

        request_timestamps[client_ip] = {
            "timestamps": deque(),
            "last_seen": current_time
        }

    client_data = request_timestamps[client_ip]

    # Update last activity time
    client_data["last_seen"] = current_time

    timestamps = client_data["timestamps"]

    # Calculate rolling window boundary
    window_start = current_time - WINDOW_SIZE

    # Remove timestamps outside the rolling window
    while timestamps and timestamps[0] <= window_start:
        timestamps.popleft()

    # Check rate limit
    if len(timestamps) >= RATE_LIMIT:

        retry_after = math.ceil(
            timestamps[0] + WINDOW_SIZE - current_time
        )

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0"
            }
        )

    # Allow request and record its timestamp
    timestamps.append(current_time)

    response = await call_next(request)

    # Calculate remaining requests
    remaining_requests = max(
        0,
        RATE_LIMIT - len(timestamps)
    )

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)

    response.headers["X-RateLimit-Remaining"] = str(
        remaining_requests
    )
    return response


# Initialize application
initialize_app(app)


# Register routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(auth_routes.router)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "RAG PDF API is running"}


# Health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)