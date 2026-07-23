"""
OTP Service — Tạo, gửi và xác minh mã OTP 4 chữ số qua Gmail bằng Django ORM local.
"""

import random
import string
from datetime import datetime, timezone, timedelta
from django.core.mail import send_mail
from django.conf import settings
from apps.authentication.models import OTPCode


def create_and_send_otp(email: str, invitation_token: str) -> dict:
    """Tạo OTP mới 4 chữ số và gửi qua Gmail."""
    try:
        # Xóa các OTP cũ của email này
        OTPCode.objects.filter(email=email).delete()

        # Sinh OTP 4 chữ số
        code = ''.join(random.choices(string.digits, k=4))
        OTPCode.objects.create(email=email, code=code)

        _send_otp_email(email, code)
        return {'success': True, 'message': f'Mã OTP đã gửi tới {email}. Kiểm tra cả hòm thư Spam.'}

    except Exception as e:
        return {'success': False, 'error': f'Lỗi gửi OTP: {str(e)}'}


def verify_otp(email: str, code: str) -> dict:
    """Xác minh mã OTP 4 chữ số."""
    try:
        otp = OTPCode.objects.filter(email=email, code=code).first()
        if not otp:
            return {'valid': False, 'message': 'Mã OTP không đúng'}

        # Đã xác minh thành công -> xóa mã OTP
        otp.delete()
        return {'valid': True}

    except Exception:
        return {'valid': False, 'message': 'Lỗi xác minh, vui lòng thử lại'}


def _send_otp_email(email: str, code: str) -> None:
    """Gửi email chứa mã OTP."""
    app = getattr(settings, 'APP_NAME', 'WebNoiBO')
    send_mail(
        subject=f'[{app}] Mã xác nhận: {code}',
        message=f"Mã xác nhận đăng ký tài khoản {app} của bạn là:\n\n    {code}\n\nMã có hiệu lực trong 10 phút.\n\nTrân trọng,\n{app} Team",
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'webnoibo@gmail.com'),
        recipient_list=[email],
        fail_silently=True,
    )
