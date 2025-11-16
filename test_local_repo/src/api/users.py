"""
User API endpoints.

Handles user registration, authentication, profile management,
and user-related operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from src.database import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from src.services.auth import get_current_user, hash_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        UserResponse: Created user data
    """
    # Check if user already exists
    existing_user = await User.get_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    user = await User.create(
        db,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )

    logger.info(f"New user registered: {user.email}")
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    Args:
        current_user: Authenticated user

    Returns:
        UserResponse: User profile data
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.

    Args:
        user_update: Updated user data
        current_user: Authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user data
    """
    updated_user = await current_user.update(db, **user_update.dict(exclude_unset=True))
    logger.info(f"User profile updated: {updated_user.email}")
    return updated_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin endpoint).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List[UserResponse]: List of users
    """
    users = await User.get_all(db, skip=skip, limit=limit)
    return users
