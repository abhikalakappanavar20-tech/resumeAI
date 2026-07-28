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

def run_migrations():
    try:
        call_command('migrate', interactive=False, verbosity=0)
        return
    except Exception as e:
        msg = str(e)
        if 'applied before its dependency' in msg:
            try:
                call_command('migrate', 'accounts', '--fake', verbosity=0)
                call_command('migrate', interactive=False, verbosity=0)
                return
            except Exception:
                pass
        print(f"[Startup] Migrate error: {e}")

run_migrations()

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
