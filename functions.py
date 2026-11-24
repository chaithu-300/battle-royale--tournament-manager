
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

ACCESS_TOKEN_EXPIRY = 15  # minutes
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60  # minutes

SECRET_KEY = "SECRET123"
ALGORITHM = "HS256"


# DATABASE CONNECTION

DATABASE_URL = "sqlite:///./battle-royale.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

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


Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    yield db
    db.close()


# --------------------------------------------------
# E10: UPDATE SQUAD DETAILS
# --------------------------------------------------

def update_squad(db: Session, squad_id: int, user_id: int, squad_name: str):

    squad = db.query(Squad).filter(
        Squad.squad_id == squad_id
    ).first()

    if squad is None:
        return False, "Squad not found", None

    if squad.captain_id != user_id: #pyright:ignore
        return False, "Only the squad captain can update squad details", None

    if squad_name.strip() == "":
        return False, "Squad name cannot be empty", None

    squad.squad_name = squad_name.strip() #pyright:ignore

    db.commit()
    db.refresh(squad)

    return True, "Squad updated successfully", {
        "squad_id": squad.squad_id,
        "squad_name": squad.squad_name,
        "captain_id": squad.captain_id
    }


# --------------------------------------------------
# E11: REGISTER SQUAD FOR TOURNAMENT
# --------------------------------------------------

def register_squad(db: Session, tournament_id: int, squad_id: int, user_id: int):

    tournament = db.query(Tournament).filter(
        Tournament.tournament_id == tournament_id
    ).first()

    if tournament is None:
        return False, "Tournament not found", None

    squad = db.query(Squad).filter(
        Squad.squad_id == squad_id
    ).first()

    if squad is None:
        return False, "Squad not found", None

    if squad.captain_id != user_id: #pyright:ignore
        return False, "Only the squad captain can register the squad", None

    if tournament.status != "registration_open": #pyright:ignore
        return False, "Tournament registration is not open", None

    current_time = datetime.now()

    if current_time < tournament.registration_start or current_time > tournament.registration_end: #pyright:ignore
        return False, "Tournament registration is outside the allowed dates", None 

    members = db.query(SquadMember).filter(
        SquadMember.squad_id == squad_id,
        SquadMember.status == "active"
    ).all()

    if len(members) < 1 or len(members) > 4:
        return False, "A squad must have between 1 and 4 active players", None

    existing_registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.squad_id == squad_id
    ).first()

    if existing_registration is not None:
        if existing_registration.status == "active":  #pyright:ignore
            return False, "Squad is already registered", None
        existing_registration.status = "active"  #pyright:ignore
        existing_registration.registered_at = datetime.now()  #pyright:ignore

    else:
        existing_registration = TournamentRegistration(
            tournament_id=tournament_id,
            squad_id=squad_id,
            status="active"
        )

        db.add(existing_registration)

    registered_squads = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.status == "active"
    ).count()

    if registered_squads > tournament.max_squads:  #pyright:ignore
        db.rollback()
        return False, "Tournament has reached maximum squad capacity", None

    for member in members:

        other_registration = db.query(TournamentRegistration).join(
            SquadMember,
            TournamentRegistration.squad_id == SquadMember.squad_id
        ).filter(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.status == "active",
            SquadMember.player_id == member.player_id,
            SquadMember.status == "active",
            SquadMember.squad_id != squad_id
        ).first()

        if other_registration is not None:
            db.rollback()
            return False, "A player is already part of another registered squad", None

    db.commit()
    db.refresh(existing_registration)

    return True, "Squad registered successfully", {
        "registration_id": existing_registration.registration_id,
        "tournament_id": tournament_id,
        "squad_id": squad_id,
        "status": existing_registration.status
    }


# --------------------------------------------------
# E12: WITHDRAW SQUAD FROM TOURNAMENT
# --------------------------------------------------

def withdraw_squad(db: Session, tournament_id: int, squad_id: int, user_id: int):

    squad = db.query(Squad).filter(
        Squad.squad_id == squad_id
    ).first()

    if squad is None:
        return False, "Squad not found", None

    if squad.captain_id != user_id:  #pyright:ignore
        return False, "Only the squad captain can withdraw the squad", None

    tournament = db.query(Tournament).filter(
        Tournament.tournament_id == tournament_id
    ).first()

    if tournament is None:
        return False, "Tournament not found", None

    if tournament.status in ["ongoing", "completed", "cancelled"]:
        return False, "Squad cannot withdraw from this tournament", None

    registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.squad_id == squad_id,
        TournamentRegistration.status == "active"
    ).first()

    if registration is None:
        return False, "Squad is not registered for this tournament", None

    registration.status = "withdrawn"  #pyright:ignore

    db.commit()

    return True, "Squad withdrawn successfully", {
        "registration_id": registration.registration_id,
        "tournament_id": tournament_id,
        "squad_id": squad_id,
        "status": registration.status
    }


# --------------------------------------------------
# E13: SCHEDULE TOURNAMENT MATCH
# --------------------------------------------------

def schedule_match(
    db: Session,
    tournament_id: int,
    user_id: int,
    match_number: int,
    match_date: datetime,
    map_name: str
):

    tournament = db.query(Tournament).filter(
        Tournament.tournament_id == tournament_id
    ).first()

    if tournament is None:
        return False, "Tournament not found", None

    if tournament.organizer_id != user_id:  #pyright:ignore
        return False, "You are not the organizer of this tournament", None

    if tournament.status not in ["registration_closed", "ongoing"]:
        return False, "Matches cannot be scheduled in the current tournament status", None

    if match_number < 1:
        return False, "Match number must be greater than zero", None

    if match_date <= datetime.now():
        return False, "Match date must be in the future", None

    if map_name.strip() == "":
        return False, "Map name cannot be empty", None

    existing_match = db.query(Match).filter(
        Match.tournament_id == tournament_id,
        Match.match_number == match_number
    ).first()

    if existing_match is not None:
        return False, "This match number already exists", None

    new_match = Match(
        tournament_id=tournament_id,
        match_number=match_number,
        match_date=match_date,
        map=map_name.strip()
    )

    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    return True, "Match scheduled successfully", {
        "match_id": new_match.match_id,
        "tournament_id": new_match.tournament_id,
        "match_number": new_match.match_number,
        "match_date": new_match.match_date,
        "map": new_match.map
    }


# --------------------------------------------------
# E14: SUBMIT MATCH RESULTS
# --------------------------------------------------

def submit_match_result(
    db: Session,
    match_id: int,
    user_id: int,
    squad_id: int,
    placement: int,
    kills: int
):

    match = db.query(Match).filter(
        Match.match_id == match_id
    ).first()

    if match is None:
        return False, "Match not found", None

    tournament = db.query(Tournament).filter(
        Tournament.tournament_id == match.tournament_id
    ).first()

    if tournament.organizer_id != user_id:  #pyright:ignore
        return False, "You are not the organizer of this tournament", None

    if tournament.status not in ["ongoing", "completed"]:  #pyright:ignore
        return False, "Results cannot be submitted for this tournament", None

    if placement < 1:
        return False, "Placement must be at least 1", None

    if kills < 0:
        return False, "Kills cannot be negative", None

    squad = db.query(Squad).filter(
        Squad.squad_id == squad_id
    ).first()

    if squad is None:
        return False, "Squad not found", None

    registration = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == match.tournament_id,
        TournamentRegistration.squad_id == squad_id,
        TournamentRegistration.status == "active"
    ).first()

    if registration is None:
        return False, "Only registered squads can receive match results", None


    existing_result = db.query(MatchResult).filter(
        MatchResult.match_id == match_id,
        MatchResult.squad_id == squad_id
    ).first()

    if existing_result is not None:
        return False, "Result for this squad has already been submitted", None


    if placement == 1:
        placement_points = 15
    elif placement == 2:
        placement_points = 12
    elif placement == 3:
        placement_points = 10
    elif placement == 4:
        placement_points = 8
    elif placement == 5:
        placement_points = 6
    elif placement <= 10:
        placement_points = 4
    else:
        placement_points = 0

    total_points = placement_points + kills

    new_result = MatchResult(
        match_id=match_id,
        squad_id=squad_id,
        placement=placement,
        kills=kills,
        placement_points=placement_points,
        total_points=total_points
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return True, "Match result submitted successfully", {
        "result_id": new_result.result_id,
        "match_id": match_id,
        "squad_id": squad_id,
        "placement": placement,
        "kills": kills,
        "placement_points": placement_points,
        "total_points": total_points
    }


# --------------------------------------------------
# E15: GET TOURNAMENT LEADERBOARD
# --------------------------------------------------

def get_tournament_leaderboard(db: Session, tournament_id: int):

    tournament = db.query(Tournament).filter(
        Tournament.tournament_id == tournament_id
    ).first()

    if tournament is None:
        return False, "Tournament not found", None


    registrations = db.query(TournamentRegistration).filter(
        TournamentRegistration.tournament_id == tournament_id,
        TournamentRegistration.status == "active"
    ).all()

    leaderboard = []

    for registration in registrations:

        squad = db.query(Squad).filter(
            Squad.squad_id == registration.squad_id
        ).first()

        results = db.query(MatchResult).join(
            Match,
            MatchResult.match_id == Match.match_id
        ).filter(
            Match.tournament_id == tournament_id,
            MatchResult.squad_id == registration.squad_id
        ).all()

        total_kills = 0
        total_points = 0

        for result in results:
            total_kills = total_kills + result.kills
            total_points = total_points + result.total_points

        leaderboard.append({
            "squad_id": squad.squad_id,  #pyright:ignore
            "squad_name": squad.squad_name,  #pyright:ignore
            "total_kills": total_kills,
            "total_points": total_points
        })


    leaderboard.sort(
        key=lambda squad: (squad["total_points"], squad["total_kills"]),
        reverse=True
    )


    rank = 1

    for squad in leaderboard:
        squad["rank"] = rank
        rank = rank + 1

    return True, "Leaderboard retrieved successfully", leaderboard
