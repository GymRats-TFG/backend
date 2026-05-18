from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class UserSignup(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_enterprise: bool = False

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe de tener al menos 8 caracteres.')
        
        # Comprueba si hay al menos una letra (mayúscula o minúscula)
        if not any(char.isalpha() for char in v):
            raise ValueError('La contraseña debe contener al menos una letra.')
        
        # Comprueba si hay al menos un dígito
        if not any(char.isdigit() for char in v):
            raise ValueError('La contraseña debe contener al menos un número.')
            
        return v

class GymCreate(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    phone: str
    email: EmailStr
    price: float
    max_capacity: int
    image_url: str = None

class GymResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    phone: str
    email: EmailStr
    price: float
    max_capacity: int
    current_capacity: int
    image_url: str = None
    is_open: bool

class MemberLinkRequest(BaseModel):
    user_id: str
    gym_id: str
    start_date: datetime
    expiration_date: datetime

class MemberInfoResponse(BaseModel):
    id: str
    username: str
    name: Optional[str] = None
    email: str
    avatar_url: Optional[str] = None
    subscription_id: str
    is_active: bool

class SubscriptionUpdate(BaseModel):
    start_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_active: Optional[bool] = None