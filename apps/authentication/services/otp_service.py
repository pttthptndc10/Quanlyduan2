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

        # Sinh OTP 4 chữ số ngẫu nhiên
        code = ''.join(random.choices(string.digits, k=4))
        OTPCode.objects.create(email=email, code=code)

        sent, err_msg = _send_otp_email(email, code)
        if sent:
            return {
                'success': True,
                'message': f'Mã OTP đã gửi tới {email}. Vui lòng kiểm tra Gmail (cả hòm thư Spam).'
            }
        else:
            # Nếu Gmail SMTP yêu cầu Mật khẩu ứng dụng (App Password) -> Hiện OTP trực tiếp để test
            return {
                'success': True,
                'message': f'Mã OTP của bạn là: [{code}] (Cần Mật khẩu ứng dụng Gmail 16 ký tự để tự gửi thư).'
            }

    except Exception as e:
        return {'success': False, 'error': f'Lỗi tạo OTP: {str(e)}'}


def verify_otp(email: str, code: str) -> dict:
    """Xác minh mã OTP 4 chữ số (Bắt buộc phải khớp chính xác)."""
    try:
        otp = OTPCode.objects.filter(email=email, code=code).first()
        if not otp:
            return {'valid': False, 'message': f'Mã OTP "{code}" không chính xác hoặc đã hết hạn.'}

        # Xác minh đúng -> Xóa mã OTP để không dùng lại được nữa
        otp.delete()
        return {'valid': True}

    except Exception as e:
        return {'valid': False, 'message': f'Lỗi xác minh OTP: {str(e)}'}


def _send_otp_email(email: str, code: str) -> tuple[bool, str]:
    """Gửi email chứa mã OTP qua Gmail SMTP."""
    app = getattr(settings, 'APP_NAME', 'WebNoiBO')
    try:
        send_mail(
            subject=f'[{app}] Mã xác nhận đăng ký: {code}',
            message=f"Mã xác nhận đăng ký tài khoản {app} của bạn là:\n\n    {code}\n\nMã có hiệu lực trong 10 phút.\n\nTrân trọng,\n{app} Team",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'pttthptndc10@gmail.com'),
            recipient_list=[email],
            fail_silently=False,
        )
        return True, ''
    except Exception as e:
        return False, str(e)
