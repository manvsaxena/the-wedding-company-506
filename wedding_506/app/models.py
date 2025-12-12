from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    
class OrganizationCreate(OrganizationBase):
    password: str = Field(..., min_length=8)
    
class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class OrganizationInDB(OrganizationBase):
    id: str
    collection_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
class UserBase(BaseModel):
    email: EmailStr
    is_admin: bool = False
    organization_id: str
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
