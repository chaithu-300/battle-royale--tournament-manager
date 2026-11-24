# functions.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Session,  declarative_base
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

DB_PATH = "battle-royale.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60

Base = declarative_base()



# 1. USERS TABLE

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="player", nullable=False)


# 2. SQUADS TABLE

class Squad(Base):
    __tablename__ = "Squads"

    squad_id = Column(Integer, primary_key=True, autoincrement=True)
    squad_name = Column(String, nullable=False)
    captain_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)


# 3. SQUAD MEMBERS TABLE

class SquadMember(Base):
    __tablename__ = "SquadMembers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    player_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    status = Column(String, default="active", nullable=False)


# 4. SQUAD INVITATIONS TABLE

class SquadInvitation(Base):
    __tablename__ = "SquadInvitations"

    invitation_id = Column(Integer, primary_key=True, autoincrement=True)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    invited_player_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.now)


# 5. TOURNAMENTS TABLE

class Tournament(Base):
    __tablename__ = "Tournaments"

    tournament_id = Column(Integer, primary_key=True, autoincrement=True)
    organizer_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    tournament_name = Column(String, nullable=False)
    description = Column(Text)
    map = Column(String, nullable=False)
    registration_start = Column(DateTime, nullable=False)
    registration_end = Column(DateTime, nullable=False)
    max_squads = Column(Integer, nullable=False)
    status = Column(String, default="draft", nullable=False)


# 6. TOURNAMENT REGISTRATIONS TABLE

class TournamentRegistration(Base):
    __tablename__ = "TournamentRegistrations"

    __table_args__ = (
        UniqueConstraint("tournament_id", "squad_id"),
    )

    registration_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("Tournaments.tournament_id"), nullable=False)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    registered_at = Column(DateTime, default=datetime.now)
    status = Column(String, default="active", nullable=False)


# 7. MATCHES TABLE

class Match(Base):
    __tablename__ = "Matches"

    __table_args__ = (
        UniqueConstraint("tournament_id", "match_number"),
    )

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("Tournaments.tournament_id"), nullable=False)
    match_number = Column(Integer, nullable=False)
    match_date = Column(DateTime, nullable=False)
    map = Column(String, nullable=False)


# 8. MATCH RESULTS TABLE

class MatchResult(Base):
    __tablename__ = "MatchResults"

    __table_args__ = (
        UniqueConstraint("match_id", "squad_id"),
    )

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("Matches.match_id"), nullable=False)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    placement = Column(Integer, nullable=False)
    kills = Column(Integer, nullable=False)
    placement_points = Column(Integer, nullable=False)
    total_points = Column(Integer, nullable=False)

Base.metadata.create_all(engine)


# -------- REGISTER --------

def register_user(username, email, password):
    session = Session(engine)

    existing = session.query(User).filter_by(email=email).first()
    if existing:
        session.close()
        return False

    user = User(username=username,email=email,password=ph.hash(password),role="player")

    session.add(user)
    session.commit()

    response = {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

    session.close()
    return response


# -------- LOGIN --------

def verify_login(email, password):
    session = Session(engine)
    user = session.query(User).filter_by(email=email).first()

    if user is None:
        session.close()
        return False

    try:
        ph.verify(user.password, password)

    except VerifyMismatchError:
        session.close()
        return False

    user_id = user.user_id
    username = user.username
    user_email = user.email
    role = user.role

    session.close()

    access_token = create_token(user_id, username, user_email, role, "access")
    refresh_token = create_token(user_id, username, user_email, role, "refresh")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


# -------- CREATE TOKEN --------

def create_token(user_id, username, email, role, token_type):
    time = ACCESS_TOKEN_EXPIRY

    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY

    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "token_type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=time)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# -------- VERIFY TOKEN --------

def verify_token(token, token_type):
   
    try:
        payload = jwt.decode(jwt=token,key=SECRET_KEY,algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return False
    if payload["token_type"]== token_type:
        return payload["user_id"]
    return False


# -------- REFRESH TOKEN --------

def refresh_access_token(token):

    try:
        payload=jwt.decode(jwt=token,key=SECRET_KEY,algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return False

    if payload["token_type"] != "refresh":
        return False

    access_token =create_token(payload["user_id"],payload["username"],payload["email"],payload["role"],"access")
    return {
        "access_token": access_token
    }