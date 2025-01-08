from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from ..security.auth import authenticate_user, create_access_token, current_user
from ..data.models import UserRead, Token
from ..utils.config import Settings


ACCESS_TOKEN_EXPIRE_MINUTES = Settings.ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(tags=["Auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not (user := await authenticate_user(form_data.username, form_data.password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", 
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.uuid}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: UserRead = Depends(current_user)):
    return current_user


#  TODO: Add logout endpoint

# TODO: Add refresh token endpoint

# TODO: Add password reset endpoint

# TODO: Add registration endpoint
