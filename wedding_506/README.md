# Organization Management Service

A multi-tenant organization management service built with FastAPI and MongoDB, featuring JWT authentication and dynamic database collection creation.

## Features

- Multi-tenant architecture with isolated data per organization
- JWT-based authentication
- Dynamic MongoDB collection creation for each organization
- RESTful API endpoints for organization management
- Admin user management
- Secure password hashing with bcrypt

## Prerequisites

- Python 3.8+
- MongoDB server (local or remote)
- pip (Python package manager)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd organization-management-service
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Copy the `.env.example` file to `.env` and update the values:
   ```bash
   cp .env.example .env
   ```

   Update the `.env` file with your configuration:
   ```
   # Application
   DEBUG=True
   
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017/
   MASTER_DB_NAME=org_master_db
   
   # JWT
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

## Running the Application

1. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/admin/login` - Authenticate and get access token
- `GET /api/admin/me` - Get current user information

### Organization Management
- `POST /api/org/create` - Create a new organization
- `GET /api/org/get/{organization_name}` - Get organization details
- `PUT /api/org/update/{organization_name}` - Update organization
- `DELETE /api/org/delete/{organization_name}` - Delete organization

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI application setup
│   ├── config.py             # Application configuration
│   ├── database.py           # Database connection and models
│   ├── auth.py               # Authentication utilities
│   ├── models.py             # Pydantic models
│   └── api/
│       ├── __init__.py
│       ├── auth.py           # Authentication endpoints
│       └── organization.py   # Organization management endpoints
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Testing

To run the tests:

```bash
# Install test dependencies
pip install pytest httpx pytest-asyncio

# Run tests
pytest
```

## Deployment

For production deployment, consider using:

1. **ASGI Server**: Gunicorn with Uvicorn workers
   ```bash
   pip install gunicorn
   gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **Containerization** (Docker)
   ```bash
   docker build -t organization-service .
   docker run -d -p 8000:8000 organization-service
   ```

3. **Environment Variables**
   Make sure to set appropriate production values in your environment variables.

## Security Considerations

- Always use HTTPS in production
- Keep your `SECRET_KEY` secure and never commit it to version control
- Implement rate limiting for authentication endpoints
- Regularly update dependencies for security patches
- Use proper CORS settings in production
