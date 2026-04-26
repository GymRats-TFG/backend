from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from database import supabase

# Para saber quién es el usuario que envía el Token
# de esta forma podemos controlar que no cualquier usuario
# pueda modificar un gimnasio, etc.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Pedimos a Supabase que nos de el usuario dueño de ese Token
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas.",
            )
        return user_response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al validar las credenciales.",
        )