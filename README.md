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
├── railway.toml                # Railway (deploy + seed)
├── Procfile                    # Railway / Render
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

## Despliegue en Railway

Guía para desplegar el backend con **PostgreSQL** persistente (recomendado en producción).

### Requisitos previos

- Cuenta en [Railway](https://railway.app)
- Repositorio en GitHub (solo la carpeta `backend` o el monorepo con root en `backend`)
- [Railway CLI](https://docs.railway.app/develop/cli) (opcional, para ejecutar `seed` manualmente)

### Paso 1 — Subir el código a GitHub

```bash
cd backend
git init   # si aún no es un repo
git add .
git commit -m "Backend listo para Railway"
git remote add origin <url-de-tu-repo>
git push -u origin main
```

No subas `.env` ni `*.db` (ya están en `.gitignore`).

### Paso 2 — Crear proyecto en Railway

1. Entra a [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
2. Elige tu repositorio.
3. Si el repo es un monorepo, en el servicio del backend: **Settings** → **Root Directory** → `backend`.

### Paso 3 — Añadir PostgreSQL

1. En el mismo proyecto: **+ New** → **Database** → **PostgreSQL**.
2. Espera a que el plugin esté activo.
3. En el servicio **backend** → **Variables** → **Add Reference**:
   - Variable: `DATABASE_URL`
   - Referencia: `${{Postgres.DATABASE_URL}}`

Railway inyecta una URL `postgres://...`; la app la convierte automáticamente a `postgresql+psycopg://` (driver PostgreSQL incluido en `requirements.txt`).

### Paso 4 — Variables de entorno del backend

En el servicio backend → **Variables**, configura:

| Variable | Valor | Notas |
|----------|--------|--------|
| `SECRET_KEY` | Cadena larga aleatoria | **Obligatorio** en producción |
| `DEBUG` | `false` | Oculta `/docs` en producción |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Referencia al plugin Postgres |
| `FRONTEND_URL` | `https://tu-frontend.vercel.app` | URL real del frontend |
| `CORS_ORIGINS` | Misma URL del frontend | Separar varias con coma |
| `SMTP_HOST` | `smtp.gmail.com` | Opcional |
| `SMTP_PORT` | `587` | |
| `SMTP_USERNAME` | tu@gmail.com | |
| `SMTP_PASSWORD` | contraseña de aplicación (16 chars) | Sin espacios |
| `SMTP_FROM_EMAIL` | tu@gmail.com | |
| `SMTP_FROM_NAME` | `Monitoring` | |

Generar `SECRET_KEY` en local:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Paso 5 — Deploy

1. Railway detecta `railway.toml` y `Procfile`.
2. En cada deploy ejecuta `python seed.py` (`preDeployCommand`) — crea `admin`/`viewer` y vehículos de ejemplo si la BD está vacía.
3. Al arrancar, `create_all` crea las tablas si no existen.

Credenciales iniciales (tras el primer deploy con seed):

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Admin |
| viewer | viewer123 | Viewer |

**Cambia estas contraseñas** antes de exponer la API públicamente.

### Paso 6 — Dominio público

1. Servicio backend → **Settings** → **Networking** → **Generate Domain**.
2. Obtendrás una URL tipo `https://backend-production-xxxx.up.railway.app`.
3. Usa esa URL en el frontend como `VITE_API_URL` (o equivalente).
4. Actualiza `FRONTEND_URL` y `CORS_ORIGINS` con la URL real del frontend.

### Paso 7 — Verificar

```bash
curl https://TU-DOMINIO-RAILWAY.up.railway.app/health
# {"status":"ok"}

curl -X POST https://TU-DOMINIO/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Seed manual (si hace falta)

```bash
railway link
railway run python seed.py
```

### Desarrollo local vs Railway

| | Local | Railway |
|---|--------|---------|
| BD | SQLite (`monitoring_innovation.db`) | PostgreSQL (plugin) |
| `SECRET_KEY` | Opcional si `DEBUG=true` | Obligatorio |
| Datos | Tu `.db` local | Nuevo Postgres; seed en deploy |
| Correos | SMTP en `.env` o consola | Variables SMTP en Railway |

### Archivos de despliegue

- `railway.toml` — comando de inicio y `seed` antes de cada deploy
- `Procfile` — respaldo para el proceso web
- `nixpacks.toml` — build con Python 3.12
- `runtime.txt` — versión de Python

---

## Licencia

Proyecto — Prueba técnica Monitoring Innovation.
