from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import supabase
from schemas import UserSignup

router = APIRouter(tags=["Auth"])

# Para saber quién es el usuario que envía el Token
# de esta forma podemos controlar que no cualquier usuario
# pueda modificar un gimnasio, etc.

# botón de login en la interfaz de Swagger
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
    
@router.post("/signup")
async def signup(user: UserSignup):
    try:
        # Comprobamos que no exista ya un usuario con ese mismo username
        existing_user = supabase.table("profiles").select("id").eq("username", user.username).execute()
        if existing_user.data:
            raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso.")

        # Registramos un nuevo usuario en supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "username": user.username,
                    "is_enterprise": user.is_enterprise
                }
            }
        })

        # Verificamos que se haya creado correctamente
        if not auth_response.user:
            raise Exception("Error al crear el usuario en la autenticación.")
        
        user_id = auth_response.user.id

        # Insertamos el perfil en la tabla profiles
        profile_data = {
            "id": user_id,
            "username": user.username,
            "name": user.username,  # Por defecto usamos el username como nombre
            "role": "enterprise" if user.is_enterprise else "user",
            "avatar_url": "https://tqovlbwynuyysiopimiv.supabase.co/storage/v1/object/public/profile%20photos/default_profile_photo.png"
        }

        profile_response = supabase.table("profiles").insert(profile_data).execute()

        # Si algo falla en la tabla profiles
        if not profile_response.data:
            raise Exception("Usuario autenticado, pero falló la creación del perfil.")

        # Devolvemos mensaje de registro exitoso y el usuario
        return {
            "message": "Usuario y perfil creados correctamente", 
            "user": auth_response.user,
            "is_enterprise": user.is_enterprise
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Intentamos iniciar sesión en supabase con correo y contraseña
        response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })

        user = response.user
        
        # Devolvemos el token del usuario
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.user_metadata.get("username", ""),
                "is_enterprise": user.user_metadata.get("is_enterprise", False)
            }
        }
    except Exception as e:
        # Si las credenciales son incorrectas o el usuario no existe.
        raise HTTPException(status_code=401, detail="Correo o contraseña inválida")