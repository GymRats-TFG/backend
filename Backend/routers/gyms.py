from fastapi import APIRouter, Depends, HTTPException
from database import supabase
from routers.auth import get_current_user
from schemas import GymCreate, GymResponse

router = APIRouter(prefix="/gyms", tags=["Gyms"])

@router.post("/")
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
    
@router.get("/my", response_model=list[GymResponse])
async def get_my_gyms(current_user = Depends(get_current_user)):
    # Obtención de todas las sedes pertenecientes a la empresa
    gyms_res = supabase.table("gyms").select("*").eq("enterprise_id", current_user.id).execute()
    if not gyms_res.data:
        return []

    result = []
    for gym in gyms_res.data:
        # Obtención del aforo actual
        stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym["id"]).single().execute()
        current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0

        result.append(GymResponse(
            id=gym["id"],
            name=gym["name"],
            address=gym["address"],
            max_capacity=gym.get("max_capacity", 0),
            current_capacity=current_cap,
            image_url=gym.get("image_url"),
            is_open=gym.get("is_open", False)
        ))

    return result