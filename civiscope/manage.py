#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "civiscope.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django nao esta disponivel. Instale as dependencias com `pip install -r requirements.txt`."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
