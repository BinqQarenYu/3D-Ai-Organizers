from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..auth import Token, create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from ..database import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: str

@router.post("/register")
async def register(user: UserCreateRequest, db=Depends(get_db)):
    if await db.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    # Check if this is the first user; if so, make them admin
    is_first_user = await db.users.count_documents({}) == 0
    role = "admin" if is_first_user else "contributor"

    new_user = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "role": role
    }
    result = await db.users.insert_one(new_user)
    return {"id": str(result.inserted_id), "username": user.username, "role": role}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = await db.users.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "contributor"), "user_id": str(user["_id"])},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
