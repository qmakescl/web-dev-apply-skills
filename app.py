from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, RedirectResponse
from contextlib import asynccontextmanager
from database import init_db, get_db
from pydantic import BaseModel, EmailStr
from auth import verify_password, get_password_hash, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from typing import Optional, List
import sqlite3
import os
import shutil
import uuid

# --- Models ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr

# --- Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    cursor = db.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    os.makedirs("uploads", exist_ok=True)
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# --- Auth Routes ---
@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    try:
        db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (user.email, hashed_password)
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return {"message": "User created successfully"}

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: sqlite3.Row = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"]}

# --- Post Models ---
class PostBase(BaseModel):
    content: str
    
class PostResponse(PostBase):
    id: int
    user_id: int
    user_email: str
    img_path: str
    created_at: str
    like_count: int
    comment_count: int
    is_liked: bool = False

class CommentCreate(BaseModel):
    comment: str

class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    user_email: str
    comment: str
    created_at: str

# --- Posts Routes ---
@app.post("/api/posts", status_code=status.HTTP_201_CREATED)
async def create_post(
    content: str = Form(...),
    image: UploadFile = File(...),
    current_user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    # Save Image
    file_extension = os.path.splitext(image.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join("uploads", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    db_img_path = f"/uploads/{filename}"
    
    cursor = db.execute(
        "INSERT INTO posts (user_id, img_path, content) VALUES (?, ?, ?)",
        (current_user["id"], db_img_path, content)
    )
    db.commit()
    return {"message": "Post created successfully", "id": cursor.lastrowid}

@app.get("/api/posts")
async def read_posts(
    current_user_email: Optional[str] = None, # Optional: For is_liked check if needed later, or use dependency optionally
    db: sqlite3.Connection = Depends(get_db)
):
    # Try to get current user if token provided (for is_liked)
    user_id = None
    # (Simplified: logic to extract user_id from token manually if needed, or separate endpoint for auth users)
    # For now, public feed.
    
    query = """
        SELECT p.*, u.email as user_email, 
        (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count,
        (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
    """
    cursor = db.execute(query)
    posts = [dict(row) for row in cursor.fetchall()]
    return posts

@app.get("/api/posts/{post_id}")
async def read_post(post_id: int, db: sqlite3.Connection = Depends(get_db)):
    query = """
        SELECT p.*, u.email as user_email,
        (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as like_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
    """
    cursor = db.execute(query, (post_id,))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get comments
    comments_cursor = db.execute("""
        SELECT c.*, u.email as user_email 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.post_id = ? 
        ORDER BY c.created_at ASC
    """, (post_id,))
    comments = [dict(row) for row in comments_cursor.fetchall()]
    
    return {"post": dict(post), "comments": comments}

@app.put("/api/posts/{post_id}")
async def update_post(
    post_id: int, 
    post_data: PostBase,
    current_user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
        
    db.execute("UPDATE posts SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (post_data.content, post_id))
    db.commit()
    return {"message": "Post updated successfully"}

@app.delete("/api/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    # Optional: Delete image file
    # if os.path.exists(post["img_path"].lstrip("/")):
    #    os.remove(post["img_path"].lstrip("/"))

    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    return {"message": "Post deleted successfully"}

@app.post("/api/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    try:
        db.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, current_user["id"]))
        db.commit()
        return {"messsage": "Liked", "liked": True}
    except sqlite3.IntegrityError:
        # Already liked, so unlike
        db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", (post_id, current_user["id"]))
        db.commit()
        return {"message": "Unliked", "liked": False}

@app.post("/api/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: sqlite3.Row = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    db.execute(
        "INSERT INTO comments (post_id, user_id, comment) VALUES (?, ?, ?)",
        (post_id, current_user["id"], comment_data.comment)
    )
    db.commit()
    return {"message": "Comment added successfully"}

# --- Page Routes ---
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
