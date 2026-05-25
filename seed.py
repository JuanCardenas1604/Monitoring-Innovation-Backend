"""
Script de inicialización de datos.

Crea el usuario administrador por defecto y 10 vehículos de ejemplo
para que el evaluador pueda probar la aplicación inmediatamente.

Uso:
    python seed.py
"""

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle

VEHICLES_SEED = [
    {
        "brand": "Toyota",
        "location": "Bogotá",
        "applicant": "Carlos Méndez",
        "year": 2024,
        "price": 85000000,
        "description": "Toyota Corolla 2024, seminuevo, 15.000 km, garantía vigente.",
    },
    {
        "brand": "Mazda",
        "location": "Medellín",
        "applicant": "Ana López",
        "year": 2023,
        "price": 72000000,
        "description": "Mazda CX-30 2023, color gris, un solo dueño.",
    },
    {
        "brand": "Chevrolet",
        "location": "Cali",
        "applicant": "Pedro Ramírez",
        "year": 2022,
        "price": 55000000,
        "description": "Chevrolet Onix Turbo 2022, excelente estado mecánico.",
    },
    {
        "brand": "Renault",
        "location": "Barranquilla",
        "applicant": "María Gómez",
        "year": 2024,
        "price": 62000000,
        "description": "Renault Duster 2024, 4x4, ideal para carretera.",
    },
    {
        "brand": "Kia",
        "location": "Bogotá",
        "applicant": "Luis Torres",
        "year": 2023,
        "price": 48000000,
        "description": "Kia Rio 2023, hatchback, bajo consumo de combustible.",
    },
    {
        "brand": "Ford",
        "location": "Medellín",
        "applicant": "Diana Ruiz",
        "year": 2021,
        "price": 68000000,
        "description": "Ford Escape 2021, SUV, 30.000 km, servicio al día.",
    },
    {
        "brand": "Volkswagen",
        "location": "Cali",
        "applicant": "Jorge Castillo",
        "year": 2024,
        "price": 78000000,
        "description": "Volkswagen Taos 2024, tecnología de punta, 0 km.",
    },
    {
        "brand": "Hyundai",
        "location": "Bucaramanga",
        "applicant": "Sandra Díaz",
        "year": 2023,
        "price": 59000000,
        "description": "Hyundai Tucson 2023, versión full equipo, techo solar.",
    },
    {
        "brand": "Nissan",
        "location": "Bogotá",
        "applicant": "Andrés Herrera",
        "year": 2022,
        "price": 82000000,
        "description": "Nissan Qashqai 2022, e-Power, caja automática.",
    },
    {
        "brand": "Suzuki",
        "location": "Pereira",
        "applicant": "Laura Jiménez",
        "year": 2024,
        "price": 43000000,
        "description": "Suzuki Swift 2024, económico, ideal para ciudad.",
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin = User(
                email="admin@monitoringinnovation.com",
                username="admin",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print("[OK] Usuario admin creado (admin / admin123)")
        else:
            print("[SKIP] Usuario admin ya existe")

        existing_viewer = db.query(User).filter(User.username == "viewer").first()
        if not existing_viewer:
            viewer = User(
                email="viewer@monitoringinnovation.com",
                username="viewer",
                hashed_password=hash_password("viewer123"),
                role=UserRole.VIEWER,
            )
            db.add(viewer)
            print("[OK] Usuario viewer creado (viewer / viewer123)")
        else:
            print("[SKIP] Usuario viewer ya existe")

        existing_count = db.query(Vehicle).count()
        if existing_count == 0:
            for v in VEHICLES_SEED:
                db.add(Vehicle(**v))
            print(f"[OK] {len(VEHICLES_SEED)} vehiculos de ejemplo creados")
        else:
            print(f"[SKIP] {existing_count} vehiculos ya existen")

        db.commit()
        print("\nSeed completado exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"Error durante seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
