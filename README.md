# battle-royale-tournament-manager

# Team 04 · battle-royale-tournament-manager

| Team | Partner 1 | Partner 2 | Partner 3 | Project |
|---|---|---|---|---|
| 04 | Kommaddi Fayaz | chaithanya |Praneeth | [battle-royale--tournament-manager](https://github.com/chaithu-300/battle-royale--tournament-manager) |


## Problem Statements

1. **Tournament Management Difficulty:** Managing BGMI tournaments manually, including tournament creation, registrations, match scheduling, and results, is time-consuming and difficult to organize efficiently.

2. **Squad Formation and Coordination:** Players face difficulties in forming squads, inviting teammates, managing squad members, and registering their squads for tournaments in a centralized system.

3. **Result Tracking and Ranking:** Tracking match placements, kills, calculating points, and maintaining an accurate tournament leaderboard manually can lead to errors and a lack of transparency.


# Backend Setup and Execution

This project uses **FastAPI, Python, SQLite, and SQLAlchemy** for backend development.

## 1. Prerequisites

Install the following before running the project:
- Docker Desktop (for Docker execution)
- AWS account (for EC2 deployment)

## 2. Clone the Repository

```
git clone <https://github.com/chaithu-300/battle-royale--tournament-manager/edit/main>
```

Navigate into the project:

```
cd <battle-royale-tournament-manager>
```

### Create a Virtual Environment

```
python -m venv venv
```

### Activate the Virtual Environment

**Windows:**

```
venv\Scripts\activate
```

### Install Dependencies

Install all project dependencies using the requirements file:

```
pip install -r requirements.txt
```

### Run the Application

```
uvicorn main:app --reload --port 8001
```

The Application will be available at:

- Application URL: http://127.0.0.1:8001
- API Documentation (Swagger UI): http://127.0.0.1:8001/docs

## 4. Docker Setup and Execution

Docker allows the application to run inside a container without requiring manual Python environment setup.

Make sure Docker Desktop is installed and running.

Open a terminal and navigate to the folder:

```
cd battle-royale-tournament-manager
```

### Build the Docker Image

```
docker build -t battle-royale-tournament-manager:v1.0.0 .
```

### Run the Docker Container

```
docker run -d -p 8001:8001 --name battle-royale-tournament-manager:v1.0.0
```

### Check Running Containers

```
docker ps
```

### View Container Logs

```
docker logs battle-royale-tournament-manager
```

### Stop the Container

```
docker stop battle-royale-tournament-manager
```

### Start the Container Again

```
docker start battle-royale-tournament-manager
```

### Remove the Container

```
docker stop battle-royale-tournament-manager
docker rm battle-royale-tournament-manager
```

### Remove the Docker Image

```
docker rmi battle-royale-tournament-manager
```

The Dockerized backend will be available at:

- Application URL: http://127.0.0.1:8001
- API Documentation: http://127.0.0.1:8001/docs

## 5. AWS EC2 Deployment

AWS EC2 (Elastic Compute Cloud) is used to deploy and run the backend application on a cloud-based virtual machine.

### Step 1: Launch an EC2 Instance

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Open the EC2 service.
3. Select **Launch Instance**.
4. Enter an instance name, such as `BGMI-Tournament-Backend`.
5. Select **Ubuntu Server LTS** as the operating system.
6. Choose an instance type suitable for your application.
7. Create or select a key pair and download the `.pem` file.
8. Configure the network settings and security group.
9. Launch the instance.

### Step 2: Configure Security Group

Open the EC2 instance's Security Group and configure the following inbound rules:

| Type | Protocol | Port | Source |
|---|---|---|---|
| SSH | TCP | 22 | My IP |
| Custom TCP | TCP | 8001 | Your IP (testing) |

For public access to the API, port 8001 can temporarily be opened to `0.0.0.0/0` for testing. Restrict access appropriately before production deployment.

### Step 3: Connect to the EC2 Instance

On your local computer, open a terminal in the folder containing your downloaded `.pem` key.

Replace `<54.210.38.202>` with your instance's public IPv4 address.

### Step 4: Update the Ubuntu System

After connecting to EC2, execute:

```
sudo apt update
sudo apt upgrade -y
```

Install Docker Engine:

```
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
```

Verify Docker installation:

```
sudo docker run hello-world
```

### Step 7: Build the Docker Image

```
sudo docker build -t bgmi-tournament-manager .
```

### Step 8: Run the Docker Container

```
sudo docker run -d -p 8001:8001 --restart unless-stopped --name battle-royale-tournament-manager
```

### Step 9: Verify Deployment

Check whether the container is running:

```
sudo docker ps
```

View application logs:

```
sudo docker logs battle-royale-tournament-manager
```

Open the following URLs in your browser:

**Backend API:**

```text
http://54.210.38.202:8001/docs
```

**Swagger API Documentation:**

```
http://54.210.38.202:8001/docs
```

Replace `<54.210.38.202>` with the public IPv4 address of your EC2 instance.

## 6. Useful Docker Commands

| Command | Description |
|---|---|
| `docker ps` | View running containers |
| `docker ps -a` | View all containers |
| `docker images` | View downloaded and built images |
| `docker logs <container-name>` | View container logs |
| `docker stop <container-name>` | Stop a container |
| `docker start <container-name>` | Start a stopped container |
| `docker restart <container-name>` | Restart a container |
| `docker rm <container-name>` | Remove a container |
| `docker rmi <image-name>` | Remove an image |

**Note:** The Docker commands on EC2 are executed with `sudo` unless Docker permissions have been configured for the user.

## 7. Database

The application uses **SQLite** as its database and SQLAlchemy as its ORM.

The database is configured using:

```python
DB_URL = "sqlite:///./battle-royale.db"
```

The database file is created automatically when the application initializes its database tables.

**Important:** The database file inside a Docker container should be persisted using a Docker volume or a host-mounted directory. Otherwise, removing the container can result in database loss.

For deployment, make sure the database storage location is mounted persistently.

## 8. Project API Documentation

FastAPI automatically generates interactive API documentation.

- Swagger UI: `/docs`
- ReDoc: `/redoc`

Use Swagger UI to test the authentication, tournament, squad, match, result, and leaderboard APIs.


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
