
import os
import time
import math
import uuid
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from redis.asyncio import Redis
from redis.exceptions import RedisError

from api.dependencies import initialize_app
from api.routes import upload, query, auth_routes


logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

# Rate-limiting configuration
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "5"))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "60"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Atomic Redis sliding-window rate limiter.
# Returns:
# [1, 0, current_count] if allowed
# [0, retry_after_seconds, current_count] if blocked
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local member = ARGV[3]
local limit = tonumber(ARGV[4])

redis.call(
    'ZREMRANGEBYSCORE',
    key,
    '-inf',
    now - window
)

local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call(
        'ZRANGE',
        key,
        0,
        0,
        'WITHSCORES'
    )

    local retry_after = math.ceil(
        (tonumber(oldest[2]) + window - now) / 1000
    )

    return {0, retry_after, count}
end

redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window + 5000)

count = count + 1

return {1, 0, count}
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create one shared Redis connection pool per application process.
    app.state.redis = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    # Verify Redis is available before accepting requests.
    await app.state.redis.ping()

    logger.info("Redis connection established")

    try:
        yield
    finally:
        await app.state.redis.aclose()
        logger.info("Redis connection closed")


app = FastAPI(
    title="RAG PDF API",
    lifespan=lifespan,
)


# CORS Configuration
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8080",
]


# Paths exempted from rate limiting
EXEMPT_PATHS = {
    "/",
    "/health",
}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    # Skip CORS preflight requests
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip exempt paths
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    # Identify client
    client = request.client
    client_ip = client.host if client else "unknown"

    # Use wall-clock time because Redis is shared across processes.
    current_time_ms = int(time.time() * 1000)

    window_ms = WINDOW_SIZE * 1000

    # Separate sorted set for each client.
    redis_key = f"rate_limit:{client_ip}"

    try:
        result = await request.app.state.redis.eval(
            RATE_LIMIT_SCRIPT,
            1,
            redis_key,
            current_time_ms,
            window_ms,
            str(uuid.uuid4()),
            RATE_LIMIT,
        )

    except RedisError:
        logger.exception("Redis rate limiter unavailable")

        return JSONResponse(
            status_code=503,
            content={
                "detail": "Rate limiting service temporarily unavailable."
            },
        )

    allowed = int(result[0])
    retry_after = int(result[1])
    request_count = int(result[2])

    remaining = max(0, RATE_LIMIT - request_count)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please try again later."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)

    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    return response


# Initialize application state
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
