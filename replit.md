# ArqueoTrack - Archaeological Site Management System

## Overview

ArqueoTrack is a web-based archaeological site management platform built with Flask (Python). It allows archaeologists and research teams to document, organize, and manage archaeological sites (yacimientos), findings (hallazgos), sectors, project phases, timeline events, and team collaboration through an invitation system. The project was originally created for the First Lego League 2026 competition. The interface is entirely in Spanish.

Key capabilities include:
- User registration and authentication
- CRUD for archaeological sites with GPS coordinates and GeoJSON polygon support
- Findings management with unique 10-character alphanumeric access codes
- Site subdivision into sectors with polygon visualization
- Project phase tracking (planning, excavation, analysis, etc.)
- Timeline event logging
- Role-based collaboration via invitation system (visualizador, editor, colaborador, asistente)
- Interactive maps using Leaflet.js with polygon drawing
- Photo uploads for findings
- Code-based finding search

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Framework**: Flask (Python) using the application factory pattern (`create_app()` in `app/__init__.py`)
- **Entry point**: `run.py` creates and runs the Flask app. It includes auto-setup logic for Replit (creates upload directory, initializes database tables)
- **Pattern**: Blueprint-based modular architecture. Blueprints are registered in `app/__init__.py` and live under `app/blueprints/`:
  - `auth` — Registration, login, logout
  - `main` — Landing page, dashboard, profile, code search
  - `yacimiento` — Archaeological site CRUD
  - `hallazgo` — Findings CRUD with unique alphanumeric codes and photo uploads
  - `sector` — Site subdivision management
  - `fase` — Project phase tracking
  - `evento` — Timeline event logging
  - `invitacion` — Collaboration invitations with role-based access

### Directory Structure
- `app/` — Application package (factory, extensions, blueprints, models, forms, utils)
- `app/models/` — SQLAlchemy models (8 models)
- `app/blueprints/` — Route handlers organized by feature
- `templates/` — Jinja2 templates (outside `app` package, configured via absolute path)
- `static/` — CSS and JavaScript files (outside `app` package)
- `uploads/` — User-uploaded files (photos)
- `config.py` — Application configuration
- `documentation/` — Project documentation and planning

### Data Layer
- **ORM**: Flask-SQLAlchemy with SQLAlchemy
- **Database**: SQLite (`arqueotrack.db`) stored in the project root. Models are ORM-based and portable to other databases.
- **Database initialization**: Tables auto-created via `db.create_all()` in the app factory and in the Replit setup function
- **Models** (in `app/models/`):
  - `Usuario` — Users with bcrypt password hashing, Flask-Login integration, role-based permissions
  - `Yacimiento` — Archaeological sites with coordinates, GeoJSON polygons, area, dates
  - `Hallazgo` — Findings with unique 10-char alphanumeric codes, photos, physical characteristics (dimensions, weight, conservation state)
  - `Sector` — Subdivisions within a site with GeoJSON polygon support and color coding
  - `FaseProyecto` — Project phases with status tracking (planificada/en_curso/finalizada), budgets, methodology
  - `Evento` — Timeline events with type, priority, status
  - `Comentario` — Comments on findings
  - `Invitacion` — Collaboration invitations with roles (visualizador/editor/colaborador/asistente)

### Authentication & Authorization
- **Session management**: Flask-Login
- **Password hashing**: Flask-Bcrypt
- **CSRF protection**: Flask-WTF CSRFProtect enabled globally
- **Authorization**: Role-based access per yacimiento through the invitation system. Site owners have full access. Invited users get permissions based on their assigned role. The `Usuario.has_permission()` method checks access for read/create/edit operations.

### Frontend
- **Templates**: Jinja2 templates in `templates/` directory, organized by feature (hallazgos/, fases/, eventos/, invitaciones/, sectores/, yacimientos/, errores/)
- **Base template**: `templates/base.html` provides navigation, flash messages, and layout
- **Static files**: `static/css/styles.css` for styling, multiple JS files in `static/js/`
- **CSS**: Custom stylesheet using CSS custom properties for an earthy/archaeological color theme
- **Maps**: Leaflet.js with OpenStreetMap tiles for interactive maps. Leaflet.Draw for polygon drawing. Custom marker styling.
- **JavaScript modules**:
  - `map.js` — Dashboard map with site markers
  - `polygon-draw.js` — Polygon drawing for sites and sectors
  - `sectores.js` — Sector visualization map
  - `timeline.js` — Timeline animation and filtering
  - `utils.js` — CSRF token helper, alerts, mobile menu toggle

### Forms
- All forms defined in `app/forms.py` using Flask-WTF/WTForms
- Form validation includes custom validators (unique username, unique email)
- File uploads handled via WTForms FileField with allowed extensions check

### Key Design Decisions
1. **Templates and static files outside the `app` package**: Configured via absolute paths in the factory. This was a deliberate choice for simpler template organization.
2. **SQLite for simplicity**: Chosen for easy deployment on Replit without external database services. The ORM-based models can migrate to PostgreSQL if needed.
3. **Blueprint organization by domain**: Each archaeological concept (site, finding, sector, phase, event, invitation) has its own blueprint for separation of concerns.
4. **Unique access codes for findings**: Each hallazgo gets a random 10-character alphanumeric code for quick lookup and sharing between teams.
5. **GeoJSON stored as text**: Polygon geometries are stored as JSON text strings in SQLite rather than using PostGIS, trading spatial query capability for deployment simplicity.

## External Dependencies

### Python Packages (from requirements.txt)
- **Flask ecosystem**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF, Flask-Migrate
- **Database**: SQLAlchemy (with SQLite backend)
- **Forms**: WTForms, email-validator
- **File handling**: Werkzeug (secure filenames), Pillow (image processing)
- **PDF generation**: ReportLab
- **HTTP**: Requests
- **Environment**: python-dotenv
- **Testing**: pytest, Flask-Testing, coverage, pytest-cov
- **CLI**: Click

### Frontend CDN Dependencies
- **Leaflet.js** (v1.9.4) — Interactive maps loaded from unpkg CDN
- **Leaflet.Draw** — Polygon drawing plugin for Leaflet
- **OpenStreetMap** — Map tile provider (no API key required)

### External Services
- No external APIs or third-party services are currently integrated
- No email service configured (invitations are in-app only)
- No cloud storage (uploads stored locally in `uploads/` directory)
- No external authentication providers

### Database
- SQLite file (`arqueotrack.db`) in project root
- No migrations currently active (tables created via `db.create_all()`)
- Flask-Migrate is in requirements but not yet configured in the app factory