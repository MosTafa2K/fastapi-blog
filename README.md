# FastAPI Blog API

A simple and production-oriented Blog REST API built with **FastAPI**, **Async SQLAlchemy**, and **PostgreSQL**.

The project includes JWT authentication, post and category management, comments, ownership-based authorization, database migrations, automated tests, and an isolated test database.

## Features

* User registration and JWT authentication
* Current authenticated user endpoint
* Password hashing with `pwdlib`
* CRUD operations for blog posts
* Post ownership authorization
* Category management
* Category filtering for posts
* Pagination for posts
* Comments for blog posts
* Comment ownership authorization
* PostgreSQL with Async SQLAlchemy
* Alembic database migrations
* Separate PostgreSQL database for tests
* Async integration tests with `pytest`
* Test coverage with `pytest-cov`
* API documentation with OpenAPI / Swagger
* Code quality checks with Ruff
* Health check endpoint

## Tech Stack

| Technology     | Purpose                            |
| -------------- | ---------------------------------- |
| FastAPI        | Web framework                      |
| SQLAlchemy 2.x | ORM / database access              |
| asyncpg        | Async PostgreSQL driver            |
| PostgreSQL     | Database                           |
| Alembic        | Database migrations                |
| Pydantic       | Data validation                    |
| PyJWT          | JWT authentication                 |
| pwdlib         | Password hashing                   |
| pytest         | Testing                            |
| pytest-asyncio | Async test support                 |
| pytest-cov     | Test coverage                      |
| Ruff           | Linting and code quality           |
| uv             | Python package and project manager |

## Requirements

* Python 3.11+
* Docker and Docker Compose
* `uv`

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd fastapi-blog
```

Install dependencies:

```bash
uv sync
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name

SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Test Environment

The project uses a separate PostgreSQL database for automated tests:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/blog_test

SECRET_KEY=test-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The test database runs separately from the development database to prevent tests from modifying development data.

## Running with Docker

Create a `.env.docker` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/db_name

SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Note:** `db` is the PostgreSQL service name defined in `docker-compose.yml`. If you change the service name, update `DATABASE_URL` accordingly.

Start the containers:

```bash
docker compose up -d
```

This starts:

* Development PostgreSQL → `localhost:5432`
* Test PostgreSQL → `localhost:5433`

## Database Migrations

After changing SQLAlchemy models, create a new migration:

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Apply all pending migrations:

```bash
uv run alembic upgrade head
```

Check the current migration:

```bash
uv run alembic current
```

## Run the Application

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically provides interactive API documentation.

### Swagger UI

```text
http://127.0.0.1:8000/docs
```

### ReDoc

```text
http://127.0.0.1:8000/redoc
```

## API Endpoints

### Authentication

| Method | Endpoint         | Auth |
| ------ | ---------------- | ---- |
| POST   | `/auth/register` | No   |
| POST   | `/auth/login`    | No   |
| GET    | `/auth/me`       | Yes  |

### Posts

| Method | Endpoint           | Auth |
| ------ | ------------------ | ---- |
| POST   | `/posts`           | Yes  |
| GET    | `/posts`           | No   |
| GET    | `/posts/{post_id}` | No   |
| PATCH  | `/posts/{post_id}` | Yes  |
| DELETE | `/posts/{post_id}` | Yes  |

Post modification and deletion are restricted to the post owner.

Posts support category filtering and pagination:

```text
GET /posts?category_id=1
```

```text
GET /posts?skip=0&limit=10
```

### Categories

| Method | Endpoint      | Auth |
| ------ | ------------- | ---- |
| POST   | `/categories` | No   |
| GET    | `/categories` | No   |

### Comments

| Method | Endpoint                    | Auth |
| ------ | --------------------------- | ---- |
| POST   | `/posts/{post_id}/comments` | Yes  |
| GET    | `/posts/{post_id}/comments` | No   |
| PATCH  | `/comments/{comment_id}`    | Yes  |
| DELETE | `/comments/{comment_id}`    | Yes  |

Users can only update or delete their own comments.

## Authentication

The API uses **JWT Bearer authentication**.

After logging in, include the returned access token in the `Authorization` header:

```http
Authorization: Bearer <access_token>
```

Protected endpoints use FastAPI's `get_current_user` dependency to authenticate the request and provide the current user.

## Database Relationships

The main relationships are:

```text
User
├── 1 ──── N Post
└── 1 ──── N Comment

Category
└── 1 ──── N Post

Post
├── N ──── 1 User
├── N ──── 1 Category
└── 1 ──── N Comment

Comment
├── N ──── 1 User
└── N ──── 1 Post
```

Related records are handled according to the cascade rules configured in the SQLAlchemy models.

## Testing

Make sure the test PostgreSQL container is running:

```bash
docker compose up -d test-db
```

Run all tests:

```bash
uv run pytest
```

Run tests with verbose output:

```bash
uv run pytest -v
```

Run only comment tests:

```bash
uv run pytest tests/test_comments.py -v
```

## Test Coverage

Run tests with coverage:

```bash
uv run pytest --cov --cov-report=term-missing
```

Generate an HTML coverage report:

```bash
uv run pytest --cov --cov-report=html
```

The generated report will be available at:

```text
htmlcov/index.html
```

## Development Philosophy

This project intentionally keeps the architecture simple.

It uses:

* FastAPI dependencies
* SQLAlchemy models
* Pydantic schemas
* API routers

without introducing unnecessary service or repository layers.

The goal is to keep the codebase:

* Easy to understand
* Easy to test
* Async from the database layer to the API
* Easy to extend
* Free from unnecessary abstractions

As the application grows, additional architectural layers can be introduced when they provide real value.

## License

This project is licensed under the MIT License.
