"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, LoginResponse
from ..sessions import issue_token, path_user_id, revoke_token, session_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Login or create user by name (no password for demo) and issue a session token."""
    # Find existing user
    result = await db.execute(
        select(User).where(User.name == user_data.name)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(name=user_data.name)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return LoginResponse(
        **UserResponse.model_validate(user).model_dump(),
        token=issue_token(user.id),
    )


@router.post("/logout")
async def logout(token: str = Depends(session_token)):
    """Revoke the caller's session token."""
    revoke_token(token)
    return {"status": "success"}


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int = Depends(path_user_id), db: AsyncSession = Depends(get_db)):
    """Get user by ID (only the caller's own user)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user
