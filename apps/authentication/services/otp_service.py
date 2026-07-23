"""
OTP Service — Tạo, gửi và xác minh mã OTP 4 chữ số qua Gmail.
OTP hợp lệ 10 phút. Gửi lại tự động vô hiệu OTP cũ.
"""

import random
import string
from datetime import datetime, timezone, timedelta

from django.core.mail import send_mail
from django.conf import settings

from .supabase_client import get_admin_supabase_client


def create_and_send_otp(email: str, invitation_token: str) -> dict:
    """Tạo OTP mới và gửi tới email. OTP cũ bị vô hiệu ngay."""
    try:
        db = get_admin_supabase_client()

        # Vô hiệu hóa tất cả OTP cũ chưa dùng
        db.table('otp_codes').update({'used': True}) \
            .eq('email', email).eq('used', False).execute()

        # Sinh OTP 4 chữ số
        code = ''.join(random.choices(string.digits, k=4))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        res = db.table('otp_codes').insert({
            'email': email,
            'code': code,
            'invitation_token': invitation_token,
            'expires_at': expires_at.isoformat(),
            'used': False,
        }).execute()

        if not res.data:
            return {'success': False, 'error': 'Không thể tạo mã OTP'}

        _send_otp_email(email, code)
        return {'success': True, 'message': f'Mã OTP đã gửi tới {email}. Kiểm tra cả thư mục Spam.'}

    except Exception as e:
        return {'success': False, 'error': f'Lỗi gửi OTP: {str(e)}'}


def verify_otp(email: str, code: str) -> dict:
    """Xác minh OTP. Nếu đúng, đánh dấu đã dùng và trả về valid=True."""
    try:
        db = get_admin_supabase_client()
        res = db.table('otp_codes').select('*') \
            .eq('email', email).eq('code', code).eq('used', False) \
            .order('created_at', desc=True).limit(1).execute()

        if not res.data:
            return {'valid': False, 'message': 'Mã OTP không đúng'}

        otp = res.data[0]
        exp = datetime.fromisoformat(otp['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > exp:
            return {'valid': False, 'message': 'Mã OTP đã hết hạn. Nhấn "Gửi lại mã".'}

        # Đánh dấu đã dùng
        db.table('otp_codes').update({'used': True}).eq('id', otp['id']).execute()
        return {'valid': True}

    except Exception:
        return {'valid': False, 'message': 'Lỗi xác minh, vui lòng thử lại'}


def _send_otp_email(email: str, code: str) -> None:
    """Gửi email chứa mã OTP."""
    app = settings.APP_NAME
    send_mail(
        subject=f'[{app}] Mã xác nhận: {code}',
        message=f"Mã xác nhận của bạn:\n\n    {code}\n\nHiệu lực 10 phút.\n\nTeam {app}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
