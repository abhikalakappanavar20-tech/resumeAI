import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')

import django
django.setup()

from django.core.management import call_command

try:
    call_command('migrate', interactive=False, verbosity=0)
except Exception as e:
    print(f"[Startup] Migrate error: {e}")

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
