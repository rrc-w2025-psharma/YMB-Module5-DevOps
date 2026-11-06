# Yarrow-Mullein Bank — Module 5 DevOps Project

## Project Overview

This project demonstrates a containerized microservices architecture for Yarrow-Mullein Bank (YMB), developed for COMP-4001 DevOps Module 5 at RRC Polytech.

The application combines a student portfolio frontend, a Python Flask banking backend, a MongoDB database, a JavaScript transactions reporting service, and an NGINX reverse proxy.

## Architecture

The application consists of five Docker services:

| Service | Technology | Purpose |
|---------|------------|---------|
| NGINX | NGINX | Public entry point and reverse proxy |
| Student Portfolio | HTML, CSS, NGINX | Student portfolio and banking navigation |
| Backend | Python, Flask | Registration, login, dashboard, deposits, and withdrawals |
| Transactions | Node.js, Express | Monthly transaction reporting |
| Database | MongoDB 6 | Stores user accounts and transactions |

### Network Architecture

Browser
   |
   v
NGINX Reverse Proxy (localhost:80)
   |
   +-- / --------------------> Student Portfolio
   |
   +-- /api/* ---------------> Flask Backend
   |
   +-- /api/transactions/:id -> Node.js Transactions Service

Flask Backend ------> MongoDB
Transactions -------> MongoDB

All five services communicate through the Docker Compose `ymb-network` bridge network.

Only NGINX publishes a port to the host. Backend, frontend, transactions, and database services communicate internally.

## Features

- Yarrow-Mullein Bank branding
- Student portfolio homepage
- User registration and login
- Banking dashboard
- Deposit functionality
- Withdrawal functionality
- Account balance tracking
- Logout
- Monthly transaction reports in JSON format
- Automated backend testing with GitHub Actions

## Requirements

- Docker Desktop
- Docker Compose
- Git
- Web browser

## Running the Application

From the project root directory:

```bash
docker compose up --build -d
```

Verify all five services:

```bash
docker compose ps
```

Access the application:

- Portfolio: http://localhost/
- Registration: http://localhost/api/register
- Login: http://localhost/api/login
- Dashboard: http://localhost/api/dashboard

The dashboard requires authentication.

To stop the containers:

```bash
docker compose down
```

To inspect NGINX logs:

```bash
docker compose logs nginx
```

To validate the NGINX configuration:

```bash
docker compose exec nginx nginx -t
```

## Transactions API

The JavaScript transactions microservice provides:

```text
GET /api/transactions/:userId
```

The endpoint retrieves transaction records from MongoDB and groups them by month and year.

Example response:

```json
[
  {
    "_id": {
      "month": 11,
      "year": 2026
    },
    "transactions": [
      {
        "type": "deposit",
        "amount": 10000
      },
      {
        "type": "withdrawal",
        "amount": 123
      }
    ]
  }
]
```

**Security limitation:** The current transaction endpoint accepts a MongoDB user ID without independently checking the authenticated banking user. This requires additional authorization controls before production use.

## NGINX Routing

NGINX is the only publicly exposed service.

- `/` routes to the student portfolio.
- `/api/` routes to the Flask banking backend.
- `/api/transactions/:userId` routes to the Node.js reporting service.

Other services are accessible through Docker's internal network rather than published host ports.

## GitHub Actions CI

The workflow is located at:

`.github/workflows/ci.yml`

It runs automatically when changes are pushed to `main` or a pull request targets `main`.

The pipeline:

1. Checks out the repository.
2. Configures Python 3.11.
3. Installs dependencies from `backend/requirements.txt`.
4. Runs automated backend tests using pytest.

The tests use `mongomock` to simulate MongoDB.

The initial GitHub Actions run completed successfully.

## Testing and Verification

The following functionality was manually verified:

- All five containers running
- Successful NGINX configuration validation
- Portfolio and banking routes accessible through NGINX
- Registration, login, deposit, and withdrawal workflows
- Node.js connection to MongoDB
- Monthly transaction API returning JSON
- Successful GitHub Actions backend test workflow

## Development Notes

This is an educational project and not a production banking system.

The Docker Compose configuration contains a development-only Flask secret key. Production deployment would require secure secrets management, HTTPS, additional authorization checks, and further security testing.

## Repository

https://github.com/rrc-w2025-psharma/YMB-Module5-DevOps
