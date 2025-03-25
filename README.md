# Barbershop User Service

REST API microservice for user management in the barbershop appointment system.

## Features

- User management (create, read, update, delete)
- JWT authentication
- Dockerized with SQLite database

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy (with SQLite)
- JWT Authentication
- Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running the Service

1. Clone the repository:

   ```
   git clone https://github.com/your-org/barbershop-user-service.git
   cd barbershop-user-service
   ```

2. Start the service:
   ```
   docker-compose up
   ```

This will run the service in the foreground with logs printed to the console. To run in detached mode:

```
docker-compose up -d
```

3. The API will be available at http://localhost:8000
   - API documentation: http://localhost:8000/docs

## API Endpoints

### Authentication

- `POST /api/auth/login` - OAuth2 compatible token login
- `POST /api/auth/login/email` - Login with email and password

### Users

- `GET /api/users/` - List all users (requires authentication)
- `POST /api/users/` - Create a new user (public endpoint)
- `GET /api/users/me` - Get current user information (requires authentication)
- `GET /api/users/{user_id}` - Get specific user information (requires authentication)
- `PUT /api/users/{user_id}` - Update user information (requires authentication)
- `DELETE /api/users/{user_id}` - Delete a user (requires barber role)
- `GET /api/users/barbers/` - List all barbers (public endpoint)
