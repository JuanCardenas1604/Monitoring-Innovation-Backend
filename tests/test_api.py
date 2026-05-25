import pytest
import uuid

from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal


def _create_user(email, username, password, role=UserRole.VIEWER):
    db = TestingSessionLocal()
    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    uid = user.id
    db.close()
    return uid


class TestHealth:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data
        assert "version" in data

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuth:
    def test_register(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "new@test.com", "username": "newuser", "password": "NewUser1!",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["username"] == "newuser"

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "dup@test.com", "username": "user1", "password": "Pass123!",
        })
        resp = client.post("/api/auth/register", json={
            "email": "dup@test.com", "username": "user2", "password": "Pass123!",
        })
        assert resp.status_code == 400

    def test_register_invalid_data(self, client):
        resp = client.post("/api/auth/register", json={"email": "bad", "username": "ab", "password": "123"})
        assert resp.status_code == 422

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@test.com", "username": "loginuser", "password": "Login123!",
        })
        resp = client.post("/api/auth/login", json={"username": "loginuser", "password": "Login123!"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "fail@test.com", "username": "failuser", "password": "Pass1!",
        })
        resp = client.post("/api/auth/login", json={"username": "failuser", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_forgot_password_nonexistent(self, client):
        resp = client.post("/api/auth/forgot-password", json={"email": "noone@test.com"})
        assert resp.status_code == 404

    def test_forgot_password_invalid_email(self, client):
        resp = client.post("/api/auth/forgot-password", json={"email": "invalid"})
        assert resp.status_code == 422


class TestVehicles:
    def test_create_vehicle_as_admin(self, client, admin_token):
        resp = client.post(
            "/api/vehicles/",
            json={"brand": "Mazda", "location": "Medellín", "applicant": "Ana"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["brand"] == "Mazda"
        assert data["location"] == "Medellín"
        assert data["applicant"] == "Ana"

    def test_create_vehicle_as_viewer_forbidden(self, client, viewer_token):
        resp = client.post(
            "/api/vehicles/",
            json={"brand": "Ford", "location": "Cali", "applicant": "Luis"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    def test_create_vehicle_unauthenticated(self, client):
        resp = client.post(
            "/api/vehicles/",
            json={"brand": "Ford", "location": "Cali", "applicant": "Luis"},
        )
        assert resp.status_code == 401

    def test_list_vehicles(self, client, admin_token):
        client.post("/api/vehicles/", json={"brand": "A", "location": "X", "applicant": "P"},
                     headers={"Authorization": f"Bearer {admin_token}"})
        client.post("/api/vehicles/", json={"brand": "B", "location": "Y", "applicant": "Q"},
                     headers={"Authorization": f"Bearer {admin_token}"})
        resp = client.get("/api/vehicles/",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_vehicles_pagination(self, client, admin_token):
        for i in range(5):
            client.post("/api/vehicles/", json={"brand": f"B{i}", "location": "X", "applicant": "P"},
                         headers={"Authorization": f"Bearer {admin_token}"})
        resp = client.get("/api/vehicles/?skip=0&limit=3",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3

    def test_get_single_vehicle(self, client, admin_token, sample_vehicle_id):
        resp = client.get(f"/api/vehicles/{sample_vehicle_id}",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == sample_vehicle_id

    def test_get_nonexistent_vehicle(self, client, admin_token):
        resp = client.get("/api/vehicles/nonexistent-id",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    def test_update_vehicle(self, client, admin_token, sample_vehicle_id):
        resp = client.put(
            f"/api/vehicles/{sample_vehicle_id}",
            json={"brand": "Toyota Updated", "price": 50000000},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["brand"] == "Toyota Updated"
        assert resp.json()["price"] == 50000000

    def test_update_vehicle_as_viewer_forbidden(self, client, viewer_token, sample_vehicle_id):
        resp = client.put(
            f"/api/vehicles/{sample_vehicle_id}",
            json={"brand": "Hacked"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    def test_delete_vehicle(self, client, admin_token, sample_vehicle_id):
        resp = client.delete(f"/api/vehicles/{sample_vehicle_id}",
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 204
        resp = client.get(f"/api/vehicles/{sample_vehicle_id}",
                          headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    def test_delete_vehicle_as_viewer_forbidden(self, client, viewer_token, sample_vehicle_id):
        resp = client.delete(f"/api/vehicles/{sample_vehicle_id}",
                              headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403


class TestUsers:
    def test_list_users_as_admin(self, client, admin_token):
        resp = client.get("/api/users/", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_users_as_viewer_forbidden(self, client, viewer_token):
        resp = client.get("/api/users/", headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403

    def test_update_role(self, client, admin_token):
        user_id = _create_user("target@test.com", "target", "Target1!")
        resp = client.put(
            f"/api/users/{user_id}/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_delete_user(self, client, admin_token):
        user_id = _create_user("delete@test.com", "delete", "Delete1!")
        resp = client.delete(f"/api/users/{user_id}",
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 204
        resp = client.get("/api/users/", headers={"Authorization": f"Bearer {admin_token}"})
        assert all(u["id"] != user_id for u in resp.json())

    def test_cannot_delete_self(self, client, admin_token):
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        my_id = resp.json()["id"]
        resp = client.delete(f"/api/users/{my_id}",
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400
