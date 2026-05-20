from fastapi import APIRouter, Depends, HTTPException
from database import supabase
from routers.auth import get_current_user
from schemas import SubscriptionUpdate
from datetime import date

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.patch("/{subscription_id}")
async def update_subscription(subscription_id: str, data: SubscriptionUpdate, current_user = Depends(get_current_user)):
    # Verificamos si es enterprise usando la columna 'role'
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Permiso denegado. Se requiere cuenta de empresa.")

    # Preparamos datos para actualizar
    update_fields = data.model_dump(exclude_none=True)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")
    
    # Si se envía una nueva expiration_date y es hoy o anterior, forzamos el estado a "inactive"
    if data.expiration_date is not None:
        if data.expiration_date.date() <= date.today():
            update_fields["status"] = "inactive" 

    # Convertimos fechas al formato correcto usando 'expiration_date'
    if "start_date" in update_fields:
        update_fields["start_date"] = update_fields["start_date"].isoformat()
    if "expiration_date" in update_fields:
        update_fields["expiration_date"] = update_fields["expiration_date"].isoformat()

    # Ejecutamos la actualización
    supabase.table("subscriptions").update(update_fields).eq("id", subscription_id).execute()
    
    return {"message": "Suscripción actualizada correctamente"}

@router.delete("/{subscription_id}")
async def delete_subscription(subscription_id: str, current_user = Depends(get_current_user)):
    # Verificamos si el usuario actual es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Permiso denegado. Se requiere cuenta de empresa.")

    # Verificamos que la suscripción exista antes de intentar eliminarla
    sub_check = supabase.table("subscriptions").select("id").eq("id", subscription_id).single().execute()
    if not sub_check.data:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada.")

    # Eliminamos la suscripción
    supabase.table("subscriptions").delete().eq("id", subscription_id).execute()
    
    # Respuesta de éxito
    return {"message": "Suscripción eliminada correctamente"}