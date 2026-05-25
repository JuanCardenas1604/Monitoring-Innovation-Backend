import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserCreateAdmin, UserLogin, UserUpdateRole, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.models.user import UserRole


class TestUserSchemas:
    def test_user_create_valid(self):
        u = UserCreate(email="test@example.com", username="testuser", password="Secret1!")
        assert u.email == "test@example.com"
        assert u.username == "testuser"

    def test_user_create_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", username="user", password="pass123")

    def test_user_create_short_username(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", username="ab", password="pass123")

    def test_user_create_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", username="user", password="12345")

    def test_user_create_admin_default_role(self):
        u = UserCreateAdmin(email="a@b.com", username="admin", password="Secret1!")
        assert u.role == UserRole.VIEWER

    def test_user_create_admin_explicit_role(self):
        u = UserCreateAdmin(email="a@b.com", username="admin", password="Secret1!", role=UserRole.ADMIN)
        assert u.role == UserRole.ADMIN

    def test_user_login(self):
        u = UserLogin(username="user", password="pass")
        assert u.username == "user"

    def test_user_login_empty_username(self):
        u = UserLogin(username="", password="pass")
        assert u.username == ""

    def test_update_role_valid(self):
        r = UserUpdateRole(role=UserRole.ADMIN)
        assert r.role == UserRole.ADMIN

    def test_update_role_invalid(self):
        with pytest.raises(ValidationError):
            UserUpdateRole(role="superadmin")

    def test_forgot_password_valid(self):
        r = ForgotPasswordRequest(email="user@example.com")
        assert r.email == "user@example.com"

    def test_forgot_password_invalid(self):
        with pytest.raises(ValidationError):
            ForgotPasswordRequest(email="bad")

    def test_reset_password_valid(self):
        r = ResetPasswordRequest(token="abc123", password="NewPass1!")
        assert r.token == "abc123"

    def test_reset_password_short(self):
        with pytest.raises(ValidationError):
            ResetPasswordRequest(token="t", password="12345")


class TestVehicleSchemas:
    def test_vehicle_create_required_only(self):
        v = VehicleCreate(brand="Toyota", location="Bogotá", applicant="Juan")
        assert v.brand == "Toyota"
        assert v.year is None
        assert v.price is None
        assert v.description is None
        assert v.image_url is None

    def test_vehicle_create_all_fields(self):
        v = VehicleCreate(
            brand="Mazda", location="Medellín", applicant="Ana",
            year=2020, price=50000000, description="Buen estado", image_url="http://img.com/1.jpg"
        )
        assert v.year == 2020
        assert v.price == 50000000

    def test_vehicle_create_missing_brand(self):
        with pytest.raises(ValidationError):
            VehicleCreate(location="X", applicant="Y")

    def test_vehicle_update_partial(self):
        v = VehicleUpdate(price=30000000)
        assert v.price == 30000000
        assert v.brand is None

    def test_vehicle_update_empty(self):
        v = VehicleUpdate()
        assert v.brand is None
        assert v.location is None

    def test_vehicle_create_year_as_string_fails(self):
        with pytest.raises(ValidationError):
            VehicleCreate(brand="X", location="Y", applicant="Z", year="not-a-number")
