# ArqueoTrack - Archaeological Site Management System

## Overview

ArqueoTrack is a web-based archaeological site management platform built for the First Lego League 2026 competition. It allows archaeologists and research teams to document, organize, and manage archaeological excavation sites ("yacimientos"), record findings ("hallazgos") with unique access codes, collaborate through invitations, track project phases, log events on a timeline, and visualize site locations on interactive maps. The interface is entirely in Spanish.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Framework**: Flask (Python) with the application factory pattern (`create_app()`)
- **Entry points**: `main.py` and `run.py` both create and run the Flask app. Use `main.py` as the primary entry point.
- **Pattern**: Blueprint-based modular architecture. The app is split into multiple blueprints under `app/blueprints/`:
  - `auth` — Registration, login, logout
  - `main` — Landing page, dashboard, profile, code search
  - `yacimiento` — Archaeological site CRUD
  - `hallazgo` — Findings CRUD with unique alphanumeric codes
  - `sector` — Site subdivision management
  - `fase` — Project phase tracking
  - `evento` — Timeline event logging
  - `invitacion` — Collaboration invitations with role-based access

### Data Layer
- **ORM**: Flask-SQLAlchemy with SQLAlchemy
- **Database**: SQLite (`arqueotrack.db`) — stored in the project root. No Postgres currently configured, but models are ORM-based and could migrate.
- **Models** (in `app/models/`):
  - `Usuario` — Users with bcrypt password hashing, Flask-Login integration
  - `Yacimiento` — Archaeological sites with coordinates, GeoJSON polygons, area
  - `Hallazgo` — Findings with unique 10-char alphanumeric codes, photos, physical characteristics
  - `Sector` — Subdivisions within a site, with GeoJSON polygon support
  - `FaseProyecto` — Project phases with status tracking (planificada/en_curso/finalizada)
  - `Evento` — Timeline events with type, priority, status
  - `Comentario` — Comments on findings
  - `Invitacion` — Collaboration invitations with roles (visualizador/editor/colaborador/asistente)
- **Database initialization**: Tables are auto-created via `db.create_all()` in the app factory

### Authentication & Authorization
- **Auth**: Flask-Login for session management, Flask-Bcrypt for password hashing
- **CSRF**: Flask-WTF CSRFProtect enabled globally
- **Authorization**: Role-based access per yacimiento through the invitation system. Owners have full access; invited users have permissions based on their assigned role.

### Frontend
- **Templates**: Jinja2 templates in `templates/` directory (outside the `app` package — configured via absolute path in the factory)
- **Static files**: CSS and JS in `static/` directory (also outside `app` package)
- **CSS**: Single custom stylesheet (`static/css/styles.css`) with CSS custom properties for theming (earthy/archaeological color palette)
- **Maps**: Leaflet.js for interactive maps with OpenStreetMap tiles. Supports marker placement, polygon drawing (via Leaflet.Draw), and sector visualization
- **JavaScript modules**:
  - `map.js` — Dashboard map with site markers
  - `polygon-draw.js` — Polygon drawing for sites and sectors
  - `sectores.js` — Advanced sector visualization
  - `timeline.js` — Timeline animation and filtering
  - `utils.js` — CSRF token helper, alert management, mobile menu

### Forms
- **Library**: Flask-WTF with WTForms
- **All forms** defined in `app/forms.py` — registration, login, site creation, finding creation, invitations, phases, events, sectors

### File Uploads
- **Storage**: Local filesystem in `uploads/` directory
- **Limit**: 16MB max file size
- **Allowed types**: PNG, JPG, JPEG, GIF, WebP
- **Processing**: Pillow (PIL) available for image processing

### Key Design Decisions
1. **Templates/static outside app package**: The Flask app factory explicitly sets `template_folder` and `static_folder` to project root directories, not inside `app/`
2. **Spanish language throughout**: All UI, form labels, flash messages, and variable names are in Spanish
3. **Unique finding codes**: Each hallazgo gets a random 10-character alphanumeric code for quick lookup
4. **GeoJSON as text**: Polygon geometries stored as plain text GeoJSON strings (no PostGIS) for SQLite compatibility
5. **No migration system active**: Flask-Migrate is in requirements but not configured in the app factory — tables are created via `db.create_all()`

## External Dependencies

### Python Packages (key ones)
- `flask` — Web framework
- `flask-sqlalchemy` / `sqlalchemy` — ORM and database
- `flask-login` — Session/auth management
- `flask-bcrypt` — Password hashing
- `flask-wtf` / `wtforms` — Form handling and CSRF
- `email-validator` — Email field validation
- `reportlab` — PDF report generation
- `Pillow` — Image processing
- `flask-migrate` — Database migrations (installed but not actively used)
- `python-dotenv` — Environment variable loading
- `requests` — HTTP client
- `pytest` / `coverage` / `pytest-cov` / `flask-testing` — Testing tools

### Frontend CDN Dependencies
- **Leaflet.js** (v1.9.4) — Interactive maps via unpkg CDN
- **Leaflet.Draw** — Polygon drawing plugin (referenced in polygon-draw.js)
- **OpenStreetMap** — Map tile provider

### No External Services
- No external APIs, no email service, no cloud storage, no external authentication providers currently configured
- Database is local SQLite file