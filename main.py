from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import functions
from pydantic import BaseModel, Field


app = FastAPI()


# -------- CORS --------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------- Pydantic Models --------

class RegisterData(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginData(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


# -------- 1. Register User --------

@app.post("/auth/register")
def register(data: RegisterData):
    response = functions.register_user(
        username=data.username,
        email=data.email,
        password=data.password
    )

    if not response:
        raise HTTPException(status_code=409, detail="Email already exists")

    return {"message": "User registered successfully"}


# -------- 2. Login --------

@app.post("/auth/login")
def login(data: LoginData):
    tokens = functions.verify_login(
        email=data.email,
        password=data.password
    )

    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return tokens


# -------- 3. Refresh Token --------

@app.post("/auth/refresh")
def refresh(refresh_token: str = Header(None)):
    response = functions.refresh_access_token(refresh_token)

    if not response:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token."
        )

    return response