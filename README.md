# Team Project & Work Management Platform

A web-based project and task management application built with Django. The project is designed to help teams organize projects, manage tasks, and track work progress.

## Features

- **User Authentication:** User registration and login.
- **Project Management:** Create and view projects.
- **Project Membership:** Associate users with projects and manage project roles.
- **Task Management:** Organize tasks under projects.
- **Task Filtering:** Filter tasks by status and priority.
- **Task Tracking:** View task deadlines and identify overdue tasks.
- **Access Control:** Restrict project access to authorized owners and members.

## Tech Stack

- **Backend:** Python, Django
- **Database:** SQLite
- **Frontend:** HTML, CSS, Django Templates
- **Version Control:** Git and GitHub

## Project Structure

```text
team-management/
├── accounts/
├── config/
├── projects/
├── tasks/
├── manage.py
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 or compatible Python version
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/team-management.git
cd team-management
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the required packages for your project. If a `requirements.txt` file is available:

```powershell
pip install -r requirements.txt
```

### 4. Apply database migrations

```powershell
python manage.py migrate
```

### 5. Create an administrator account

```powershell
python manage.py createsuperuser
```

### 6. Start the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Learning Objectives

This project demonstrates practical experience with Django fundamentals, database relationships, ORM queries, authentication, authorization, templates, and CRUD operations.

## Future Improvements

- Automated tests for project and task permissions
- Improved UI and responsive design
- Team collaboration and notifications
- Deployment to a production hosting platform

## Author

**Nitheeshwaran J**

GitHub: https://github.com/NitheeshwaranJ

---

*This project is being developed as a learning project to strengthen Django and Python backend development skills.*
