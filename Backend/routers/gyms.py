from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from pydantic import EmailStr
from typing import Optional
from database import supabase
from routers.auth import get_current_user
from schemas import GymResponse, MemberLinkRequest, MemberInfoResponse, ScanRequest
from datetime import date

router = APIRouter(prefix="/gyms", tags=["Gyms"])

@router.post("/", status_code=201)
async def create_gym(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    address: str = Form(...),
    phone: str = Form(...),
    email: EmailStr = Form(...),
    price: float = Form(...),
    max_capacity: int = Form(...),
    image_file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Verificar que el usuario es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden registrar sedes.")

    # Subir imagen a Supabase Storage
    bucket_name = "gym images"
    file_ext = image_file.filename.split(".")[-1] if "." in image_file.filename else "jpg"
    safe_filename = f"{current_user.id}_{name.replace(' ', '_')}.{file_ext}"
    
    file_content = await image_file.read()
    file_options = {"content-type": image_file.content_type}

    try:
        # Intentamos subir como archivo nuevo
        supabase.storage.from_(bucket_name).upload(
            path=safe_filename,
            file=file_content,
            file_options=file_options
        )
    except Exception:
        # Si falla (ya existe), lo sobrescribimos
        supabase.storage.from_(bucket_name).update(
            path=safe_filename,
            file=file_content,
            file_options=file_options
        )

    image_url = supabase.storage.from_(bucket_name).get_public_url(safe_filename)

    # Preparamos datos para la base de datos (SIN latitud/longitud)
    gym_dict = {
        "name": name,
        "description": description,
        "address": address,
        "phone": phone,
        "email": email,
        "price": price,
        "max_capacity": max_capacity,
        "image_url": image_url,
        "enterprise_id": current_user.id,
        "is_open": False
    }

    # Insertamos en la tabla gyms
    gym_res = supabase.table("gyms").insert(gym_dict).execute()
    if not gym_res.data:
        raise HTTPException(status_code=500, detail="Error al registrar la sede en la base de datos.")

    new_gym_id = gym_res.data[0]["id"]

    # Inicializamos estadísticas de aforo
    supabase.table("gym_stats").insert({
        "gym_id": new_gym_id,
        "current_capacity": 0
    }).execute()

    return {"message": "Sede creada correctamente", "gym": gym_res.data[0]}

@router.get("/my", response_model=list[GymResponse])
async def get_my_gyms(current_user = Depends(get_current_user)):
    gyms_res = supabase.table("gyms").select("*").eq("enterprise_id", current_user.id).execute()
    if not gyms_res.data:
        return []

    result = []
    for gym in gyms_res.data:
        stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym["id"]).single().execute()
        current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0

        result.append(GymResponse(
            id=gym["id"],
            name=gym["name"],
            description=gym.get("description"),
            address=gym.get("address", "Dirección no disponible"),
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
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).single().execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada.")

    stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym_id).single().execute()
    current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0

    gym_data = gym_res.data
    
    return GymResponse(
        id=gym_data["id"],
        name=gym_data["name"],
        description=gym_data.get("description"),
        address=gym_data.get("address", "Dirección no disponible"),
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

    # Obtenemos las suscripciones para esta sede
    subs_res = supabase.table("subscriptions").select("*").eq("gym_id", gym_id).execute()
    if not subs_res.data:
        return []

    members = []
    for sub in subs_res.data:
        user_res = supabase.table("profiles").select("*").eq("id", sub["user_id"]).single().execute()
        if user_res.data:
            user_data = user_res.data
            members.append(MemberInfoResponse(
                id=user_data["id"],
                username=user_data["username"],
                name=user_data.get("name"),
                avatar_url=user_data.get("avatar_url"),
                subscription_id=sub["id"],
                status=sub.get("status", "active"),
                start_date=sub.get("start_date"),
                expiration_date=sub.get("expiration_date")
            ))
    
    return members

@router.post("/members", status_code=201)
async def add_member_to_gym(data: MemberLinkRequest, current_user = Depends(get_current_user)):
    # Verificamos que el solicitante es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).execute()
    if not profile.data or profile.data[0].get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden gestionar socios.")

    # Validamos que se proporcionó al menos un identificador
    if not data.user_id and not data.username:
        raise HTTPException(status_code=400, detail="Debes proporcionar 'user_id' o 'username'.")

    target_user_id = data.user_id

    # Resolvemos el ID del usuario objetivo (SIN .single())
    if data.username:
        user_res = supabase.table("profiles").select("id").eq("username", data.username).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail=f"No se encontró ningún usuario con el nombre '{data.username}'.")
        target_user_id = user_res.data[0]["id"]
    else:
        user_res = supabase.table("profiles").select("id").eq("id", data.user_id).execute()
        if not user_res.data:
            # 🔍 DEBUG: Si llega aquí, el ID no está en la tabla 'profiles'
            raise HTTPException(status_code=404, detail=f"El ID '{data.user_id}' no existe en la tabla de perfiles.")
        target_user_id = user_res.data[0]["id"]

    # Validamos que el usuario objetivo NO es enterprise
    target_profile = supabase.table("profiles").select("role").eq("id", target_user_id).execute()
    if not target_profile.data or target_profile.data[0].get("role") == "enterprise":
        raise HTTPException(status_code=400, detail="No se pueden suscribir cuentas de tipo enterprise a un gimnasio.")

    # Validamos que no es auto-suscripción
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes suscribirte a ti mismo desde la cuenta de empresa.")

    # Evitamos suscripciones duplicadas activas
    existing = supabase.table("subscriptions").select("id").eq("user_id", target_user_id).eq("gym_id", data.gym_id).eq("status", "active").execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="El usuario ya tiene una suscripción activa en este gimnasio.")

    # Creamos la suscripción
    subscription_data = {
        "user_id": target_user_id,
        "gym_id": data.gym_id,
        "start_date": data.start_date.isoformat(),
        "expiration_date": data.expiration_date.isoformat(),
        "status": "active"
    }

    sub_res = supabase.table("subscriptions").insert(subscription_data).execute()
    if not sub_res.data:
        raise HTTPException(status_code=500, detail="Error al vincular el socio.")

    return {"message": "Socio vinculado correctamente", "subscription": sub_res.data[0]}

@router.patch("/{gym_id}")
async def update_gym(
    gym_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[EmailStr] = Form(None),
    price: Optional[float] = Form(None),
    max_capacity: Optional[int] = Form(None),
    image_file: Optional[UploadFile] = File(None),
    current_user = Depends(get_current_user)
):
    # Verificar que el usuario es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden editar sedes.")

    # Verificar que el gimnasio existe y pertenece a esta empresa
    gym_check = supabase.table("gyms").select("*").eq("id", gym_id).eq("enterprise_id", current_user.id).single().execute()
    if not gym_check.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada o no tienes permisos para editarla.")

    update_fields = {}

    # Recopilar solo los campos que se han enviado
    if name is not None: update_fields["name"] = name
    if description is not None: update_fields["description"] = description
    if address is not None: update_fields["address"] = address
    if phone is not None: update_fields["phone"] = phone
    if email is not None: update_fields["email"] = email
    if price is not None: update_fields["price"] = price
    if max_capacity is not None: update_fields["max_capacity"] = max_capacity

    # Manejar imagen si se proporciona
    bucket_name = "gym images"
    if image_file:
        file_ext = image_file.filename.split(".")[-1] if "." in image_file.filename else "jpg"

        safe_filename = f"{gym_id}.{file_ext}"
        
        file_content = await image_file.read()
        file_options = {"content-type": image_file.content_type}

        try:
            supabase.storage.from_(bucket_name).upload(path=safe_filename, file=file_content, file_options=file_options)
        except Exception:
            supabase.storage.from_(bucket_name).update(path=safe_filename, file=file_content, file_options=file_options)

        update_fields["image_url"] = supabase.storage.from_(bucket_name).get_public_url(safe_filename)

    # Validar que haya al menos un campo para actualizar
    if not update_fields:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar.")

    # Ejecutar actualización en Supabase
    supabase.table("gyms").update(update_fields).eq("id", gym_id).execute()

    # Devolver datos actualizados
    updated_gym_res = supabase.table("gyms").select("*").eq("id", gym_id).single().execute()
    return {"message": "Sede actualizada correctamente", "gym": updated_gym_res.data}

@router.get("/stats/summary")
async def get_enterprise_stats_summary(current_user = Depends(get_current_user)):
    # Verificamos que el usuario es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden consultar estadísticas.")

    # Obtenemos los IDs de todas las sedes de esta empresa
    gyms_res = supabase.table("gyms").select("id").eq("enterprise_id", current_user.id).execute()
    gym_ids = [g["id"] for g in (gyms_res.data or [])]

    if not gym_ids:
        return {"total_gyms": 0, "active_subscribers": 0, "total_current_capacity": 0}

    # Contamos suscripciones activas en esas sedes
    subs_res = supabase.table("subscriptions")\
        .select("id")\
        .eq("status", "active")\
        .in_("gym_id", gym_ids)\
        .execute()
    active_subscribers = len(subs_res.data)

    # Sumamos el aforo actual de todas las sedes
    stats_res = supabase.table("gym_stats")\
        .select("current_capacity")\
        .in_("gym_id", gym_ids)\
        .execute()
    total_current_capacity = sum(s.get("current_capacity", 0) for s in (stats_res.data or []))

    # Devolvemos el resumen
    return {
        "total_gyms": len(gym_ids),
        "active_subscribers": active_subscribers,
        "total_current_capacity": total_current_capacity
    }

@router.patch("/{gym_id}/toggle-open")
async def toggle_gym_open_status(gym_id: str, current_user = Depends(get_current_user)):
    # Verificar que el usuario es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Solo cuentas enterprise pueden cambiar el estado de una sede.")

    # Verificar que el gimnasio existe y pertenece a esta empresa
    gym_res = supabase.table("gyms").select("is_open").eq("id", gym_id).eq("enterprise_id", current_user.id).single().execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada o no tienes permisos para gestionarla.")

    # Invertir el estado actual
    current_status = gym_res.data.get("is_open", False)
    new_status = not current_status

    # Actualizar en la base de datos
    supabase.table("gyms").update({"is_open": new_status}).eq("id", gym_id).execute()

    # Devolver respuesta clara para la app
    return {
        "message": "Estado de la sede actualizado correctamente",
        "is_open": new_status
    }

@router.post("/{gym_id}/scan")
async def process_scan(gym_id: str, data: ScanRequest, current_user = Depends(get_current_user)):
    # Verificar que la cuenta es enterprise
    profile = supabase.table("profiles").select("role").eq("id", current_user.id).single().execute()
    if not profile.data or profile.data.get("role") != "enterprise":
        raise HTTPException(status_code=403, detail="Permiso denegado.")

    # Verificar que la sede existe y pertenece a esta empresa
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).eq("enterprise_id", current_user.id).single().execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Sede no encontrada o no tienes permisos.")
    gym = gym_res.data

    # Verificar que el usuario escaneado existe
    user_res = supabase.table("profiles").select("id, name, username").eq("id", data.user_id).single().execute()
    if not user_res.data:
        return {"success": False, "action": None, "message": "Usuario no registrado en la plataforma."}
    user_name = user_res.data.get("name") or user_res.data.get("username")

    # Obtener la última acción de este usuario en este gimnasio
    last_log = supabase.table("access_logs")\
        .select("action_type")\
        .eq("user_id", data.user_id)\
        .eq("gym_id", gym_id)\
        .order("recorded_at", desc=True)\
        .limit(1)\
        .execute()
    
    last_action = last_log.data[0]["action_type"] if last_log.data else None

    # Determinar siguiente acción: si la última fue 'entry' → toca 'exit', sino → 'entry'
    next_action = "exit" if last_action == "entry" else "entry"

    # Lógica según la acción
    if next_action == "entry":
        if not gym.get("is_open", False):
            return {"success": False, "action": "entry", "message": "El gimnasio está cerrado actualmente."}

        # Validar suscripción activa
        sub_res = supabase.table("subscriptions").select("*").eq("user_id", data.user_id).eq("gym_id", gym_id).eq("status", "active").single().execute()
        if not sub_res.data:
            return {"success": False, "action": "entry", "message": "No tiene suscripción activa en esta sede."}

        # Validar fecha de caducidad
        exp_str = sub_res.data.get("expiration_date")
        if exp_str and date.fromisoformat(exp_str) < date.today():
            supabase.table("subscriptions").update({"status": "expired"}).eq("id", sub_res.data["id"]).execute()
            return {"success": False, "action": "entry", "message": "Suscripción caducada."}

        # Validar aforo
        stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym_id).single().execute()
        stats = stats_res.data or {}
        current_cap = stats.get("current_capacity", 0)

        # Registrar entrada y aumentar aforo
        supabase.table("access_logs").insert({"user_id": data.user_id, "gym_id": gym_id, "action_type": "entry"}).execute()
        supabase.table("gym_stats").update({"current_capacity": current_cap + 1}).eq("gym_id", gym_id).execute()

        return {"success": True, "action": "entry", "message": "Entrada registrada", "user_name": user_name}

    else:  # next_action == "exit"
        # Registrar salida y disminuir aforo (nunca por debajo de 0)
        stats_res = supabase.table("gym_stats").select("current_capacity").eq("gym_id", gym_id).single().execute()
        current_cap = stats_res.data.get("current_capacity", 0) if stats_res.data else 0
        new_cap = max(0, current_cap - 1)

        supabase.table("gym_stats").update({"current_capacity": new_cap}).eq("gym_id", gym_id).execute()
        supabase.table("access_logs").insert({"user_id": data.user_id, "gym_id": gym_id, "action_type": "exit"}).execute()

        return {"success": True, "action": "exit", "message": "Salida registrada", "user_name": user_name}