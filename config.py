"""
default config, used as fallback if /instance/config.py is missing
"""

import os
import secrets

SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(16)