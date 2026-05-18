from fastapi import APIRouter, Depends, HTTPException
import asyncio
from database import supabase
from routers.auth import get_current_user
from schemas import GymCreate, GymResponse, MemberLinkRequest, MemberInfoResponse
from utils.geocoding import forward_geocode, reverse_geocode

router = APIRouter(prefix="/gyms", tags=["Gyms"])

@router.post("/", status_code=201)
async def create_gym(gym: GymCreate, current_user = Depends(get_current_user)):
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden registrar sedes.")

    lat, lon = await forward_geocode(gym.street, gym.number, gym.city, gym.country)

    gym_dict = gym.model_dump(exclude={"street", "number", "city", "country"})
    gym_dict["latitude"] = lat
    gym_dict["longitude"] = lon
    gym_dict["enterprise_id"] = current_user.id
    gym_dict["is_open"] = False

    gym_res = supabase.table("gyms").insert(gym_dict).execute()
    if not gym_res.data:
        raise HTTPException(status_code=500, detail="Error al registrar la sede.")

    new_gym_id = gym_res.data[0]["id"]
    supabase.table("gym_stats").insert({
        "gym_id": new_gym_id,
        "current_capacity": 0,
        "max_capacity": gym.max_capacity
    }).execute()

    return {"message": "Sede creada correctamente", "gym": gym_res.data[0]}

@router.get("/my", response_model=list[GymResponse])
async def get_my_gyms(current_user = Depends(get_current_user)):
    gyms_res = supabase.table("gyms").select("*").eq("enterprise_id", current_user.id).execute()
    if not gyms_res.data:
        return []

    tasks = [reverse_geocode(g["latitude"], g["longitude"]) for g in gyms_res.data]
    addresses = await asyncio.gather(*tasks)

    result = []
    for i, gym in enumerate(gyms_res.data):
        stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym["id"]).single().execute()
        current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0

        result.append(GymResponse(
            id=gym["id"],
            name=gym["name"],
            description=gym.get("description"),
            address=addresses[i],
            latitude=gym["latitude"],
            longitude=gym["longitude"],
            phone=gym["phone"],
            email=gym["email"],
            price=gym["price"],
            max_capacity=gym.get("max_capacity", 0),
            current_capacity=current_cap,
            image_url=gym.get("image_url"),
            is_open=gym.get("is_open", False)
        ))
    return result

@router.get("/{gym_id}", response_model=GymResponse)
async def get_gym(gym_id: str, current_user = Depends(get_current_user)):
    # Obtenemos ñps datos del gimnasio
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).single().execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada.")

    # Obtenemos las estadísticas de aforo
    stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym_id).single().execute()
    current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0

    gym_data = gym_res.data
    
    return GymResponse(
        id=gym_data["id"],
        name=gym_data["name"],
        description=gym_data.get("description"),
        latitude=gym_data["latitude"],
        longitude=gym_data["longitude"],
        phone=gym_data["phone"],
        email=gym_data["email"],
        price=gym_data["price"],
        max_capacity=gym_data.get("max_capacity", 0),
        current_capacity=current_cap,
        image_url=gym_data.get("image_url"),
        is_open=gym_data.get("is_open", False)
    )

@router.get("/{gym_id}/members")
async def get_gym_members(gym_id: str, current_user = Depends(get_current_user)):
    # Verificamos que la sede existe
    gym_check = supabase.table("gyms").select("id").eq("id", gym_id).single().execute()
    if not gym_check.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada.")

    # Obtenemos las suscripciones activas para esta sede
    subs_res = supabase.table("subscriptions").select("*").eq("gym_id", gym_id).execute()
    if not subs_res.data:
        return []

    members = []
    for sub in subs_res.data:
        # Obtenemos el perfil del usuario
        user_res = supabase.table("profiles").select("*").eq("id", sub["user_id"]).single().execute()
        if user_res.data:
            user_data = user_res.data
            members.append(MemberInfoResponse(
                id=user_data["id"],
                username=user_data["username"],
                name=user_data.get("name"),
                email=user_data.get("email", ""),
                avatar_url=user_data.get("avatar_url"),
                subscription_id=sub["id"],
                is_active=sub.get("is_active", False)
            ))
    
    return members

@router.post("/members", status_code=201)
async def add_member_to_gym(data: MemberLinkRequest, current_user = Depends(get_current_user)):
    # Se verifica si el usuario actual es enterprise
    profile = supabase.table("profiles").select("is_enterprise").eq("id", current_user.id).single().execute()
    if not profile.data or not profile.data.get("is_enterprise"):
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden gestionar socios.")

    # Creamos la suscripción
    subscription_data = {
        "user_id": data.user_id,
        "gym_id": data.gym_id,
        "start_date": data.start_date.isoformat(),
        "expiration_date": data.expiration_date.isoformat(),
        "is_active": True
    }

    sub_res = supabase.table("subscriptions").insert(subscription_data).execute()
    if not sub_res.data:
        raise HTTPException(status_code=500, detail="Error al vincular el socio.")

    return {"message": "Socio vinculado correctamente", "subscription": sub_res.data[0]}