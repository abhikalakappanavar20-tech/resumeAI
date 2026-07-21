import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')

# Initialize Django
import django
django.setup()

# Run migrations on cold start (Vercel serverless)
try:
    from django.core.management import call_command
    call_command('migrate', '--run-syncdb', verbosity=0)
except Exception:
    pass

# Create superuser if needed
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@resumeiq.com', 'AdminPass123!')
except Exception:
    pass

# Import the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
