from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, Session
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, create_engine #pyright: ignore
from sqlalchemy.orm import Session, declarative_base #pyright: ignore
import jwt #pyright: ignore
from argon2 import PasswordHasher #pyright: ignore
from argon2.exceptions import VerifyMismatchError #pyright: ignore

ACCESS_TOKEN_EXPIRY = 15  # minutes
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60  # minutes

SECRET_KEY = "SECRET123"
ALGORITHM = "HS256"
ph = PasswordHasher()


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

    user_id = verify_token(token, "access")  

    if user_id is False:
        return False

    session = Session(engine)

    user = session.query(User).filter_by(user_id=user_id).first()

    session.close()

    if user is None:
        return False

    return user

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
        ph.verify(user.password, password)  #pyright:ignore

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

    if not token:
        return False

    try:
        payload = jwt.decode(
            jwt=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return False

    if payload.get("token_type") == token_type:
        return payload.get("user_id")

    return False


# -------- REFRESH TOKEN --------

def refresh_access_token(token):

    if not token:
        return False

    try:
        payload = jwt.decode(
            jwt=token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return False

    if payload.get("token_type") != "refresh":
        return False

    access_token = create_token(
        payload.get("user_id"),
        payload.get("username"),
        payload.get("email"),
        payload.get("role"),
        "access"
    )

    return {
        "access_token": access_token
    }
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
        password=ph.hash(password),
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


# E5 – Update tournament
def update_tournament(tournament_id, user_id, tournament_name,
                      description, map_name, registration_start,
                      registration_end, max_squads, status):

    session = Session(engine)

    tournament = session.query(Tournament).filter_by(
        tournament_id=tournament_id
    ).first()

    if tournament is None:
        session.close()
        return False

    if tournament.organizer_id != user_id:
        session.close()
        return False

    if tournament.status in ["ongoing", "completed", "cancelled"]:
        session.close()
        return False

    if registration_start is not None:
        if registration_end is not None:
            if registration_start >= registration_end:
                session.close()
                return False
        elif registration_start >= tournament.registration_end:
            session.close()
            return False

        tournament.registration_start = registration_start

    if registration_end is not None:
        if registration_start is None:
            if registration_end <= tournament.registration_start:
                session.close()
                return False

        tournament.registration_end = registration_end

    if max_squads is not None:
        if max_squads < 1:
            session.close()
            return False

        registered_squads = session.query(TournamentRegistration).filter_by(
            tournament_id=tournament_id,
            status="active"
        ).count()

        if max_squads < registered_squads:
            session.close()
            return False

        tournament.max_squads = max_squads

    if tournament_name is not None:
        if tournament_name.strip() == "":
            session.close()
            return False
        tournament.tournament_name = tournament_name.strip()

    if description is not None:
        tournament.description = description

    if map_name is not None:
        if map_name.strip() == "":
            session.close()
            return False
        tournament.map = map_name.strip()

    if status is not None:
        if status not in [
            "draft",
            "registration_open",
            "registration_closed",
            "ongoing",
            "completed",
            "cancelled"
        ]:
            session.close()
            return False

        tournament.status = status

    session.commit()

    response = {
        "tournament_id": tournament.tournament_id,
        "tournament_name": tournament.tournament_name,
        "description": tournament.description,
        "map": tournament.map,
        "registration_start": tournament.registration_start,
        "registration_end": tournament.registration_end,
        "max_squads": tournament.max_squads,
        "status": tournament.status
    }

    session.close()
    return response


# E6 – Create squad
def create_squad(user_id, squad_name):
    session = Session(engine)

    if squad_name.strip() == "":
        session.close()
        return False

    new_squad = Squad(
        squad_name=squad_name.strip(),
        captain_id=user_id
    )

    session.add(new_squad)
    session.commit()

    new_member = SquadMember(
        squad_id=new_squad.squad_id,
        player_id=user_id,
        status="active"
    )

    session.add(new_member)
    session.commit()

    response = {
        "squad_id": new_squad.squad_id,
        "squad_name": new_squad.squad_name,
        "captain_id": new_squad.captain_id,
        "members": [
            {
                "player_id": user_id,
                "status": "active"
            }
        ]
    }

    session.close()
    return response




# 7) Get squads created or joined by the logged-in player

def get_player_squads(user_id):
    session = Session(engine)

    # Find squads created by this player (captain)
    created_squads = session.query(Squad).filter(Squad.captain_id == user_id).all()

    # Find squads where this player is a member
    joined_memberships = session.query(SquadMember).filter(SquadMember.player_id == user_id).all()

    response = []
    squad_ids = []

    # Add squads created by the player
    for squad in created_squads:
        if squad.squad_id not in squad_ids:
            squad_ids.append(squad.squad_id)

            response.append({
                "squad_id": squad.squad_id,
                "squad_name": squad.squad_name,
                "captain_id": squad.captain_id,
                "membership": "captain"
            })

    # Add squads joined by the player
    for membership in joined_memberships:
        squad = session.query(Squad).filter(Squad.squad_id == membership.squad_id).first()

        if squad is not None and squad.squad_id not in squad_ids:
            squad_ids.append(squad.squad_id)
            response.append({
                "squad_id": squad.squad_id,
                "squad_name": squad.squad_name,
                "captain_id": squad.captain_id,
                "membership": "member"
            })

    session.close()
    return response

# 8) Invite a player to a squad

def invite_player_to_squad(captain_id, squad_id, invited_player_id):
    session = Session(engine)
    squad = session.query(Squad).filter(Squad.squad_id == squad_id).first()
    if squad is None:
        session.close()
        return {"error": "Squad not found"}

    # Check whether the logged-in user is the captain
    if squad.captain_id != captain_id:
        session.close()
        return {"error": "Only the squad captain can invite players"}

    # Check whether the invited player exists
    invited_player = session.query(User).filter(User.user_id == invited_player_id).first()

    if invited_player is None:
        session.close()
        return {"error": "Player not found"}

    # Captain cannot invite themselves
    if captain_id == invited_player_id:
        session.close()
        return {"error": "You cannot invite yourself"}

    # Check if player is already an active member
    existing_member = session.query(SquadMember).filter(
        SquadMember.squad_id == squad_id,
        SquadMember.player_id == invited_player_id,
        SquadMember.status == "active"
    ).first()

    if existing_member:
        session.close()
        return {"error": "Player is already in this squad"}

    # Check if a pending invitation already exists
    existing_invitation = session.query(SquadInvitation).filter(
        SquadInvitation.squad_id == squad_id,
        SquadInvitation.invited_player_id == invited_player_id,
        SquadInvitation.status == "pending"
    ).first()

    if existing_invitation:
        session.close()
        return {"error": "Invitation is already pending"}

    # Count active squad members
    active_members = session.query(SquadMember).filter(
        SquadMember.squad_id == squad_id,
        SquadMember.status == "active"
    ).all()

    member_count = len(active_members)

    # Add captain if they are not already in SquadMembers
    captain_is_member = False

    for member in active_members:
        if member.player_id == captain_id:
            captain_is_member = True
            break

    if not captain_is_member:
        member_count += 1

    # Count pending invitations to avoid over-inviting
    pending_invitations = session.query(SquadInvitation).filter(
        SquadInvitation.squad_id == squad_id,
        SquadInvitation.status == "pending"
    ).count()

    if member_count + pending_invitations >= 4:
        session.close()
        return {"error": "Squad is full"}

    # Create invitation
    invitation = SquadInvitation(squad_id=squad_id,invited_player_id=invited_player_id,status="pending")
    session.add(invitation)
    session.commit()
    invitation_id = invitation.invitation_id
    session.close()
    return {
        "message": "Player invited successfully",
        "invitation_id": invitation_id
    }

# E9: Player accepts or rejects a squad invitation

def respond_to_squad_invitation(player_id, invitation_id, response):
    session = Session(engine)
    invitation = session.query(SquadInvitation).filter(
        SquadInvitation.invitation_id == invitation_id
    ).first()

    if invitation is None:
        session.close()
        return {"error": "Invitation not found"}
    
    if invitation.invited_player_id != player_id:
        session.close()
        return {"error": "You are not allowed to respond to this invitation"}

    if invitation.status != "pending":   #pyright:ignore
        session.close()
        return {"error": "Invitation has already been responded to"}

    if response == "reject":
        invitation.status = "rejected"    #pyright:ignore
        session.commit()
        session.close()
        return {"message": "Invitation rejected successfully"}

    if response == "accept":
        squad = session.query(Squad).filter(
            Squad.squad_id == invitation.squad_id
        ).first()

        if squad is None:
            session.close()
            return {"error": "Squad not found"}

        existing_member = session.query(SquadMember).filter(
            SquadMember.squad_id == invitation.squad_id,
            SquadMember.player_id == player_id,
            SquadMember.status == "active"
        ).first()

        if existing_member:
            session.close()
            return {"error": "You are already a member of this squad"}

        active_members = session.query(SquadMember).filter(
            SquadMember.squad_id == invitation.squad_id,
            SquadMember.status == "active"
        ).all()

        member_count = len(active_members)

        captain_is_member = False

        for member in active_members:
            if member.player_id == squad.captain_id:    #pyright:ignore
                captain_is_member = True
                break

        if not captain_is_member:
            member_count += 1

        if member_count >= 4:
            session.close()
            return {"error": "Squad is full"}

        new_member = SquadMember(
            squad_id=invitation.squad_id,
            player_id=player_id,
            status="active"
        )

        session.add(new_member)
        invitation.status = "accepted"    #pyright:ignore
        session.commit()
        session.close()
        return {"message": "Invitation accepted successfully"}
    session.close()
    return {"error": "Invalid response. Use accept or reject"}






def create_first_admin(username, email, password):
    session = Session(engine)

    # Check whether an admin already exists
    admin = session.query(User).filter_by(role="admin").first()

    if admin is not None:
        session.close()
        return False

    # Check whether the email is already registered
    existing_user = session.query(User).filter_by(email=email).first()

    if existing_user is not None:
        session.close()
        return False

    # Hash the password
    hashed_password = ph.hash(password)

    new_admin = User(
        username=username,
        email=email,
        password=hashed_password,
        role="admin"
    )

    session.add(new_admin)
    session.commit()
    session.close()

    return True

