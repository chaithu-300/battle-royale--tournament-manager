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

class InvitePlayerData(BaseModel):
    squad_id: int
    invited_player_id: int

class InvitationResponseData(BaseModel):
    invitation_id: int
    response: str = Field(min_length=1)
# -------- 1. Register User --------

@app.post("/register")
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

@app.post("/login")
def login(data: LoginData):
    tokens = functions.verify_login(
        email=data.email,
        password=data.password
    )

    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return tokens


# -------- 3. Refresh Token --------

@app.post("/refresh")
def refresh(refresh_token: str = Header(None)):
    response = functions.refresh_access_token(refresh_token)

    if not response:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token."
        )

    return response

# 7) Get squads created or joined by the logged-in player

@app.get("/squads/me")
def get_my_squads(token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")
    user_id = functions.verify_token(token, "access")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    role = functions.get_user_role(user_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can access this endpoint")
    response = functions.get_player_squads(user_id)

    return {"squads": response}

# 8) Invite a player to a squad

@app.post("/squads/invite")
def invite_player(data: InvitePlayerData, token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")
    captain_id = functions.verify_token(token, "access")
    if not captain_id:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    role = functions.get_user_role(captain_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can invite squad members")

    response = functions.invite_player_to_squad(captain_id,data.squad_id,data.invited_player_id)
    if "error" in response:
        if response["error"] == "Squad not found" or response["error"] == "Player not found":
            raise HTTPException(status_code=404, detail=response["error"])
        raise HTTPException(status_code=400, detail=response["error"])

    return response

# 9) Player accepts or rejects a squad invitation

@app.post("/squads/invitations/respond")
def respond_to_invitation(data: InvitationResponseData, token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")
    player_id = functions.verify_token(token, "access")
    if not player_id:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    role = functions.get_user_role(player_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can respond to invitations")
    response = functions.respond_to_squad_invitation(player_id,data.invitation_id,data.response.lower())
    if "error" in response:
        if response["error"] == "Invitation not found" or response["error"] == "Squad not found":
            raise HTTPException(status_code=404, detail=response["error"])
        if response["error"] == "You are not allowed to respond to this invitation":
            raise HTTPException(status_code=403, detail=response["error"])
        raise HTTPException(status_code=400, detail=response["error"])

    return response