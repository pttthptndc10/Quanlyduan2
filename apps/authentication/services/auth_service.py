"""
Auth Service — Xử lý đăng nhập, đăng xuất, tạo tài khoản qua Supabase Auth.
"""

from .supabase_client import get_supabase_client, get_admin_supabase_client


def login(email: str, password: str) -> dict:
    """
    Đăng nhập qua Supabase Auth.
    Returns: { success, user: {id, email, full_name, role}, access_token, refresh_token }
             hoặc { success: False, error: str }
    """
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        auth_user = result.user
        session = result.session

        if not auth_user:
            return {'success': False, 'error': 'Đăng nhập thất bại'}

        # Lấy thêm thông tin profile từ bảng profiles
        admin = get_admin_supabase_client()
        try:
            profile_res = admin.table('profiles').select('*').eq('id', str(auth_user.id)).execute()
            profiles_list = profile_res.data or []
        except Exception:
            profiles_list = []

        if not profiles_list:
            # Tự động tạo profile nếu chưa có
            user_meta = auth_user.user_metadata or {}
            full_name = user_meta.get('full_name') or auth_user.email.split('@')[0]
            new_profile = {
                'id': str(auth_user.id),
                'full_name': full_name,
                'role': 'admin' if 'admin' in auth_user.email else 'member',
                'status': 'active',
            }
            try:
                admin.table('profiles').upsert(new_profile).execute()
                profile = new_profile
            except Exception:
                profile = new_profile
        else:
            profile = profiles_list[0]

        # Kiểm tra tài khoản bị khóa
        if profile.get('status') == 'inactive':
            return {'success': False, 'error': 'Tài khoản đã bị vô hiệu hóa. Liên hệ admin.'}

        return {
            'success': True,
            'user': {
                'id': str(auth_user.id),
                'email': auth_user.email,
                'full_name': profile.get('full_name', ''),
                'role': profile.get('role', 'member'),
                'department': profile.get('department', ''),
            },
            'access_token': session.access_token,
            'refresh_token': session.refresh_token,
        }

    except Exception as e:
        msg = str(e)
        if 'Invalid login credentials' in msg or 'invalid_credentials' in msg.lower():
            return {'success': False, 'error': 'Email hoặc mật khẩu không đúng'}
        from django.conf import settings
        if settings.DEBUG:
            return {'success': False, 'error': f'Lỗi hệ thống: {msg}'}
        return {'success': False, 'error': 'Lỗi hệ thống, vui lòng thử lại'}


def logout(access_token: str = None) -> None:
    """Đăng xuất khỏi Supabase, xóa session server-side."""
    try:
        get_supabase_client().auth.sign_out()
    except Exception:
        pass


def register(email: str, password: str, full_name: str, invitation_token: str) -> dict:
    """
    Tạo tài khoản mới qua Supabase Admin API.
    Chỉ gọi sau khi đã xác minh invitation + OTP hợp lệ.
    """
    try:
        admin = get_admin_supabase_client()

        # Tạo user trong Supabase Auth (không cần xác nhận email)
        result = admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name}
        })

        if not result.user:
            return {'success': False, 'error': 'Không thể tạo tài khoản'}

        user_id = str(result.user.id)

        # Tạo profile (trigger handle_new_user có thể đã tạo, dùng upsert cho an toàn)
        admin.table('profiles').upsert({
            'id': user_id,
            'full_name': full_name,
            'role': 'member',
            'status': 'active',
        }).execute()

        # Đánh dấu invitation đã dùng
        from .invitation_service import mark_invitation_used
        mark_invitation_used(invitation_token)

        return {'success': True}

    except Exception as e:
        msg = str(e)
        if 'already' in msg.lower():
            return {'success': False, 'error': 'Email này đã có tài khoản'}
        return {'success': False, 'error': f'Lỗi tạo tài khoản: {msg}'}
