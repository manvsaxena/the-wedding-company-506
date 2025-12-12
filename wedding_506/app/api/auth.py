from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..models import Token, UserInDB
from ..auth import AuthHandler, get_current_user
from ..database import UserDB
from ..config import get_settings

router = APIRouter(tags=["Authentication"])
auth_handler = AuthHandler()
settings = get_settings()

@router.post("/admin/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_db = UserDB()
    user = await user_db.get_user_by_email(form_data.username)  # username is email in this case
    
    if not user or not auth_handler.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth_handler.create_access_token(
        data={"sub": user["email"]}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/admin/me", response_model=UserInDB)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Convert ObjectId to string for the response
    current_user["id"] = str(current_user["_id"])
    current_user["organization_id"] = str(current_user["organization_id"])
    return current_user
