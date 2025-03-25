import os
import sys
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.dependencies import get_db
from app.main import app

# test DB
os.makedirs("./test_data", exist_ok=True)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_data/test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test data
test_user = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "1234567890",
    "is_barber": False,
}

test_barber = {
    "email": "barber@example.com",
    "username": "barberuser",
    "password": "barber123",
    "first_name": "Barber",
    "last_name": "Test",
    "phone_number": "9876543210",
    "is_barber": True,
}


class BaseTestCase(unittest.TestCase):
    """Base test case with setup and teardown"""

    def setUp(self):
        """Set up test database and client before each test"""
        # Create tables
        Base.metadata.create_all(bind=engine)

        # Override the get_db dependency
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        # Create test client
        self.client = TestClient(app)

        # Set up user tokens
        self.user_token = None
        self.barber_token = None

    def tearDown(self):
        """Clean up after each test"""
        # Drop all tables
        Base.metadata.drop_all(bind=engine)

        engine.dispose()

        # Remove the test database file
        if os.path.exists("./test.db"):
            os.remove("./test.db")

        # Clear dependency overrides
        app.dependency_overrides = {}

    def create_user_and_get_token(self, user_data):
        """Helper method to create a user and get an authentication token"""
        # Create the user
        response = self.client.post("/api/users/", json=user_data)
        self.assertEqual(response.status_code, 201)

        # Login and get token
        login_data = {"email": user_data["email"], "password": user_data["password"]}
        response = self.client.post("/api/auth/login/email", json=login_data)
        self.assertEqual(response.status_code, 200)

        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


class HealthCheckTestCase(BaseTestCase):
    """Tests for the health check endpoint"""

    def test_health_check(self):
        """Test that health check endpoint returns success"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        self.assertIn("barbershop-user-service", response.json()["service"])


class UserTestCase(BaseTestCase):
    """Tests for user-related endpoints"""

    def test_create_user(self):
        """Test creating a new user"""
        response = self.client.post("/api/users/", json=test_user)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["email"], test_user["email"])
        self.assertEqual(data["username"], test_user["username"])
        self.assertNotIn("password", data)
        self.assertEqual(data["is_barber"], test_user["is_barber"])

    def test_create_duplicate_user(self):
        """Test that creating a duplicate user fails"""
        # Create first user
        response = self.client.post("/api/users/", json=test_user)
        self.assertEqual(response.status_code, 201)

        # Try to create another user with the same email
        duplicate_user = test_user.copy()
        duplicate_user["username"] = "different"
        response = self.client.post("/api/users/", json=duplicate_user)
        self.assertEqual(response.status_code, 400)
        self.assertIn("already registered", response.json()["detail"].lower())

    def test_get_users_unauthorized(self):
        """Test that unauthorized users can't access user list"""
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 401)

    def test_get_users(self):
        """Test retrieving the list of users"""
        # Create a user and get token
        token = self.create_user_and_get_token(test_user)

        # Get users list
        response = self.client.get("/api/users/", headers=token)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["email"], test_user["email"])

    def test_get_current_user(self):
        """Test getting the current user info"""
        # Create a user and get token
        token = self.create_user_and_get_token(test_user)

        # Get current user
        response = self.client.get("/api/users/me", headers=token)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["email"], test_user["email"])
        self.assertEqual(data["username"], test_user["username"])

    def test_update_user(self):
        """Test updating a user"""
        # Create a user and get token
        token = self.create_user_and_get_token(test_user)

        # Get user ID
        response = self.client.get("/api/users/me", headers=token)
        user_id = response.json()["id"]

        # Update user
        update_data = {"first_name": "UpdatedFirst", "last_name": "UpdatedLast"}
        response = self.client.put(
            f"/api/users/{user_id}", json=update_data, headers=token
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["first_name"], update_data["first_name"])
        self.assertEqual(data["last_name"], update_data["last_name"])
        self.assertEqual(
            data["email"], test_user["email"]
        )  # Unchanged fields remain the same

    def test_user_cant_update_other_user(self):
        """Test that a regular user can't update another user"""
        # Create user and barber with tokens
        user_token = self.create_user_and_get_token(test_user)
        barber_token = self.create_user_and_get_token(test_barber)

        # Get barber's ID
        response = self.client.get("/api/users/me", headers=barber_token)
        barber_id = response.json()["id"]

        # Try to update barber as regular user
        update_data = {"first_name": "Hacked"}
        response = self.client.put(
            f"/api/users/{barber_id}", json=update_data, headers=user_token
        )
        self.assertEqual(response.status_code, 403)

    def test_barber_can_update_user(self):
        """Test that a barber can update another user"""
        # Create user and barber with tokens
        user_token = self.create_user_and_get_token(test_user)
        barber_token = self.create_user_and_get_token(test_barber)

        # Get user's ID
        response = self.client.get("/api/users/me", headers=user_token)
        user_id = response.json()["id"]

        # Update user as barber
        update_data = {"first_name": "UpdatedByBarber"}
        response = self.client.put(
            f"/api/users/{user_id}", json=update_data, headers=barber_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], update_data["first_name"])

    def test_get_barbers(self):
        """Test getting all barbers"""
        # Create both a user and a barber
        self.client.post("/api/users/", json=test_user)
        self.client.post("/api/users/", json=test_barber)

        # Get all barbers
        response = self.client.get("/api/users/barbers/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)

        # Should only contain barbers
        barbers = [u for u in data if u["is_barber"]]
        non_barbers = [u for u in data if not u["is_barber"]]
        self.assertGreater(len(barbers), 0)
        self.assertEqual(len(non_barbers), 0)

        # Verify barber data
        found_test_barber = False
        for barber in barbers:
            if barber["email"] == test_barber["email"]:
                found_test_barber = True
                break

        self.assertTrue(found_test_barber)

    def test_delete_user_unauthorized(self):
        """Test that a regular user can't delete users"""
        # Create a user and get token
        token = self.create_user_and_get_token(test_user)

        # Get user ID
        response = self.client.get("/api/users/me", headers=token)
        user_id = response.json()["id"]

        # Try to delete self as regular user
        response = self.client.delete(f"/api/users/{user_id}", headers=token)
        self.assertEqual(response.status_code, 403)

    def test_barber_can_delete_user(self):
        """Test that a barber can delete users"""
        # Create user and barber with tokens
        user_token = self.create_user_and_get_token(test_user)
        barber_token = self.create_user_and_get_token(test_barber)

        # Get user's ID
        response = self.client.get("/api/users/me", headers=user_token)
        user_id = response.json()["id"]

        # Delete user as barber
        response = self.client.delete(f"/api/users/{user_id}", headers=barber_token)
        self.assertEqual(response.status_code, 204)

        # Verify user is deleted
        response = self.client.get(f"/api/users/{user_id}", headers=barber_token)
        self.assertEqual(response.status_code, 404)


class AuthTestCase(BaseTestCase):
    """Tests for authentication endpoints"""

    def test_login_with_email(self):
        """Test login with email endpoint"""
        # Create a user first
        self.client.post("/api/users/", json=test_user)

        # Try to login
        login_data = {"email": test_user["email"], "password": test_user["password"]}
        response = self.client.post("/api/auth/login/email", json=login_data)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_login_oauth(self):
        """Test login with OAuth2 password flow"""
        # Create a user first
        self.client.post("/api/users/", json=test_user)

        # Try to login with OAuth2 password flow
        response = self.client.post(
            "/api/auth/login",
            data={"username": test_user["email"], "password": test_user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create a user first
        self.client.post("/api/users/", json=test_user)

        # Try to login with wrong password
        login_data = {"email": test_user["email"], "password": "wrongpassword"}
        response = self.client.post("/api/auth/login/email", json=login_data)
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
