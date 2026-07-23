"""
Middleware xác thực Supabase.
Bảo vệ route cần đăng nhập, điều hướng tự động.
"""

from django.shortcuts import redirect


class SupabaseAuthMiddleware:
    # Route cần đăng nhập
    PROTECTED = [
        '/dashboard/', '/projects/', '/tasks/',
        '/members/', '/reports/', '/settings/', '/auth/invite/',
    ]
    # Route chỉ dành cho chưa đăng nhập
    AUTH_ONLY = ['/login/', '/register/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        uid = request.session.get('user_id')

        if any(path.startswith(p) for p in self.PROTECTED) and not uid:
            return redirect(f'/login/?next={path}')

        if any(path.startswith(p) for p in self.AUTH_ONLY) and uid:
            return redirect('/dashboard/')

        return self.get_response(request)
