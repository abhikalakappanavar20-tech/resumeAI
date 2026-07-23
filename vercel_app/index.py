import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')

import django
django.setup()

STATIC_MARKER = '/tmp/.static_collected'
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

if IS_VERCEL and not os.path.exists(STATIC_MARKER):
    try:
        from django.core.management import call_command
        call_command('collectstatic', '--noinput', verbosity=0)
        with open(STATIC_MARKER, 'w') as f:
            f.write('done')
    except Exception:
        pass

try:
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception:
    pass

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
except Exception:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
