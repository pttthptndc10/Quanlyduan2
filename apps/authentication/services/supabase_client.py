"""
Supabase Client Factory.
- get_supabase_client(request=None): dùng anon key + attach access_token từ session nếu có.
- get_admin_supabase_client(request=None): client cho backend operations, tự động gắn token người dùng để pass RLS.
"""

from supabase import create_client, Client
from django.conf import settings


def get_supabase_client(request=None) -> Client:
    """Client cho client-side / public operations."""
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    if request and hasattr(request, 'session') and request.session.get('access_token'):
        client.postgrest.auth(request.session['access_token'])
    return client


def get_admin_supabase_client(request=None) -> Client:
    """Client cho backend operations, tự động gắn access_token từ session để qua RLS."""
    key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    client = create_client(settings.SUPABASE_URL, key)
    if request and hasattr(request, 'session') and request.session.get('access_token'):
        client.postgrest.auth(request.session['access_token'])
    return client
