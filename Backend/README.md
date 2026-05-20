# ⚙️ GymRats - API REST Backend

Este directorio contiene el núcleo lógico de la aplicación **GymRats**, desarrollado con un enfoque en alto rendimiento y escalabilidad para la gestión de centros deportivos.

## 🛠️ Stack tecnológico

* **Lenguaje:** Python 3.10 o superior
* **Framework:** FastAPI - Framework moderno y asíncrono para la creación de APIs
* **Servidor ASGI:** Uvicorn - Servidor de alto rendimiento
* **Validación de datos:** Pydantic - Basado en Python Type Hints con validación avanzada
* **Base de datos y autenticación:** Supabase - Backend as a Service con PostgreSQL
* **Almacenamiento de archivos:** Supabase Storage - Para gestión de imágenes de perfil y gimnasios

## 📂 Estructura de archivos

* `main.py`: Punto de entrada que inicializa FastAPI y registra los routers
* `database.py`: Configuración del cliente de Supabase y gestión de la conexión
* `schemas.py`: Modelos Pydantic con validadores personalizados para contraseñas y correos
* `requirements.txt`: Lista completa de dependencias del proyecto
* `.env`: Variables de entorno con credenciales de Supabase (no compartir)
* `example.env`: Plantilla de configuración para variables de entorno
* `routers/`: Directorio con los módulos de rutas organizados por funcionalidad
  * `auth.py`: Endpoints de registro, login y validación de tokens JWT
  * `users.py`: Gestión de perfiles de usuario y actualización de datos
  * `gyms.py`: CRUD de gimnasios y gestión de socios
  * `subscriptions.py`: Administración de suscripciones y membresías

## 🔐 Sistema de seguridad y roles

La API implementa un flujo de seguridad robusto basado en OAuth2 con Bearer Tokens:

* **Validación de registro:** Las contraseñas deben cumplir con requisitos mínimos: al menos 8 caracteres, una letra y un número
* **Autenticación:** Gestión centralizada mediante Supabase Auth, que devuelve un JWT tras el login exitoso
* **Control de acceso:** Uso de la dependencia `get_current_user` para proteger rutas sensibles
* **Verificación de roles:** Los endpoints empresariales validan el campo `role` en la tabla `profiles` para restringir acceso a cuentas enterprise

## 🛰️ Endpoints principales

### Autenticación

* `POST /signup`: Registro de nuevos usuarios con validación de complejidad de contraseña y creación automática del perfil
* `POST /login`: Autenticación con email y contraseña, devuelve token de acceso y datos del usuario
* `GET /users/me`: Recuperación de información del usuario actual (requiere token válido)

### Gestión de usuarios

* `GET /users/me`: Obtiene el perfil completo del usuario autenticado, incluyendo foto, descripción y estado de suscripciones
* `PATCH /users/profile`: Actualiza datos del perfil (nombre, username, avatar) con soporte para subida de imágenes

### Gestión de gimnasios (solo enterprise)

* `POST /gyms`: Crea una nueva sede con imagen, datos de contacto y configuración de capacidad
* `GET /gyms/my`: Lista todos los gimnasios registrados por el usuario enterprise actual
* `GET /gyms/{gym_id}`: Obtiene detalles completos de una sede específica, incluyendo aforo actual
* `GET /gyms/{gym_id}/members`: Lista todos los socios activos vinculados a una sede
* `POST /gyms/members`: Vincula un usuario como socio a un gimnasio, usando user_id o username como identificador

### Gestión de suscripciones

* `PATCH /subscriptions/{subscription_id}`: Actualiza fechas o estado de una suscripción (solo enterprise)
* `DELETE /subscriptions/{subscription_id}`: Elimina una suscripción de la base de datos (solo enterprise)

## 🚀 Instalación y uso

### 1. Preparar el entorno virtual

Se recomienda usar un entorno virtual para aislar las dependencias:

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
.\venv\Scripts\activate

# Activar en macOS o Linux
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Se debe renombrar el archivo `example.env` a `.env` y completar con las credenciales del proyecto en Supabase:

* `SUPABASE_URL`: URL del proyecto en Supabase
* `SUPABASE_KEY`: Clave pública o privada según el entorno de uso

### 4. Ejecutar el servidor de desarrollo

```bash
uvicorn main:app --reload
```

El servidor se iniciará en `http://127.0.0.1:8000` con recarga automática de cambios en el código.

## 📖 Documentación automática e interactiva

FastAPI genera documentación interactiva de forma automática:

* **Swagger UI:** http://127.0.0.1:8000/docs - Interfaz completa para probar endpoints con autenticación
* **ReDoc:** http://127.0.0.1:8000/redoc - Documentación alternativa con vista de esquema

Para probar rutas protegidas en Swagger, se debe usar el botón "Authorize" e introducir el token obtenido en el endpoint `/login`.

## 🗄️ Esquema de base de datos

El proyecto utiliza las siguientes tablas en Supabase:

* `profiles`: Almacena información pública de usuarios (username, nombre, avatar, rol)
* `gyms`: Registro de sedes deportivas con datos de contacto, capacidad y estado
* `gym_stats`: Control de aforo en tiempo real para cada gimnasio
* `subscriptions`: Vinculación de usuarios a gimnasios con fechas de inicio y expiración

## 🧪 Consideraciones para pruebas

* Las imágenes se almacenan en buckets de Supabase Storage: `profile photos` y `gym images`
* Las fechas de expiración de suscripciones se validan automáticamente al consultar el perfil del usuario
* Los endpoints enterprise verifican el rol del usuario en cada petición para garantizar seguridad
* La API maneja conflictos de username duplicado y suscripciones activas previas

## 🔧 Despliegue en producción

Para desplegar en un entorno productivo:

* Desactivar el modo `--reload` de Uvicorn
* Usar un servidor ASGI con workers múltiples, por ejemplo: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`
* Configurar variables de entorno de forma segura, sin exponer el archivo `.env`
* Establecer políticas de acceso adecuadas en Supabase para tablas y storage
* Considerar el uso de un proxy inverso como Nginx para gestión de SSL y caché

## 🤝 Contribuciones

Para contribuir al desarrollo:

* Mantener la coherencia con los esquemas Pydantic definidos en `schemas.py`
* Añadir validaciones adicionales en los endpoints según los requisitos de negocio
* Documentar nuevos endpoints con descripciones claras en los decorators de FastAPI
* Probar los cambios en la interfaz Swagger antes de enviar una propuesta

## 📄 Licencia

Este proyecto forma parte del Trabajo de Fin de Grado del ciclo formativo correspondiente. Su uso está restringido a fines académicos y de demostración.
