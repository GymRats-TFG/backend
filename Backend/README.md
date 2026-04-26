# ⚙️ GymRats - API REST Backend

Este directorio contiene el núcleo lógico de la aplicación **GymRats**, desarrollado con un enfoque en alto rendimiento y escalabilidad para la gestión de centros deportivos.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) - Framework moderno y asíncrono.
* **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/) - Servidor de alto rendimiento.
* **Validación de Datos:** [Pydantic](https://docs.pydantic.dev/) - Basado en Python Type Hints con validación avanzada.
* **BBDD / Auth:** [Supabase](https://supabase.com/) - Backend as a Service (PostgreSQL).

## 📂 Estructura de Archivos

* `main.py`: Punto de entrada que inicializa FastAPI y define las rutas base.
* `auth.py`: Sistema de seguridad y dependencia para inyección de usuarios mediante tokens JWT.
* `database.py`: Gestión de la sesión y conexión con el cliente de Supabase.
* `schemas.py`: Modelos Pydantic con validadores personalizados (Regex para contraseñas y EmailStr).
* `requirements.txt`: Lista de dependencias para el despliegue (incluye `email-validator`).
* `example.env`: Plantilla de configuración de variables de entorno.

## 🔐 Sistema de Seguridad y Roles

La API implementa un flujo de seguridad robusto basado en **OAuth2 con Bearer Tokens**:

1. **Validación de Registro:** Las contraseñas deben tener un mínimo de 8 caracteres, incluyendo al menos una letra y un número.
2. **Autenticación:** Gestión centralizada mediante Supabase Auth, devolviendo un JWT en el login.
3. **Control de Acceso:** Uso de la dependencia `get_current_user` para proteger rutas.
4. **Verificación de Roles:** Los endpoints sensibles (como la creación de gimnasios) verifican el campo `is_enterprise` dentro de la metadata del token del usuario.

## 🛰️ Endpoints Principales

### Autenticación & Perfil
* `POST /signup`: Registro de usuarios con validación de complejidad de contraseña.
* `POST /login`: Autenticación y obtención del token de acceso.
* `GET /users/me`: Recuperación de la información del usuario actual (protegido).

### Gestión de Gimnasios (Enterprise)
* `POST /gyms`: **(Protegido - Solo Empresas)** Registro de nuevas sedes. Al crear un gimnasio, el sistema inicializa automáticamente su registro en la tabla de estadísticas de aforo (`gym_stats`) con capacidad actual 0.

## 🚀 Instalación y Uso

### 1. Preparar el Entorno Virtual

Para mantener las dependencias aisladas y el sistema limpio:

```bash
# Crear entorno
python -m venv venv

# Activar en Windows
.\venv\Scripts\activate

# Activar en Mac/Linux
source venv/bin/activate
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Variables de Entorno

Renombra `example.env` a `.env` e introduce tus credenciales de proyecto de Supabase.

### 4. Ejecución del Servidor

```bash
uvicorn main:app --reload
```

## 📖 Documentación Automática e Interactiva

Una vez encendido el servidor, puedes acceder a:

* **Swagger UI (Recomendado):** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

*Nota: Para probar rutas protegidas en Swagger, usa el botón Authorize e introduce el token obtenido en el login.*