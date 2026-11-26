# battle-royale-tournament-manager

# Team 06 · Class-rep-Elections

| Team | Partner 1 | Partner 2 | Partner 3 | Project |
|---|---|---|---|---|
| 06 | Kommaddi Fayaz | chaithanya |Praneeth | [battle-royale--tournament-manager](https://github.com/chaithu-300/battle-royale--tournament-manager) |


## Problem Statements

1. **Tournament Management Difficulty:** Managing BGMI tournaments manually, including tournament creation, registrations, match scheduling, and results, is time-consuming and difficult to organize efficiently.

2. **Squad Formation and Coordination:** Players face difficulties in forming squads, inviting teammates, managing squad members, and registering their squads for tournaments in a centralized system.

3. **Result Tracking and Ranking:** Tracking match placements, kills, calculating points, and maintaining an accurate tournament leaderboard manually can lead to errors and a lack of transparency.


## 1. Who is doing what

Update your own row at every check-in.

| Day | Partner | What will you do? | Completed? | What are you going to work on next? | Stuck on? |
|---|---|---|---|---|---|
| Day 1 | Praneeth | E1 to E6 endpoints | E1 & E2 | E3 to E6 endpoints | no |
| Day 1 | Kommaddi Fayaz | Authenticatin endpoints and E7,E8,E9 endpoints | Athentication Endpoints  | E7,E8,E9 Endpoints  |  |
| Day 1 | chaithanya | Defined Endpoints from E10 to E15 | E10, 12, 13 |E14, 15 | No |
| Day 2 | Praneeth | working on E3,E4,E5,E6 functions| completed | solve the errors|yes  |
| Day 2 | Kommaddi Fayaz | E7,E8,E9 endpoints  | E7,E8,E9 endpoints  | solvoing the merge errors and checking swager  | No |
| Day 2 | chaithanya | Defining E14 and E15 | E14 , 15 | Assign Role Based Access | No |
| Day 3 | Praneeth | modified the code due to errors and build the docker image locally |done  | --- | no |
| Day 3 | Kommaddi Fayaz | solvoing the merge errors and checking swager   | done | prepare for presentation  |  No  |
| Day 3 | chaithanya | Create docker file and implement git hub actions and create EC2 | Yes  |  prepare for presentation | No |


## 2. Endpoint tracker

## API Requirements

The application provides 18 APIs across Authentication (A1–A3) and Project-Specific endpoints (E1–E15):

### A. Authentication APIs

| # | Description | Method | Endpoint | Path / Query Params | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A1 | Register a new account | POST | `/register` | None | `username`, `email`, `password` | `message`, `user_id` | 201, 400, 409, 422 |
| A2 | Login and generate access and refresh tokens | POST | `/login` | None | `email`, `password` | `message`, `access_token`, `refresh_token`, `token_type` | 200, 401, 422 |
| A3 | Generate a new access token | POST | `/refresh` | Header: `token` | None | `access_token`, `token_type` | 200, 401 |

### B. Project-Specific APIs

| # | Description | Method | Endpoint | Path / Query Params | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E1 | Create an organizer account (Admin) | POST | `/admin/organizers` | Header: `token` | `username`, `email`, `password` | `message`, `user_id` | 201, 400, 401, 403, 409 |
| E2 | Create a tournament (Organizer) | POST | `/tournaments` | Header: `token` | `name`, `game_mode`, `max_squads`, `start_date`, `prize_pool` | `message`, `tournament_id` | 201, 400, 401, 403, 422 |
| E3 | Get all available tournaments (All) | GET | `/tournaments` | Query: `status` (optional) | None | List of tournaments (`tournament_id`, `name`, `status`, `max_squads`, etc.) | 200 |
| E4 | Get details of a particular tournament (All) | GET | `/tournaments/{tournament_id}` | Path: `tournament_id` | None | Tournament details (`tournament_id`, `name`, `game_mode`, `status`, `registered_squads`, etc.) | 200, 404 |
| E5 | Update tournament details and registration status (Organizer) | PUT | `/tournaments/{tournament_id}` | Path: `tournament_id`, Header: `token` | `name`, `status`, `registration_status`, `max_squads`, `start_date` | `message`, updated tournament details | 200, 400, 401, 403, 404 |
| E6 | Create a squad (Player) | POST | `/squads` | Header: `token` | `squad_name`, `tag` | `message`, `squad_id` | 201, 400, 401, 403, 422 |
| E7 | Get squads created or joined by the logged-in player (Player) | GET | `/squads/my-squads` | Header: `token` | None | List of squads (`squad_id`, `squad_name`, `captain_id`, `members`) | 200, 401, 403 |
| E8 | Invite a player to a squad (Squad captain) | POST | `/squads/invite` | Header: `token` | `squad_id`, `invited_player_id` | `message`, `invitation_id` | 200, 400, 401, 403, 404 |
| E9 | Accept or reject a squad invitation (Invited player) | POST | `/squads/invitations/respond` | Header: `token` | `invitation_id`, `action` (`accept` / `reject`) | `message`, `status` | 200, 400, 401, 403, 404 |
| E10 | Update squad details (Squad captain) | PUT | `/squads/{squad_id}` | Path: `squad_id`, Header: `token` | `squad_name`, `tag` | `message`, updated squad details | 200, 400, 401, 403, 404 |
| E11 | Register a squad for a tournament (Squad captain) | POST | `/tournaments/{tournament_id}/register` | Path: `tournament_id`, Header: `token` | `squad_id` | `message`, `registration_id` | 201, 400, 401, 403, 404 |
| E12 | Withdraw a squad from a tournament (Squad captain) | POST | `/tournaments/{tournament_id}/withdraw` | Path: `tournament_id`, Header: `token` | `squad_id` | `message`, `status` | 200, 400, 401, 403, 404 |
| E13 | Schedule a tournament match (Organizer) | POST | `/tournaments/{tournament_id}/matches` | Path: `tournament_id`, Header: `token` | `map_name`, `match_number`, `scheduled_time` | `message`, `match_id` | 201, 400, 401, 403, 404 |
| E14 | Submit match results (Organizer) | POST | `/matches/{match_id}/results` | Path: `match_id`, Header: `token` | `squad_id`, `placement`, `kills` | `message`, `total_points` | 200, 400, 401, 403, 404 |
| E15 | Get the tournament leaderboard (All) | GET | `/tournaments/{tournament_id}/leaderboard` | Path: `tournament_id` | None | Ranked list of squads (`rank`, `squad_id`, `squad_name`, `total_kills`, `total_points`) | 200, 404 |



## 3.File structure
```text
battle-royale-tournament-manager/
├── __pycache__/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── venv/
├── battle-royale.db
├── dockerfile
├── functions.py
├── main.py
├── README.md
└── requirements.txt
```

## Database Tables

| # | Table | Columns |
| :--- | :--- | :--- |
| 1 | `users` | `user_id`, `username`, `email`, `hashed_password`, `role`, `created_at` |
| 2 | `tournaments` | `tournament_id`, `name`, `game_mode`, `max_squads`, `start_date`, `prize_pool`, `registration_status`, `status`, `organizer_id`, `created_at` |
| 3 | `squads` | `squad_id`, `squad_name`, `tag`, `captain_id`, `created_at` |
| 4 | `squad_members` | `member_id`, `squad_id`, `player_id`, `status`, `joined_at` |
| 5 | `invitations` | `invitation_id`, `squad_id`, `invited_player_id`, `status`, `created_at` |
| 6 | `registrations` | `registration_id`, `tournament_id`, `squad_id`, `status`, `registered_at` |
| 7 | `matches` | `match_id`, `tournament_id`, `map_name`, `match_number`, `scheduled_time`, `status` |
| 8 | `match_results` | `result_id`, `match_id`, `squad_id`, `placement`, `kills`, `total_points` |
