import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.main import app

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


def _make_token(db, email, username, password, role):
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    return create_access_token({"sub": user.id, "role": user.role.value})


@pytest.fixture
def admin_token():
    db = TestingSessionLocal()
    token = _make_token(db, "admin@test.com", "admin", "Admin123!", UserRole.ADMIN)
    db.close()
    return token


@pytest.fixture
def viewer_token():
    db = TestingSessionLocal()
    token = _make_token(db, "viewer@test.com", "viewer", "Viewer123!", UserRole.VIEWER)
    db.close()
    return token


@pytest.fixture
def sample_vehicle_id(client, admin_token):
    resp = client.post(
        "/api/vehicles/",
        json={"brand": "Toyota", "location": "Bogotá", "applicant": "Carlos", "year": 2020, "price": 45000000},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return resp.json()["id"]
