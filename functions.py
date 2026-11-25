from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Session, declarative_base
from datetime import datetime, timedelta, timezone
import jwt  # pyright: ignore[reportMissingImports]
from argon2 import PasswordHasher   # pyright: ignore[reportMissingImports]
from argon2.exceptions import VerifyMismatchError   # pyright: ignore[reportMissingImports]

ACCESS_TOKEN_EXPIRY = 15  # minutes
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60  # minutes

SECRET_KEY = "SECRET123"
ALGORITHM = "HS256"


# DATABASE CONNECTION

DB_URL = "sqlite:///./battle-royale.db"
engine = create_engine(DB_URL)
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
    registration_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("Tournaments.tournament_id"), nullable=False)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    registered_at = Column(DateTime, default=datetime.now)
    status = Column(String, default="active", nullable=False)

# 7. MATCHES TABLE

class Match(Base):
    __tablename__ = "Matches"
    match_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey("Tournaments.tournament_id"), nullable=False)
    match_number = Column(Integer, nullable=False)
    match_date = Column(DateTime, nullable=False)
    map = Column(String, nullable=False)

# 8. MATCH RESULTS TABLE

class MatchResult(Base):
    __tablename__ = "MatchResults"
    result_id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("Matches.match_id"), nullable=False)
    squad_id = Column(Integer, ForeignKey("Squads.squad_id"), nullable=False)
    placement = Column(Integer, nullable=False)
    kills = Column(Integer, nullable=False)
    placement_points = Column(Integer, nullable=False)
    total_points = Column(Integer, nullable=False)

Base.metadata.create_all(engine)


# E1 – Create organizer
def create_organizer(username, email, password):
    session = Session(engine)

    user_exists = session.query(User).filter_by(email=email).first()

    if user_exists is not None:
        session.close()
        return False

    new_user = User(
        username=username,
        email=email,
        hashed_password=ph.hash(password),
        role="organizer"
    )

    session.add(new_user)
    session.commit()

    response = {
        "user_id": new_user.user_id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role
    }

    session.close()
    return response


# E2 – Create tournament
def create_tournament(user_id, tournament_name, description, map_name,
                      registration_start, registration_end, max_squads):

    session = Session(engine)

    if registration_start >= registration_end:
        session.close()
        return False

    if max_squads < 1:
        session.close()
        return False

    new_tournament = Tournament(
        organizer_id=user_id,
        tournament_name=tournament_name,
        description=description,
        map=map_name,
        registration_start=registration_start,
        registration_end=registration_end,
        max_squads=max_squads,
        status="draft"
    )

    session.add(new_tournament)
    session.commit()

    response = {
        "tournament_id": new_tournament.tournament_id,
        "tournament_name": new_tournament.tournament_name,
        "description": new_tournament.description,
        "map": new_tournament.map,
        "registration_start": new_tournament.registration_start,
        "registration_end": new_tournament.registration_end,
        "max_squads": new_tournament.max_squads,
        "status": new_tournament.status
    }

    session.close()
    return response


# E3 – Get all available tournaments
def get_tournaments():
    session = Session(engine)

    current_time = datetime.now()

    tournaments = session.query(Tournament).filter(
        Tournament.status == "registration_open",
        Tournament.registration_start <= current_time,
        Tournament.registration_end >= current_time
    ).all()

    response = []

    for tournament in tournaments:
        response.append({
            "tournament_id": tournament.tournament_id,
            "tournament_name": tournament.tournament_name,
            "description": tournament.description,
            "map": tournament.map,
            "registration_start": tournament.registration_start,
            "registration_end": tournament.registration_end,
            "max_squads": tournament.max_squads,
            "status": tournament.status
        })

    session.close()
    return response


# E4 – Get tournament by ID
def get_tournament_by_id(tournament_id):
    session = Session(engine)

    tournament = session.query(Tournament).filter_by(
        tournament_id=tournament_id
    ).first()

    if tournament is None:
        session.close()
        return False

    registered_squads = session.query(TournamentRegistration).filter_by(
        tournament_id=tournament_id,
        status="active"
    ).count()

    response = {
        "tournament_id": tournament.tournament_id,
        "organizer_id": tournament.organizer_id,
        "tournament_name": tournament.tournament_name,
        "description": tournament.description,
        "map": tournament.map,
        "registration_start": tournament.registration_start,
        "registration_end": tournament.registration_end,
        "max_squads": tournament.max_squads,
        "status": tournament.status,
        "registered_squads": registered_squads
    }

    session.close()
    return response


# 