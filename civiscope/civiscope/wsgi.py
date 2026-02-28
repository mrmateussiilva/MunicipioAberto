"""WSGI config for civiscope project."""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "civiscope.settings.dev")

application = get_wsgi_application()
