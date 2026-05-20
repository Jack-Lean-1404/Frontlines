# Frontlines Webapp

A browser-based geopolitical strategy platform where players manage nations, military units, resources, diplomacy, and strategic operations through a persistent web dashboard.

---

# Overview

see [setup.md](setup.md) for setting up the project.

## Core Features

- Nation login and authentication system
- Player nation dashboards
- Resource economy and upkeep systems
- Military unit management
- Turn-based gameplay mechanics
- Administrative control panel
- Activity logging and event history
- Database-driven statistics and progression systems

---

# Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python |
| Database | MySQL |
| Hosting | Render |
| IDE | VS Code |
| Database Tooling | MySQL Workbench |
| Version Control | Git + GitHub |

---

# System Architecture

## Frontend

The frontend uses:

- HTML for structure
- CSS for styling
- Vanilla JavaScript for interactivity

### Responsibilities

- Display nation dashboards
- Handle user interaction
- Send API requests
- Display dynamic game data

---

## Backend

The Python backend:

- Handles authentication
- Processes gameplay logic
- Validates player actions
- Communicates with MySQL
- Returns JSON API responses

---

## Database

MySQL stores:

- Users
- Nations
- Military units
- Resources
- Diplomatic relations
- Turn history
- Game statistics

---

# Development Workflow

## Branching Rules

Never commit directly to `main`.

Only jack can do a Pull Request from `development` to `main`

Use branches:

```text
main = live website
development = in progress
```

---

# Commit Naming

Examples:

```bash
git commit -m "Add nation dashboard API"

git commit -m "Fix login session timeout"

git commit -m "Refactor combat calculation service"
```

---

# Coding Standards

## Python

- Use `snake_case`
- Separate routes, services, and database logic

---

## HTML / CSS

- Use semantic HTML
- Keep CSS modular
- Avoid inline styling
- Use reusable components where possible

---

## JavaScript

- Use `camelCase`
- Keep functions focused and modular
- Avoid duplicated logic
- Separate API calls from UI rendering

---

## SQL

- Use lowercase SQL keywords
- Use singular table names
- Define proper foreign keys
- Avoid direct production edits

---

# Deployment

## Render Hosting

The application is deployed using Render.

---

# Deployment Flow

1. Push changes to GitHub
2. Render automatically deploys from `main`
3. Verify deployment logs
4. Test production environment

---

# Production Environment Variables

Configured through the Render dashboard:

```env
DB_HOST=
DB_USER=
DB_PASSWORD=
SECRET_KEY=
API_KEYS=
```

---

# Production Database Rules

Do NOT:

- Modify production schema directly
- Run destructive SQL queries
- Delete rows manually
- Push untested migrations

---

# API Documentation

## Login Endpoint

### Request

```http
POST /api/login
```

### Request Body

```json
{
  "username": "player1",
  "password": "password"
}
```

### Response

```json
{
  "success": true,
  "token": "jwt-token"
}
```

---

# Database Schema Reference

## users

| Column | Type |
|---|---|
| id | INT |
| username | VARCHAR |
| password_hash | VARCHAR |

---

## nations

| Column | Type |
|---|---|
| id | INT |
| nation_name | VARCHAR |
| treasury | BIGINT |

---

# Team Roles

| Role | Responsibility | Name
|---|---|---|
| Project Lead | Architecture and approvals | Jack
| Frontend Developer | UI/UX systems | Brad
| Backend Developer | APIs and gameplay logic | Jack
| Database Administrator | MySQL maintenance | Jack
| Game Designer | Gameplay Decisions | Jack

---

# Important Rules

Contact Jack before:

- Changing database schema
- Modifying authentication systems
- Editing deployment configuration
- Refactoring shared systems
- Modifying production infrastructure