from fastapi import FastAPI, HTTPException, Depends
from database import supabase
from schemas import UserSignup, UserLogin, GymCreate
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
        # Registramos un nuevo usuario en supabase
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "username": user.username,
                    "is_enterprise": user.is_enterprise
                }
            }
        })

        # Devolvemos mensaje de registro exitoso y el usuario
        return {"message": "User created successfully", "user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(user: UserLogin):
    try:
        # Intentamos iniciar sesión en supabase con correo y contraseña
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        
        # Devolvemos el token del usuario
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": response.user
        }
    except Exception as e:
        # Si las credenciales son incorrectas o el usuario no existe.
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
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
        # Preparamos los datos para la tabla gyms
        # Extraemos max_capacity porque va a la tabla gym_stats, no a gyms
        gym_dict = gym.model_dump()
        max_cap = gym_dict.pop("max_capacity")
        
        # Vinculamos el gym a la cuenta empresa
        gym_dict["owner_id"] = current_user.id

        # Insertamos en Supabase
        response = supabase.table("gyms").insert(gym_dict).execute()
        
        if response.data:
            new_gym_id = response.data[0]["id"]
            
            # Inicializamos las estadísticas de aforo (tabla gym_stats)
            supabase.table("gym_stats").insert({
                "gym_id": new_gym_id,
                "max_capacity": max_cap,
                "current_capacity": 0
            }).execute()

        return {"message": "Gimnasio registrado", "gym": response.data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")