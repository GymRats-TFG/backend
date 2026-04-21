# ⚙️ GymRats - API REST Backend

Este directorio contiene el núcleo lógico de la aplicación **GymRats**, desarrollado con un enfoque en alto rendimiento y escalabilidad.

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Framework:** FastAPI - Framework moderno y asíncrono para Python.
* **Servidor ASGI:** Uvicorn - Servidor de alto rendimiento (para pruebas en local).
* **Validación de Datos:** Pydantic - Basado en Python Type Hints.
* **BBDD / Auth:** Supabase - Backend as a Service (PostgreSQL).

## 📂 Estructura de Archivos

* `main.py`: Punto de entrada que inicializa FastAPI y define las rutas base.
* `database.py`: Gestión de la sesión y conexión con el cliente de Supabase.
* `schemas.py`: Modelos Pydantic que garantizan la integridad de los datos de entrada/salida.
* `example.env`: Plantilla de configuración de variables de entorno.

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
pip install fastapi uvicorn supabase pydantic python-dotenv
```

### 3. Variables de Entorno

Renombra `example.env` a `.env` e introduce tus credenciales de proyecto de Supabase.

### 4. Ejecución del Servidor

```bash
uvicorn main:app --reload
```

## 📖 Documentación Automática

Una vez encendido el servidor, puedes acceder a:

* **Swagger UI:** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

---

## ✅ Siguiente paso recomendado

Ahora que tienes el entorno listo, el siguiente paso es implementar `database.py` para gestionar la conexión con Supabase.
