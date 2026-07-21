#!/bin/bash
set -e

echo "Building ResumeIQ for Vercel..."

# Install Python dependencies
pip install -r requirements.txt --quiet

# Run collectstatic
python -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resumeiq.settings')
sys.path.insert(0, '.')
import django
django.setup()
from django.core.management import call_command
call_command('collectstatic', '--noinput', verbosity=0)
print('Static files collected.')
"

echo "Build complete."
