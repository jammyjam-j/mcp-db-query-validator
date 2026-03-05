# mcp-db-query-validator  
FastAPI MCP server validating SQL queries before DB execution  

## Overview  
mcp‑db‑query‑validator is a lightweight FastAPI service that acts as an intermediary between AI agents and a relational database. It receives raw SQL statements, runs them through a safety validator, and only forwards those that pass the checks to the underlying database engine. This approach mitigates accidental data leaks, injection attacks, and unintended schema modifications while still allowing flexible query execution for trusted users.

## Features  
- **MCP‑compatible**: Implements the Machine‑Controlled Protocol (MCP) spec for AI agents.  
- **SQL safety validation**: Custom logic in `services/query_validator.py` blocks destructive statements and enforces whitelists.  
- **JWT authentication middleware**: Protects all endpoints with bearer tokens (`middleware/auth_middleware.py`).  
- **User management**: CRUD routes for users (`routes/users.py`) backed by SQLAlchemy models.  
- **Dockerized**: `Dockerfile` and `docker‑compose.yml` enable rapid deployment.  
- **Automated tests**: Pytest suite covering API endpoints and the validator logic.  
- **Database migrations**: Alembic migration script in `migrations/versions/0001_create_user_table.py`.  

## Tech Stack  
- Python 3.10+  
- FastAPI  
- SQLAlchemy (async) with PostgreSQL  
- Alembic for migrations  
- Pydantic for data validation  
- Docker & docker‑compose  
- Pytest, httpx for testing  

## Installation  

```bash
git clone https://github.com/jammyjam-j/mcp-db-query-validator
cd mcp-db-query-validator

# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt
```

## Usage  

### Running locally  
```bash
uvicorn app.main:app --reload
```
The server will be available at `http://127.0.0.1:8000`.

### Docker Compose  
```bash
docker compose up --build
```
This starts the API and a PostgreSQL instance.

### Example request  

```bash
curl -X POST "http://localhost:8000/mcp/execute" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"query": "SELECT * FROM users;"}'
```

If the query passes validation, the response will contain the result set. Otherwise a 400 error with a safety message is returned.

## API Endpoints  

| Method | Path                | Description                                   |
|--------|---------------------|-----------------------------------------------|
| POST   | `/mcp/execute`      | Validate and execute an SQL statement         |
| GET    | `/users/`           | List all users (auth required)                |
| POST   | `/users/`           | Create a new user                              |
| GET    | `/users/{id}`       | Retrieve a single user                         |
| PUT    | `/users/{id}`       | Update an existing user                        |
| DELETE | `/users/{id}`       | Delete a user                                  |

All endpoints require a valid JWT in the `Authorization` header.

## References and Resources  

- [Building an Agentic AI – RunSQLOperations via Natural Language](https://www.linkedin.com/pulse/agentic-mysql-ai-executing-sql-database-natural-shanmugavelu-munivelu-2kflc)  
- [FastAPIMCPServer-MCPServer](https://mcprepository.com/Nabeelshar/fastapi-mcp-server)  
- [How to build MCP server with Authentication in Python using FastAPI](https://medium.com/@miki_45906/how-to-build-mcp-server-with-authentication-in-python-using-fastapi-8777f1556f75)  
- [How to Use FastAPIMCPServer](https://apidog.com/blog/fastapi-mcp/)  
- [Building an MCP Server with fastapi-mcp for Stock Analysis - DEV Community](https://dev.to/mrzaizai2k/building-an-mcp-server-with-fastapi-mcp-for-stock-analysis-a-step-by-step-guide-de6)  

## Contributing  

Bug reports and pull requests are welcome.  
Please open issues or PRs at https://github.com/jammyjam-j/mcp-db-query-validator/issues.

## License  

MIT © 2024