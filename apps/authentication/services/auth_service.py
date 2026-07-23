"""
Auth Service — Đăng nhập, Đăng ký và Quản lý tài khoản local.
"""

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from apps.authentication.models import Profile, Invitation


def login(email: str, password: str) -> dict:
    """Đăng nhập người dùng bằng Django ORM."""
    try:
        user = User.objects.filter(email=email).first()
        if not user:
            # Thu mat khau qua username neu email khong tim thay
            user = User.objects.filter(username=email).first()
        if not user:
            return {'success': False, 'error': 'Email hoặc mật khẩu không đúng.'}

        if not user.check_password(password):
            return {'success': False, 'error': 'Email hoặc mật khẩu không đúng.'}

        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={'full_name': user.first_name or email.split('@')[0], 'role': 'member'}
        )

        return {
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': profile.full_name,
                'role': profile.role,
            },
            'access_token': f"session_token_{user.id}"
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def register(email: str, password: str, full_name: str, invitation_token: str) -> dict:
    """Đăng ký tài khoản mới bằng Django ORM từ Lời mời."""
    try:
        invitation = Invitation.objects.filter(token=invitation_token, used=False).first()
        if not invitation:
            return {'success': False, 'error': 'Lời mời không hợp lệ hoặc đã sử dụng.'}

        if User.objects.filter(email=email).exists():
            return {'success': False, 'error': 'Email đã được đăng ký tài khoản.'}

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name
        )

        profile = Profile.objects.create(
            user=user,
            full_name=full_name,
            role=invitation.role,
            status='active'
        )

        invitation.used = True
        invitation.save()

        return {
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': profile.full_name,
                'role': profile.role
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def logout(token=None):
    """Đăng xuất người dùng."""
    pass
