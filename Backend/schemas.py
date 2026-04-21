from pydantic import BaseModel, EmailStr
from typing import Optional

class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_enterprise: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str