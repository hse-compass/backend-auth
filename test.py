import unittest
from fastapi.testclient import TestClient
from app.main import app, get_db, User, create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://sarvar@localhost:5432/credentials_test"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = next(override_get_db())
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.session = TestingSessionLocal(bind=self.connection)

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    # def test_register(self):
    #     response = self.client.post("/register?email=test@example.com&password=testpassword")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn("access_token", response.json())

    def test_register_existing_user(self):
        self.client.post("/register?email=test@example.com&password=testpassword")
        response = self.client.post("/register?email=test@example.com&password=testpassword")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Email already registered")

    def test_login(self):
        self.client.post("/register?email=test@example.com&password=testpassword")
        response = self.client.post("/login?email=test@example.com&password=testpassword")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

    def test_login_invalid_password(self):
        self.client.post("/register?email=test@example.com&password=testpassword")
        response = self.client.post("/login?email=test@example.com&password=wrongpassword")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid email or password")

    def test_login_nonexistent_user(self):
        response = self.client.post("/login?email=nonexistent@example.com&password=testpassword")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid email or password")

if __name__ == "__main__":
    unittest.main()