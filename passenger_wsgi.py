import os
import sys

# ==============================================================================
# Phusion Passenger Virtual Environment Setup for cPanel
# ==============================================================================
# In cPanel, Passenger runs the global Python interpreter by default.
# To force it to use your app's virtual environment, uncomment the block below
# and replace the path with your actual virtual environment Python path.
# You can find this path in cPanel under "Setup Python App".
#
# INTERP = "/home/your_cpanel_username/virtualenv/your_app_directory/3.x/bin/python"
# if sys.executable != INTERP:
#     os.execl(INTERP, INTERP, *sys.argv)
# ==============================================================================

sys.path.insert(0, os.path.dirname(__file__))

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

