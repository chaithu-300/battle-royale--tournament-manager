from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, Session

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


def get_current_user(token):
    if not token:
        return False

    user_id = verify_token(token)

    if user_id is False:
        return False

    session = Session(engine)

    user = session.query(User).filter_by(user_id=user_id).first()

    session.close()

    if user is None:
        return False

    return user

# --------------------------------------------------
# E10: UPDATE SQUAD FOR TOURNAMENT
# --------------------------------------------------

def update_squad(squad_id, user_id, squad_name):
    session = Session(engine)

    squad = session.query(Squad).filter_by(squad_id=squad_id).first()

    if squad is None:
        session.close()
        return False

    if squad.captain_id != user_id:
        session.close()
        return False

    if squad_name.strip() == "":
        session.close()
        return False

    squad.squad_name = squad_name.strip()

    session.commit()
    session.close()

    return True


# --------------------------------------------------
# E11: REGISTER SQUAD FOR TOURNAMENT
# --------------------------------------------------
def register_squad(tournament_id, squad_id, user_id):
    session = Session(engine)

    tournament = session.query(Tournament).filter_by(tournament_id=tournament_id).first()

    if tournament is None:
        session.close()
        return False

    squad = session.query(Squad).filter_by(squad_id=squad_id).first()

    if squad is None or squad.captain_id != user_id:
        session.close()
        return False

    if tournament.status != "registration_open":   #pyright:ignore
        session.close()
        return False

    if datetime.now() < tournament.registration_start or datetime.now() > tournament.registration_end:  #pyright:ignore
        session.close()
        return False

    members = session.query(SquadMember).filter_by(
        squad_id=squad_id,
        status="active"
    ).all()

    if len(members) < 1 or len(members) > 4:
        session.close()
        return False

    registration = session.query(TournamentRegistration).filter_by(
        tournament_id=tournament_id,
        squad_id=squad_id
    ).first()

    if registration is not None and registration.status == "active":  #pyright:ignore
        session.close()
        return False

    registered_squads = session.query(TournamentRegistration).filter_by(
        tournament_id=tournament_id,
        status="active"
    ).count()

    if registered_squads >= tournament.max_squads:  #pyright:ignore
        session.close()
        return False

    for member in members:
        other_squad = session.query(SquadMember).join(
            TournamentRegistration,
            SquadMember.squad_id == TournamentRegistration.squad_id
        ).filter(
            TournamentRegistration.tournament_id == tournament_id,
            TournamentRegistration.status == "active",
            SquadMember.player_id == member.player_id,
            SquadMember.status == "active"
        ).first()

        if other_squad is not None:
            session.close()
            return False

    if registration is None:
        registration = TournamentRegistration(
            tournament_id=tournament_id,
            squad_id=squad_id,
            status="active"
        )
        session.add(registration)
    else:
        registration.status = "active"  #pyright:ignore
        registration.registered_at = datetime.now()  #pyright:ignore

    session.commit()

    response = {
        "registration_id": registration.registration_id,
        "tournament_id": tournament_id,
        "squad_id": squad_id,
        "status": registration.status
    }

    session.close()
    return response


# --------------------------------------------------
# E12: WITHDRAW SQUAD FROM TOURNAMENT
# --------------------------------------------------

def withdraw_squad(tournament_id, squad_id, user_id):
    session = Session(engine)

    squad = session.query(Squad).filter_by(squad_id=squad_id).first()

    if squad is None or squad.captain_id != user_id:
        session.close()
        return False

    tournament = session.query(Tournament).filter_by(tournament_id=tournament_id).first()

    if tournament is None:
        session.close()
        return False

    if tournament.status in ["ongoing", "completed", "cancelled"]:
        session.close()
        return False

    registration = session.query(TournamentRegistration).filter_by(
        tournament_id=tournament_id,
        squad_id=squad_id,
        status="active"
    ).first()

    if registration is None:
        session.close()
        return False

    registration.status = "withdrawn"   #pyright:ignore

    session.commit()

    response = {
        "registration_id": registration.registration_id,
        "tournament_id": tournament_id,
        "squad_id": squad_id,
        "status": registration.status
    }

    session.close()
    return response


# --------------------------------------------------
# E13: SCHEDULE TOURNAMENT MATCH
# --------------------------------------------------
def schedule_match(tournament_id, user_id, match_number, match_date, map_name):
    session = Session(engine)

    tournament = session.query(Tournament).filter_by(tournament_id=tournament_id).first()

    if tournament is None or tournament.organizer_id != user_id:
        session.close()
        return False

    if tournament.status not in ["registration_closed", "ongoing"]:
        session.close()
        return False

    if match_number < 1:
        session.close()
        return False

    if match_date <= datetime.now():
        session.close()
        return False

    if map_name.strip() == "":
        session.close()
        return False

    existing_match = session.query(Match).filter_by(
        tournament_id=tournament_id,
        match_number=match_number
    ).first()

    if existing_match is not None:
        session.close()
        return False

    new_match = Match(
        tournament_id=tournament_id,
        match_number=match_number,
        match_date=match_date,
        map=map_name.strip()
    )

    session.add(new_match)
    session.commit()

    response = {
        "match_id": new_match.match_id,
        "tournament_id": tournament_id,
        "match_number": match_number,
        "match_date": match_date,
        "map": map_name.strip()
    }

    session.close()
    return response

# --------------------------------------------------
# E14: SUBMIT MATCH RESULTS
# --------------------------------------------------
def submit_match_result(match_id, user_id, squad_id, placement, kills):
    session = Session(engine)

    match = session.query(Match).filter_by(match_id=match_id).first()

    if match is None:
        session.close()
        return False

    tournament = session.query(Tournament).filter_by(
        tournament_id=match.tournament_id
    ).first()

    if tournament is None or tournament.organizer_id != user_id:
        session.close()
        return False

    if tournament.status not in ["ongoing", "completed"]:
        session.close()
        return False

    if placement < 1 or kills < 0:
        session.close()
        return False

    squad = session.query(Squad).filter_by(squad_id=squad_id).first()

    if squad is None:
        session.close()
        return False

    registration = session.query(TournamentRegistration).filter_by(
        tournament_id=match.tournament_id,
        squad_id=squad_id,
        status="active"
    ).first()

    if registration is None:
        session.close()
        return False

    existing_result = session.query(MatchResult).filter_by(
        match_id=match_id,
        squad_id=squad_id
    ).first()

    if existing_result is not None:
        session.close()
        return False

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

    session.add(new_result)
    session.commit()

    response = {
        "result_id": new_result.result_id,
        "match_id": match_id,
        "squad_id": squad_id,
        "placement": placement,
        "kills": kills,
        "placement_points": placement_points,
        "total_points": total_points
    }

    session.close()
    return response

# --------------------------------------------------
# E15: GET TOURNAMENT LEADERBOARD
# --------------------------------------------------
def get_tournament_leaderboard(tournament_id):
    session = Session(engine)

    tournament = session.query(Tournament).filter_by(
        tournament_id=tournament_id
    ).first()

    if tournament is None:
        session.close()
        return False

    registrations = session.query(TournamentRegistration).filter_by(
        tournament_id=tournament_id,
        status="active"
    ).all()

    leaderboard = []

    for registration in registrations:
        squad = session.query(Squad).filter_by(
            squad_id=registration.squad_id
        ).first()

        results = session.query(MatchResult).join(Match).filter(
            Match.tournament_id == tournament_id,
            MatchResult.squad_id == registration.squad_id
        ).all()

        total_kills = 0
        total_points = 0

        for result in results:
            total_kills += result.kills
            total_points += result.total_points

        leaderboard.append({
            "squad_id": squad.squad_id,   #pyright:ignore
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
        rank += 1

    session.close()
    return leaderboard
