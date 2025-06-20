# 🎷 Music Events Aggregator

A Python-based web crawler that scrapes music events and stores them in a PostgreSQL database, accessible via pgAdmin. Perfect for building your own personalized gig calendar or analytics platform.

---

## 🐳 Stack

- **Python 3.13**
- **Docker + Docker Compose**
- **PostgreSQL**
- **pgAdmin 4**
- **SQLAlchemy (async)**
- **asyncpg**

---

## 🚀 Features

- Scrapes and stores live music events data
- Async database integration
- pgAdmin web interface for DB management
- Secure `.env`-based configuration
- Persistent volume for pgAdmin

---

## 📦 Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

## 🔐 Configuration

Create your own `.env` file based on the provided `.env.example`:

```
POSTGRES_USER=super_secret_pg_user
POSTGRES_PASSWORD=super_secret_pg_pwd
POSTGRES_DB=super_secred_db_name
DATABASE_URL=postgresql+asyncpg://super_secret_pg_user:super_secret_pg_pwd@postgres:5432/super_secred_db_name
PGADMIN_DEFAULT_EMAIL=super_secret_pgAdmin_user
PGADMIN_DEFAULT_PASSWORD=super_secret_pgAdmin_pwd
PGADMIN_LISTEN_PORT=1234
PGADMIN_ACCESS_PORT=5678
POSTGRESS_LISTEN_PORT=9012
POSTGRESS_ACCESS_PORT=3456
```

Likewise, create a `servers.json` file (like `servers.json.example`) to auto-register your database inside pgAdmin:

```
{
  "Servers": {
    "1": {
      "Name": "super_secret_server_name",
      "Group": "super_secret_group_name",
      "Host": "postgres",
      "Port": 5432,
      "MaintenanceDB": "super_secred_db_name",
      "Username": "a_different_super_secret_user",
      "Password": "a_different_super_secret_pwd",
      "SSLMode": "prefer"
    }
  }
}
```

## Installation

1. Clone the repository 

```
git clone https://github.com/aggeor/music-events-aggregator
cd music-events-aggregator
```

2. Start the services
``` 
docker compose up --build
```
This will:

- Start a PostgreSQL database

- Start pgAdmin at http://localhost:<PGADMIN_ACCESS_PORT>

- Build and run the crawler once

3. Stop the services
``` 
docker compose down -v
```
The `-v` flag also removes volumes (database + pgAdmin state)

📅 Run the Crawler Manually
You can run the crawler again at any time:

```
docker compose run --rm crawler
```

✨ Author
Made with 🎷 by [Aggelos Georgiadis](https://github.com/aggeor)