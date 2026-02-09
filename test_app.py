from fastapi.testclient import TestClient
from app import app
from database import init_db, get_db
import os
import pytest

client = TestClient(app)

# Initialize DB for testing
init_db()

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_register_and_login():
    # Register
    email = "test@example.com"
    password = "password123"
    
    # Clean up first if exists (simple way for this script)
    # in real tests, use a fixture with a fresh DB
    
    response = client.post("/api/auth/register", json={"email": email, "password": password})
    # Might be 201 or 400 if already exists.
    assert response.status_code in [201, 400]

    # Login
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None
    return token

def test_create_and_read_post():
    token = test_register_and_login()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Post
    # We need a dummy image file
    with open("test_image.jpg", "wb") as f:
        f.write(b"dummy image content")
        
    with open("test_image.jpg", "rb") as f:
        response = client.post(
            "/api/posts",
            headers=headers,
            data={"content": "Hello World"},
            files={"image": ("test_image.jpg", f, "image/jpeg")}
        )
    assert response.status_code == 201
    post_id = response.json()["id"]
    
    # Read Posts
    response = client.get("/api/posts")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) > 0
    assert posts[0]["content"] == "Hello World"
    
    # Read Single Post
    response = client.get(f"/api/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["post"]["content"] == "Hello World"

    # Clean up
    os.remove("test_image.jpg")

if __name__ == "__main__":
    # Manually run tests if executed directly
    try:
        test_read_main()
        print("test_read_main passed")
        test_register_and_login()
        print("test_register_and_login passed")
        test_create_and_read_post()
        print("test_create_and_read_post passed")
        print("All tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
        exit(1)
