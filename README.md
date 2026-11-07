# Customer Support Ticket Management System

A full-stack Customer Support Ticket Management System built using **FastAPI, Python, SQLAlchemy, SQLite, HTML, CSS and JavaScript**. The application provides secure authentication, role-based access control, ticket management, agent assignment and customer-agent communication.

## Project Overview

The Customer Support Ticket Management System helps customers raise support requests and track their progress. Support agents can manage assigned tickets, respond to customers and update ticket statuses. Administrators can oversee tickets and assign them to support agents.

## Technologies Used

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- JWT Authentication
- Passlib
- Bcrypt

### Frontend
- HTML5
- CSS3
- JavaScript
- Fetch API

### Tools
- Visual Studio Code
- Swagger UI
- Uvicorn
- Git and GitHub

## Features

### 1. User Authentication
- User registration and login.
- Password hashing using Bcrypt.
- JWT-based authentication.
- Protected API endpoints.
- Token verification and expiration.

### 2. Role-Based Access Control
The application supports three user roles:

- **Customer:** Create tickets, view personal tickets and communicate through comments.
- **Support Agent:** View assigned tickets, update ticket statuses and respond to customers.
- **Admin:** Access all tickets, manage ticket assignments and access administrative functionality.

### 3. Ticket Management
- Create support tickets.
- Retrieve all accessible tickets.
- Retrieve individual ticket details.
- Update ticket information.
- Delete tickets.
- Track ticket ownership.

### 4. Ticket Assignment
- Administrators can assign tickets to support agents.
- Agents can access their assigned tickets.
- Ticket access is controlled based on user roles.

### 5. Ticket Status Management
Tickets support the following statuses:

- Open
- In Progress
- Resolved
- Closed

### 6. Comments and Communication
- Customers and support agents can add comments to tickets.
- Retrieve ticket conversations.
- Store the comment author and creation timestamp.
- Restrict comment access based on ticket permissions.

### 7. Search, Filtering and Pagination
- Search tickets by title.
- Filter tickets by status.
- Filter tickets by priority.
- Retrieve tickets using pagination.
- Sort tickets by creation date.

### 8. Database Management
- SQLAlchemy ORM for database operations.
- SQLite database for data storage.
- Foreign key relationships between users, tickets and comments.
- Automatic creation and update timestamps.

## Project Structure

```text
support-ticket-api/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── config.js
│
├── main.py
├── models.py
├── schemas.py
├── database.py
├── requirements.txt
├── .env
├── .gitignore
├── tickets.db
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd support-ticket-api
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_secure_secret_key
```

Use a strong secret key and never commit your `.env` file to GitHub.

### 5. Start the Backend Server

```bash
uvicorn main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

### 6. Access API Documentation

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

## Running the Frontend

Open a separate terminal and navigate to the frontend folder:

```bash
cd frontend
```

Start a local static server:

```bash
python -m http.server 5500
```

Open the application:

```text
http://127.0.0.1:5500
```

Configure the backend URL in `frontend/config.js`:

```javascript
window.APP_CONFIG = {
    API_BASE_URL: "http://127.0.0.1:8000"
};
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register` | Register a new user |
| POST | `/login` | Authenticate a user |
| GET | `/users/me` | Retrieve logged-in user details |
| POST | `/tickets` | Create a ticket |
| GET | `/tickets` | Retrieve accessible tickets |
| GET | `/tickets/{ticket_id}` | Retrieve ticket details |
| PUT | `/tickets/{ticket_id}` | Update a ticket |
| DELETE | `/tickets/{ticket_id}` | Delete a ticket |
| PUT | `/tickets/{ticket_id}/assign` | Assign ticket to an agent |
| POST | `/tickets/{ticket_id}/comments` | Add a comment |
| GET | `/tickets/{ticket_id}/comments` | Retrieve ticket comments |
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/agent/dashboard` | Agent dashboard |

## Authentication and Security

- Passwords are stored as hashes rather than plain text.
- JWT tokens are used to authenticate protected requests.
- Role-based dependencies restrict access to administrative and agent functionality.
- Ticket ownership and assignment are checked before allowing access.
- Environment variables are used to store the JWT secret key.

## Future Enhancements

- Automated API testing using Pytest.
- PostgreSQL database integration.
- Alembic database migrations.
- Email notifications for ticket updates.
- File attachments for support requests.
- Advanced dashboard analytics.
- Deployment with persistent database storage.
- Improved frontend validation and accessibility.

## Deployment

The application can be deployed using separate frontend and backend hosting services.

- **Frontend:** Netlify or Vercel.
- **Backend:** Render or another Python-compatible hosting platform.
- **Database:** PostgreSQL for persistent hosted data.

CORS must be configured to allow requests from the deployed frontend domain.

Deployment and production testing are planned as the final project phase.

## Author

**Kaleru Yuvaraj**

B.Tech Computer Science and Business Systems

## Project Objective

The objective of this project is to develop a secure and organised customer support platform that demonstrates practical implementation of REST APIs, backend development, database integration, authentication, authorization and frontend-backend communication.