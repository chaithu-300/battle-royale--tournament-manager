from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
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

class CreateAdmin(BaseModel):
    username: str
    email: str
    password: str


class RegisterData(BaseModel):
    username: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginData(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)

class CreateOrganizer(BaseModel):
    username: str
    email: str
    password: str


class CreateTournament(BaseModel):
    tournament_name: str
    description: str
    map_name: str
    registration_start: datetime
    registration_end: datetime
    max_squads: int


class UpdateTournament(BaseModel):
    tournament_name: str = None
    description: str = None
    map_name: str = None
    registration_start: datetime = None
    registration_end: datetime = None
    max_squads: int = None
    status: str = None


class CreateSquad(BaseModel):
    squad_name: str


class InvitePlayerData(BaseModel):
    squad_id: int
    invited_player_id: int

class InvitationResponseData(BaseModel):
    invitation_id: int
    response: str = Field(min_length=1)

class UpdateSquad(BaseModel):
    squad_name: str


class RegisterSquad(BaseModel):
    squad_id: int


class ScheduleMatch(BaseModel):
    match_number: int
    match_date: datetime
    map_name: str


class SubmitMatchResult(BaseModel):
    squad_id: int
    placement: int
    kills: int



@app.get("/")
def home():
    return {"message": "BGMI Tournament Manager API is running"}


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


# E1 – Create organizer

@app.post("/admin/organizers")
def add_organizer(data: CreateOrganizer, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = functions.get_user_role(user_id)
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create organizers")

    result = functions.create_organizer(
        data.username,
        data.email,
        data.password
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Email already exists")

    return result


# E2 – Create tournament

@app.post("/tournaments")
def add_tournament(data: CreateTournament, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = functions.get_user_role(user_id)
    if role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can create tournaments")

    result = functions.create_tournament(
        user_id,
        data.tournament_name,
        data.description,
        data.map_name,
        data.registration_start,
        data.registration_end,
        data.max_squads
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Invalid tournament details")

    return result


# E3 – Get all available tournaments
@app.get("/tournaments")
def all_tournaments():

    result = functions.get_tournaments()

    return result

# E4 - Get tournament by ID
@app.get("/tournaments/{tournament_id}")
def tournament_details(tournament_id: int):

    result = functions.get_tournament_by_id(tournament_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return result


# E5 – Update tournament

@app.patch("/tournaments/{tournament_id}")
def edit_tournament(tournament_id: int, data: UpdateTournament, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = functions.get_user_role(user_id)
    if role != "organizer":
        raise HTTPException(status_code=403, detail="Only organizers can update tournaments")

    result = functions.update_tournament(
        tournament_id,
        user_id,
        data.tournament_name,
        data.description,
        data.map_name,
        data.registration_start,
        data.registration_end,
        data.max_squads,
        data.status
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Tournament could not be updated")

    return result


# E6 – Create squad

@app.post("/squads")
def add_squad(data: CreateSquad, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = functions.get_user_role(user_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only players can create squads")

    result = functions.create_squad(
        user_id,
        data.squad_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Invalid squad name")

    return result

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

# E10 - Update squad details

@app.patch("/squads/{squad_id}")
def update_squad_details(data: UpdateSquad, squad_id: int, token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")
    user_id = functions.verify_token(token, "access")

    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    role = functions.get_user_role(user_id)

    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can access this endpoint")

    result = functions.update_squad(squad_id, user_id, data.squad_name)

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to update squad")

    return {"message": "Squad updated successfully"}

# E11 - Register squad for tournament

@app.post("/tournaments/{tournament_id}/register")
def register_tournament_squad(tournament_id: int, data: RegisterSquad, token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    role = functions.get_user_role(user_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can register squads")

    result = functions.register_squad(tournament_id, data.squad_id, user_id)
    if result is False:
        raise HTTPException(status_code=400, detail="Unable to register squad")

    return result

# E12 - Withdraw squad from tournament

@app.delete("/tournaments/{tournament_id}/squads/{squad_id}")
def withdraw_tournament_squad(tournament_id: int, squad_id: int, token: str = Header(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    role = functions.get_user_role(user_id)
    if role != "player":
        raise HTTPException(status_code=403, detail="Only Players can withdraw squads")

    result = functions.withdraw_squad(tournament_id, squad_id, user_id)
    if result is False:
        raise HTTPException(status_code=400, detail="Unable to withdraw squad")

    return result

# E13 - Schedule tournament match


@app.post("/tournaments/{tournament_id}/matches")
def create_tournament_match(tournament_id: int, data: ScheduleMatch, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    role = functions.get_user_role(user_id)
    if role != "organizer":
        raise HTTPException(status_code=403, detail="Only Organizers can schedule matches")

    result = functions.schedule_match(
        tournament_id,
        user_id,
        data.match_number,
        data.match_date,
        data.map_name
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to schedule match")

    return result

# E14 - Submit match results


@app.post("/matches/{match_id}/results")
def create_match_result(match_id: int, data: SubmitMatchResult, token: str = Header(None)):

    if not token:
        raise HTTPException(status_code=401, detail="Access token is required")

    user_id = functions.verify_token(token, "access")
    if user_id is False:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

    role = functions.get_user_role(user_id)
    if role != "organizer":
        raise HTTPException(status_code=403, detail="Only Organizers can submit match results")

    result = functions.submit_match_result(
        match_id,
        user_id,
        data.squad_id,
        data.placement,
        data.kills
    )

    if result is False:
        raise HTTPException(status_code=400, detail="Unable to submit match result")

    return result

# E15 - Get tournament leaderboard

@app.get("/tournaments/{tournament_id}/leaderboard")
def tournament_leaderboard(tournament_id: int):

    result = functions.get_tournament_leaderboard(tournament_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Tournament not found")

    return result


@app.post("/setup/create-admin")
def create_admin(data: CreateAdmin):

    result = functions.create_first_admin(
        data.username,
        data.email,
        data.password
    )

    if result is False:
        raise HTTPException(
            status_code=400,
            detail="Admin already exists or email is already registered"
        )

    return {"message": "First admin account created successfully"}