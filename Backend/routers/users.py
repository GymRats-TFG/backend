from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
from database import supabase
from routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_my_profile(current_user = Depends(get_current_user)):
    user_id = current_user.id

    # Recopilamos toda la información del usuario, como foto de perfil, etc.
    response = supabase.table("profiles").select("*").eq("id",user_id).execute()
    profile_data = response.data[0] if response.data else {}

    # Devolvemos toda la información
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.user_metadata.get("username", ""),
        "name": profile_data.get("name"),
        "avatar_url": profile_data.get("avatar_url"),
        "description": profile_data.get("description"),
        "is_enterprise": current_user.user_metadata.get("is_enterprise", False)
    }

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
        # Si existe en BD y NO pertenece al usuario actual
        if check.data and check.data[0]["id"] != user_id:
            raise HTTPException(status_code=409, detail="El nombre de usuario ya está en uso por otro usuario.")
        update_payload["username"] = username

    if name is not None:
        update_payload["name"] = name

    # Procesar y subir imagen
    if avatar_file:
        if not avatar_file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

        file_content = await avatar_file.read()
        file_name = f"{user_id}.png"
        bucket_name = "profile photos"
        
        file_options = {"content-type": avatar_file.content_type}

        try:
            # Intentamos subir la imagen como si fuera nueva
            supabase.storage.from_(bucket_name).upload(
                path=file_name,
                file=file_content,
                file_options=file_options
            )
        except Exception:
            # Si falla, asumimos que ya existe y la sobrescribimos (update)
            supabase.storage.from_(bucket_name).update(
                path=file_name,
                file=file_content,
                file_options=file_options
            )

        # Obtener la URL pública tras asegurar que la imagen está en el bucket
        avatar_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        update_payload["avatar_url"] = avatar_url

    # Validamos que hay algo para actualizar
    if not update_payload:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar.")

    # Actualizamos el usuario
    supabase.table("profiles").update(update_payload).eq("id", user_id).execute()

    # Devolvemos el perfil actualizado
    updated_profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    return updated_profile.data