"""
Azure-specific settings for SmartShop Django application
Import this in settings.py when running on Azure
"""
import os
from decouple import config

# Azure Storage Configuration for Static and Media Files
AZURE_STORAGE_ACCOUNT_NAME = config('AZURE_STORAGE_ACCOUNT_NAME', default='')
AZURE_STORAGE_ACCOUNT_KEY = config('AZURE_STORAGE_ACCOUNT_KEY', default='')

if AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY:
    # Use Azure Storage for static and media files
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    
    AZURE_ACCOUNT_NAME = AZURE_STORAGE_ACCOUNT_NAME
    AZURE_ACCOUNT_KEY = AZURE_STORAGE_ACCOUNT_KEY
    AZURE_CONTAINER = 'media'
    AZURE_STATIC_CONTAINER = 'static'
    
    # URLs for Azure Storage
    STATIC_URL = f'https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/static/'
    MEDIA_URL = f'https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/media/'

# ALLOWED_HOSTS for Azure
AZURE_ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
if AZURE_ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(AZURE_ALLOWED_HOSTS)

# Security settings for production
if not config('DEBUG', default=False, cast=bool):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
