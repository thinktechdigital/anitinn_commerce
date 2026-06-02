# Anitinn Django Project

Django integration of the Anitinn HTML/CSS/JS frontend (20 pages).

## Setup
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000/

## Structure
- `anitinn/` – Django project (settings, root urls, wsgi/asgi)
- `pages/` – Django app holding views + URL map for all 20 pages
- `pages/templates/pages/` – Converted HTML templates (extend `base.html`)
- `pages/templates/base.html` – Shared layout (head, fonts, Tailwind CDN, blocks)
- `static/` – Place for local CSS/JS/images (currently the templates use CDN Tailwind + remote images, so this is empty by default)
- `media/` – User uploads (configured via MEDIA_URL/MEDIA_ROOT)

## URL map
Each HTML file maps to a clean route, e.g.
- `/` → Vendor Dashboard (01)
- `/marketplace/` → Marketplace Homepage (02)
- `/catalog/` → Product Catalog (03)
- ... see `pages/urls.py` for the full list.

## Notes / Remaining work
- Tailwind is loaded via CDN (matches original). For production, install Tailwind CLI and compile to `static/css/`.
- Forms in the original HTML are static. Add Django `forms.Form` / `ModelForm` + POST views where you need persistence.
- No models defined yet – add them under `pages/models.py` when wiring real data.
- All CSRF tokens should be added to any form you make functional: `{% csrf_token %}`.
