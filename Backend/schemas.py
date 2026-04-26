from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

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

class UserLogin(BaseModel):
    email: EmailStr
    password: str