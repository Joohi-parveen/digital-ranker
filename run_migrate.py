import os
import django
from django.core.management import call_command

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
django.setup()

# Execute migrate command
print("Starting database migrations...")
call_command('migrate')
print("Database migrations completed successfully!")
