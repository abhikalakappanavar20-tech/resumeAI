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

def reset_and_migrate():
    try:
        from django.conf import settings
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'postgresql' in db_engine or 'psycopg' in db_engine:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
            call_command('migrate', interactive=False, verbosity=0)
            print("[Startup] Migrate succeeded after full reset")
        else:
            call_command('migrate', interactive=False, verbosity=0)
    except Exception as e:
        print(f"[Startup] Full reset failed: {e}")

reset_and_migrate()

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
