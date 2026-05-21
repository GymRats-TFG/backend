from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import os
os.environ["HTTPX_HTTP2"] = "0"
from database import supabase
from routers.auth import get_current_user
from datetime import date
import httpx
import httpcore

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user = Depends(get_current_user)):
    user_id = current_user.id

    try:
        for attempt in range(2):
            try:
                profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
                break
            except (httpx.RemoteProtocolError, httpcore.RemoteProtocolError) as e:
                if "ConnectionTerminated" in str(e) and attempt == 0:
                    continue
                raise

        profile_data = profile_response.data[0] if profile_response.data else {}

        today = date.today()
        for attempt in range(2):
            try:
                subs_response = supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
                break
            except (httpx.RemoteProtocolError, httpcore.RemoteProtocolError) as e:
                if "ConnectionTerminated" in str(e) and attempt == 0:
                    continue
                raise
        
        if subs_response.data:
            for sub in subs_response.data:
                if sub.get("status") == "active":
                    exp_str = sub.get("expiration_date")
                    if exp_str:
                        exp_date = date.fromisoformat(exp_str[:10])
                        if exp_date <= today:
                            supabase.table("subscriptions").update({"status": "inactive"}).eq("id", sub["id"]).execute()

        return {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.user_metadata.get("username", ""),
            "name": profile_data.get("name"),
            "avatar_url": profile_data.get("avatar_url"),
            "description": profile_data.get("description"),
            "is_enterprise": current_user.user_metadata.get("is_enterprise", False)
        }

    except Exception as e:
        print(f"🚨 ERROR DETECTADO EN /me: {repr(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno al obtener el perfil: {str(e)}")

@router.patch("/profile")
async def update_user_profile(
    name: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user)
):
    user_id = current_user.id
    update_payload = {}

    if username is not None:
        check = supabase.table("profiles").select("id").eq("username", username).execute()
        if check.data and check.data[0]["id"] != user_id:
            raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso por otro usuario.")
        update_payload["username"] = username

    if name is not None:
        update_payload["name"] = name

    if avatar_file:
        if not avatar_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

        file_content = await avatar_file.read()
        file_name = f"{user_id}.png"
        bucket_name = "profile photos"
        file_options = {"content-type": avatar_file.content_type}

        try:
            supabase.storage.from_(bucket_name).upload(path=file_name, file=file_content, file_options=file_options)
        except Exception:
            supabase.storage.from_(bucket_name).update(path=file_name, file=file_content, file_options=file_options)

        avatar_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        update_payload["avatar_url"] = avatar_url

    if not update_payload:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar.")

    supabase.table("profiles").update(update_payload).eq("id", user_id).execute()
    updated_profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    return updated_profile.data