import os
import django
from django.core.management import call_command

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
django.setup()

# Execute collectstatic command
print("Starting collectstatic...")
call_command('collectstatic', '--noinput')
print("collectstatic completed successfully!")
