from pydantic import BaseModel, field_validator
import re
from db import DatabaseConnection
from typing import Optional
from passlib.context import CryptContext
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError
from config import settings

router = APIRouter()

logger = logging.getLogger('app')

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")  # provided password hashing


class CredentialsError(Exception):
    pass


class User(BaseModel):
    user_id: int
    created_at: datetime
    active: bool
    email: str
    first_name: str
    last_name: str
    password: str


class Credentials(BaseModel):
    email: str
    password: str


class CreateUser(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

    @field_validator("email")
    def is_email(cls, value: str) -> str:
        """Check for invalid email when the object is instantiated."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        is_valid = re.fullmatch(pattern, value)
        if not is_valid:
            raise ValueError('Email not valid.')
        return value

    @field_validator("password")
    def is_password(cls, value: str) -> str:
        """Check for invalid password when the object is instantiated."""
        pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
        is_valid = re.fullmatch(pattern, value)
        if not is_valid:
            raise ValueError('Password has to have a minimum of 8 characters and at least 1 digit, 1 letter.')
        return value


def create_user(new_user: CreateUser) -> int:
    """Creates a new user and returns the user_id."""
    hashed_password = pwd_context.hash(new_user.password)
    new_user.password = hashed_password
    with DatabaseConnection() as db:
        db.cursor.execute("""
        INSERT INTO app.users(email, first_name, last_name, password) 
        VALUES (%(email)s, %(first_name)s, %(last_name)s, %(password)s)
        ON CONFLICT ON CONSTRAINT unique_email do update set
            email = excluded.email,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            password = excluded.password
        RETURNING user_id;
        """, dict(new_user))
        user = db.cursor.fetchone()
        db.cursor.connection.commit()
    return user['user_id']


def login(credentials: Credentials) -> dict:
    """Take the email and find the user. Verify the user-provided password with the right password."""
    user = get_user_by_email(credentials.email)
    if user is None:
        raise CredentialsError("Invalid credentials.")
    valid_credentials = pwd_context.verify(credentials.password, user.password)
    if not valid_credentials:
        raise CredentialsError("Invalid credentials.")

    access_token = create_access_token({'user_id': user.user_id})
    return {'access_token': access_token, 'token_type': 'bearer'}


def create_access_token(to_encode: dict):
    """Create a token for the user such that it does not need to login next call."""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_TOKEN_EXPIRY_MINUTES)
    to_encode['expire'] = expire.strftime("%Y-%m-%d %H:%M:S")
    return jwt.encode(to_encode, settings.SECRET_KEY, settings.JWT_ENCRYPTION_ALGORITHM)


def get_current_user(token: str) -> Optional[User]:
    """Returns the user model instance given a JWT token."""
    user_id: int = verify_user(token)
    return get_user_by_id(user_id)


def verify_user(token: str) -> int:
    """Verify the access token and give back the user id."""
    payload = jwt.decode(token, settings.SECRET_KEY, settings.JWT_ENCRYPTION_ALGORITHM)  # verifies a JWT string's signature.
    user_id = payload.get("user_id", None)
    if user_id is None:
        raise CredentialsError("User id cannot be obtained from jwt.")
    return int(user_id)


def get_user_by_id(user_id: int) -> Optional[User]:
    """Returns the user from the database given a user_id."""
    with DatabaseConnection() as db:
        db.cursor.execute("""
        SELECT * FROM app.users WHERE user_id = %(user_id)s AND active = true;
        """, {'user_id': user_id})
        user = db.cursor.fetchone()
        db.cursor.connection.commit()
    if not user:
        return None
    return User(**user)


def get_user_by_email(email: str) -> Optional[User]:
    with DatabaseConnection() as db:
        db.cursor.execute("""
        SELECT * FROM app.users WHERE email = %(email)s AND active = true;
        """, {'email': email})
        user = db.cursor.fetchone()
        db.cursor.connection.commit()
    if not user:
        return None
    return User(**user)


@router.post("/login")
async def login_user(credentials: Credentials):
    try:
        return login(credentials)
    except CredentialsError:
        logger.error(f"Unable to login user {credentials}", exc_info=True)
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except Exception:
        logger.error(f"Unable to login user {credentials}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to login user.")


@router.post("/user")
async def create_new_user(user: CreateUser):
    try:
        return create_user(user)
    except Exception:
        logger.error(f"Unable to create user {user}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to create user.")


@router.get("/user/{user_id}")
async def get_user(token, user_id):
    try:
        verify_user(token)
        return get_user_by_id(user_id)
    except JWTError:
        logger.error(f"Unable to decode JWT.")
        raise HTTPException(status_code=422, detail="Cannot verify user.")
    except Exception:
        logger.error(f"Unable to get user {user_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to get user.")
