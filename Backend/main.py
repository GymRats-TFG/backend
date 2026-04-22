from fastapi import FastAPI, HTTPException
from database import supabase
from schemas import UserSignup, UserLogin

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