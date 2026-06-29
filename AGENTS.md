# AGENTS.md

## Purpose
This file helps AI coding agents understand the Clinica_Veterinaria Django backend and get productive quickly.

## Project overview
- Django backend for a veterinary clinic management system.
- Built with Python 3.12 and Django 4.2.
- Uses MySQL in `clinica_veterinaria_proyecto/settings.py`.
- Primary apps:
  - `gestion_veterinaria` (main clinic workflow, operators, patients, clinical history)
  - `pagos` (billing and payment flow)
  - `productos` (product catalog)
- Templates and static assets are stored under `gestion_veterinaria/templates` and `gestion_veterinaria/static`.

## Recommended setup
1. `python -m venv venv`
2. `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Configure MySQL credentials in `clinica_veterinaria_proyecto/settings.py`
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py runserver`

## Key files and entry points
- `manage.py` — Django CLI entrypoint.
- `clinica_veterinaria_proyecto/settings.py` — database, installed apps, template/static config, auth redirects.
- `clinica_veterinaria_proyecto/urls.py` — root URL routing, auth views, includes `gestion_veterinaria` and `pagos`.
- `gestion_veterinaria/urls.py` — clinic workflow routes and role-based dashboards.
- `pagos/urls.py` — billing/payment routes.
- `README.md` — project description, install/run instructions and architecture summary.

## Conventions
- Views and routes largely use Spanish names and comments.
- Keep UI and route names aligned with `name='...'` values in `urls.py`.
- Most views are class-based Django generic views with `LoginRequiredMixin`.
- Avoid changing migration files unless required for schema updates.

## Notes for provider-related requests
- The codebase currently has no `provider` module or explicit provider/service pattern.
- If a task mentions `provider`, ask the user whether they mean a new external service integration, a Django dependency provider, or some specific domain concept.
- Do not assume an existing third-party provider architecture is already present.

## Useful guidance for agents
- Prefer small focused changes over broad refactors in this academic project.
- Preserve Spanish names and comments when editing the domain logic.
- Use the existing README install and run commands as the authoritative development workflow.
- When adding new functionality, update routing in `clinica_veterinaria_proyecto/urls.py` and the relevant app `urls.py`.
- For database work, use Django models and migrations rather than direct SQL.

## What agents should avoid
- Do not commit actual credentials or secret keys from `settings.py` into public output.
- Do not remove or rewrite the entire project structure without user approval.
- Do not assume a frontend framework beyond Django templates.
