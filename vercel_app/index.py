import os
import sys
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')

import django
django.setup()

IS_VERCEL = os.environ.get('VERCEL', '') == '1'

# Run migrations once on cold start
try:
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception as e:
    logger.warning(f"Migration failed: {e}")

# Seed test users on Vercel (only once per cold start)
if IS_VERCEL:
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = [
            ('testcandidate', 'candidate', 'testcandidate@test.com', 'TestPass123!'),
            ('testrecruiter', 'recruiter', 'testrecruiter@test.com', 'TestPass123!'),
            ('testadmin', 'admin', 'testadmin@test.com', 'TestPass123!'),
        ]
        for username, role, email, password in users:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, email=email, password=password, role=role)
    except Exception as e:
        logger.warning(f"User seeding failed: {e}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
