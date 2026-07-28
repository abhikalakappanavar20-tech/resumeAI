import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')

import django
django.setup()

from django.core.management import call_command
from django.db import connection

def migrate_clean():
    try:
        call_command('migrate', interactive=False, verbosity=0)
        return
    except Exception as e:
        msg = str(e)
        print(f"[Startup] Migrate error: {msg}")
        if 'applied before its dependency' in msg or 'relation' in msg:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("DROP TABLE IF EXISTS django_migrations CASCADE")
                call_command('migrate', '--fake-initial', interactive=False, verbosity=0)
                print("[Startup] Migrate succeeded after reset")
            except Exception as e2:
                print(f"[Startup] Migrate reset failed: {e2}")

migrate_clean()

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
