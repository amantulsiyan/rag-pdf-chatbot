import os
import psycopg2
from dotenv import load_dotenv
from fastapi import status, APIRouter, HTTPException, Depends
from api.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

from api.auth import (
    hash_password,
    verify_password,
    create_access_token
)
from api.models import RegisterRequest
load_dotenv()
router = APIRouter(tags = ['Authentication'])

def get_db_connection():
    db_password= os.getenv("DB_PASSWORD")
    if not db_password:
        raise RuntimeError("DB_PASSWORD is missing from .env")
    return psycopg2.connect(
        dbname = "rag_db",
        user = "postgres",
        password = db_password,
        host = 'localhost',
        port = '5432'
    )


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user":current_user}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(data: RegisterRequest):
    email = str(data.email).strip().lower()
    password_hash_value = hash_password(data.password)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users(email,password_hash)
                VALUES (%s,%s)
                RETURNING id, email, created_at
                """,
                (email,password_hash_value),
            )
            user = cursor.fetchone()

        conn.commit()
        return {
            "message":"User registered successfully",
            "user": {
                "id": user[0],
                "email": user[1],
                "created_at": user[2],
            },
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail ="An account with this email already exists",
        )
    finally:
        conn.close()

@router.post("/token")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    email = form_data.username.strip().lower()
    password = form_data.password

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash
                FROM users
                WHERE LOWER(email) = %s
                """,
                (email,),
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if user is None or not verify_password(password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(str(user[0]))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }