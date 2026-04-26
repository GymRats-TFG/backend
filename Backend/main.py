from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import supabase
from schemas import UserSignup, GymCreate
from auth import get_current_user

app = FastAPI(title="GymRats API")

@app.get("/")
def read_root():
    return {"message": "GymRats API is running 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "0.0.1"}

@app.post("/signup")
async def signup(user: UserSignup):
    try:
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
            "role": "enterprise" if user.is_enterprise else "user"
        }

        profile_response = supabase.table("profiles").insert(profile_data).execute()

        # Si algo falla en la tabla profiles
        if not profile_response.data:
            raise Exception("Usuario autenticado, pero falló la creación del perfil.")

        # Devolvemos mensaje de registro exitoso y el usuario
        return {
            "message": "Usuario y perfil creados correctamente", 
            "user": auth_response.user
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()): # Usamos el estándar de formulario para que funcione en SwaggerUI
    try:
        # Intentamos iniciar sesión en supabase con correo y contraseña
        response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        # Devolvemos el token del usuario
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": response.user
        }
    except Exception as e:
        # Si las credenciales son incorrectas o el usuario no existe.
        raise HTTPException(status_code=401, detail="Correo o contraseña inválida")
    
@app.get("/users/me")
async def get_my_profile(current_user = Depends(get_current_user)):
    # Aquí current_user ya tiene toda la info de la DB
    return {
        "id": current_user.id,
        "email": current_user.email,
        "metadata": current_user.user_metadata # el resto de datos del usuario, como el username, is_enterprise, etc.
    }

@app.post("/gyms")
async def create_gym(gym: GymCreate, current_user = Depends(get_current_user)):
    # Verificamos si es empresa
    user_metadata = current_user.user_metadata
    if not user_metadata.get("is_enterprise"):
        raise HTTPException(
            status_code=403, 
            detail="Solo las empresas pueden registrar gimnasios."
        )
    try:
        # Convertimos el esquema a diccionario
        gym_dict = gym.model_dump()
        
        # Vinculamos el gym a la cuenta empresa
        gym_dict["enterprise_id"] = current_user.id
        # Forzamos que el gym nazca cerrado por defecto
        gym_dict["is_open"] = False

        # Insertamos en Supabase
        response = supabase.table("gyms").insert(gym_dict).execute()

        if not response.data:
            raise Exception("No se pudieron insertar los datos en la tabla gyms.")
        
        # Obtener el ID del gimnasio
        new_gym_id = response.data[0]["id"]

        # Inicializamos las estadísticas del aforo
        supabase.table("gym_stats").insert({
            "gym_id": new_gym_id,
            "current_capacity": 0
        }).execute()

        return {"message": "Gimnasio registrado", "gym": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")