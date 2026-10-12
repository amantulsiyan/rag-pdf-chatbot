import os 
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY not in .env file")

password_hash = PasswordHash.recommended()

#Hash a password before storing it
def hash_password(password: str) -> str:
    return password_hash.hash(password)

#2. Verify login against stored hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

#3. Create JWT access token for user
def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload ={
        "sub":user_id,
        "iat":now,
        "exp":now + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(
        payload, 
        JWT_SECRET_KEY,
        algorithm = JWT_ALGORITHM,
    )
    return token

#4. Decode and validate the JWT access token
def decode_access_token(token: str)-> dict:
    payload=jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options = {"require":["sub","exp"]},
    )
    return payload