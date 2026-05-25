# Monitoring Innovation — Backend API

API REST para la gestión de vehículos de un concesionario. Desarrollada con **FastAPI**, **SQLAlchemy**, **JWT** y **bcrypt**.

---

## Stack

- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0
- **Autenticación:** JWT (python-jose) + bcrypt
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Roles:** Admin (CRUD completo) / Viewer (solo lectura)

---

## Requisitos

- Python 3.12+
- pip

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd backend

# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Poblar la base de datos con datos iniciales
python seed.py

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`.
Documentación Swagger: `http://localhost:8000/docs`.

---

## Seed data

Al ejecutar `python seed.py` se crean:

| Usuario  | Credenciales       | Rol   |
|----------|--------------------|-------|
| admin    | admin / admin123   | Admin |
| viewer   | viewer / viewer123 | Viewer |

Además se crean 10 vehículos de ejemplo con distintas marcas, localidades y precios.

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py                 # Punto de entrada
│   ├── core/
│   │   ├── config.py           # Configuración
│   │   ├── database.py         # Conexión a BD
│   │   └── security.py         # JWT + bcrypt
│   ├── models/
│   │   ├── user.py             # Modelo User
│   │   └── vehicle.py          # Modelo Vehicle
│   ├── schemas/
│   │   ├── user.py             # Pydantic (request/response)
│   │   └── vehicle.py
│   ├── api/
│   │   ├── deps.py             # Dependencias (auth, roles)
│   │   └── v1/
│   │       ├── auth.py         # /api/auth/register, login, me
│   │       ├── vehicles.py     # /api/vehicles/ CRUD + filtros
│   │       └── users.py        # /api/users/ gestión (admin)
│   └── middleware/
│       └── logging_middleware.py
├── logs/
│   └── app.log                 # Logs rotativos
├── seed.py                     # Población inicial
├── Procfile                    # Render
├── runtime.txt                 # Versión de Python
├── requirements.txt
└── .env.example
```

---

## Endpoints

### Autenticación

| Método | Ruta                    | Auth     | Descripción                        |
|--------|-------------------------|----------|------------------------------------|
| POST   | /api/auth/register      | ✗        | Registro público (rol viewer)      |
| POST   | /api/auth/register-admin| ✓ Admin  | Crear usuarios con rol específico  |
| POST   | /api/auth/login         | ✗        | Inicio de sesión                   |
| POST   | /api/auth/forgot-password | ✗        | Solicitar restablecimiento de contraseña |
| POST   | /api/auth/reset-password  | ✗        | Restablecer contraseña con token         |
| GET    | /api/auth/me              | ✓ Cualq. | Perfil del usuario autenticado           |

### Vehículos

| Método | Ruta                    | Auth      | Descripción                        |
|--------|-------------------------|-----------|------------------------------------|
| GET    | /api/vehicles/          | ✓ Cualq.  | Listar (con filtros y búsqueda)   |
| GET    | /api/vehicles/{id}      | ✓ Cualq.  | Detalle de un vehículo            |
| POST   | /api/vehicles/          | ✓ Admin   | Crear vehículo                    |
| PUT    | /api/vehicles/{id}      | ✓ Admin   | Actualizar vehículo               |
| DELETE | /api/vehicles/{id}      | ✓ Admin   | Eliminar vehículo                 |

**Filtros disponibles en GET /api/vehicles/:**
- `q` — Búsqueda global (marca, localidad, aspirante)
- `brand` — Filtrar por marca
- `location` — Filtrar por localidad
- `applicant` — Filtrar por aspirante
- `skip` — Paginación (offset)
- `limit` — Paginación (límite, máx. 500)

### Usuarios (solo admin)

| Método | Ruta                    | Auth    | Descripción                         |
|--------|-------------------------|---------|-------------------------------------|
| GET    | /api/users/             | ✓ Admin | Listar todos los usuarios           |
| GET    | /api/users/{id}         | ✓ Admin | Detalle de usuario                  |
| PUT    | /api/users/{id}/role    | ✓ Admin | Cambiar rol de un usuario           |
| DELETE | /api/users/{id}         | ✓ Admin | Eliminar un usuario                 |

---

## Licencia

Proyecto — Prueba técnica Monitoring Innovation.
