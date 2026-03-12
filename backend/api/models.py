from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime

# Users
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "contributor" # "admin" or "contributor"

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: str

class UserResponse(UserBase):
    id: str

# Projects
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectInDB(ProjectBase):
    id: str = Field(alias="_id")
    owner_id: str
    members: List[str] = [] # list of user IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectResponse(ProjectBase):
    id: str
    owner_id: str
    members: List[str]

# Assets (extension)
# Note: Assets are still tracked locally or in SQLite vector DB but now need project_id association
class AssetProjectAssociation(BaseModel):
    asset_id: str
    project_id: str
    owner_id: str
