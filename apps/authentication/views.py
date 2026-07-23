"""
Authentication Views — Xử lý Đăng nhập, Đăng ký và Quản lý Lời mời.
"""

import json
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.authentication.services import auth_service, invitation_service, otp_service


def root_redirect(request):
    """Điều hướng trang chủ / về /dashboard/ nếu đã đăng nhập hoặc /login/."""
    if request.session.get('user_id'):
        return redirect('/dashboard/')
    return redirect('/login/')


# ─── Đăng nhập ───────────────────────────────────────────────────────────────

def login_view(request):
    if request.session.get('user_id'):
        return redirect('/dashboard/')

    if request.method == 'GET':
        return render(request, 'authentication/login.html')

    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '').strip()

    ctx = {'email': email}

    if not email or not password:
        ctx['error'] = 'Vui lòng nhập đầy đủ Email và Mật khẩu'
        return render(request, 'authentication/login.html', ctx)

    result = auth_service.login(email=email, password=password)

    if result['success']:
        u = result['user']
        request.session.update({
            'user_id': u['id'],
            'user_email': u['email'],
            'user_name': u['full_name'],
            'user_role': u['role'],
            'access_token': result['access_token'],
        })

        next_url = request.GET.get('next')
        if next_url and next_url.startswith('/') and not next_url.startswith('//'):
            return redirect(next_url)
        return redirect('/dashboard/')

    ctx.update({'error': result['error'], 'email': email})
    return render(request, 'authentication/login.html', ctx)


# ─── Đăng xuất ───────────────────────────────────────────────────────────────

def logout_view(request):
    try:
        request.session.flush()
    except Exception:
        pass
    return redirect('/login/')


# ─── Đăng ký qua lời mời ─────────────────────────────────────────────────────

def register_view(request):
    token = request.GET.get('token') or request.POST.get('invitation_token', '')
    email = request.POST.get('email', '').strip()

    # Kiểm tra nếu Email đã đăng ký xong rồi
    if email and User.objects.filter(email=email).exists():
        return render(request, 'authentication/register.html', {
            'token_error': f'Tài khoản {email} đã hoàn tất đăng ký thành công rồi! Vui lòng Đăng nhập để sử dụng.',
            'email': email,
        })

    invitation = None
    if token:
        invitation = invitation_service.get_valid_invitation(token)
    elif email:
        invitation = invitation_service.get_valid_invitation_by_email(email)

    if request.method == 'GET':
        return render(request, 'authentication/register.html', {
            'invitation': invitation, 'token': token or ''
        })

    # POST — xử lý form
    full_name = request.POST.get('full_name', '').strip()
    password = request.POST.get('password', '').strip()
    confirm = request.POST.get('confirm_password', '').strip()
    otp_code = request.POST.get('otp_code', '').strip()

    if not invitation:
        invitation = invitation_service.get_valid_invitation_by_email(email)

    if not invitation:
        return render(request, 'authentication/register.html', {
            'token_error': f'Email {email or ""} chưa nằm trong danh sách Whitelist được Admin mời.',
            'email': email, 'full_name': full_name
        })

    token = invitation['token']
    errors = {}
    if not full_name or len(full_name) < 2:
        errors['full_name'] = 'Họ tên tối thiểu 2 ký tự'
    pwd_err = _check_password(password)
    if pwd_err:
        errors['password'] = pwd_err
    if password and password != confirm:
        errors['confirm_password'] = 'Mật khẩu xác nhận không khớp'
    if not otp_code:
        errors['otp'] = 'Vui lòng nhập mã OTP'
    else:
        otp_res = otp_service.verify_otp(email, otp_code)
        if not otp_res['valid']:
            errors['otp'] = otp_res['message']

    if errors:
        return render(request, 'authentication/register.html', {
            'invitation': invitation, 'token': token,
            'errors': errors, 'full_name': full_name, 'email': email,
        })

    reg = auth_service.register(email=email, password=password,
                                full_name=full_name, invitation_token=token)
    if not reg['success']:
        return render(request, 'authentication/register.html', {
            'invitation': invitation, 'token': token,
            'error': reg['error'], 'full_name': full_name, 'email': email,
        })

    # Tự đăng nhập sau khi đăng ký thành công
    login_res = auth_service.login(email, password)
    if login_res['success']:
        u = login_res['user']
        request.session.update({
            'user_id': u['id'], 'user_email': u['email'],
            'user_name': u['full_name'], 'user_role': u['role'],
        })
    return redirect('/dashboard/')


# ─── AJAX: Gửi OTP ────────────────────────────────────────────────────────────

def send_otp_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        email = data.get('email', '').strip()
    except Exception:
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'}, status=400)

    # Nếu Email đã được tạo tài khoản rồi
    if email and User.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': f'Tài khoản {email} đã đăng ký hoàn tất rồi. Vui lòng quay lại Đăng nhập!'}, status=400)

    invitation = None
    if token:
        invitation = invitation_service.get_valid_invitation(token)
    elif email:
        invitation = invitation_service.get_valid_invitation_by_email(email)

    if not invitation:
        return JsonResponse({'success': False, 'error': 'Email chưa được Admin thêm vào danh sách Lời mời Whitelist.'}, status=400)

    return JsonResponse(otp_service.create_and_send_otp(invitation['email'], invitation['token']))


# ─── Admin: Quản lý lời mời ──────────────────────────────────────────────────

def create_invitation_view(request):
    role = request.session.get('user_role')
    if role not in ('admin', 'leader'):
        return redirect('/login/')

    ctx = {
        'user_name': request.session.get('user_name'),
        'user_role': role,
        'invitations': invitation_service.get_all_invitations(),
    }

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        if action == 'revoke':
            res = invitation_service.revoke_invitation(request.POST.get('invitation_id', ''))
            ctx['success' if res['success'] else 'error'] = (
                'Đã thu hồi lời mời' if res['success'] else res.get('error')
            )
        else:
            email = request.POST.get('email', '').strip()
            fname = request.POST.get('full_name', '').strip()
            errs = {}
            if not email or '@' not in email:
                errs['email'] = 'Gmail không hợp lệ'
            if not fname or len(fname) < 2:
                errs['full_name'] = 'Nhập họ tên đầy đủ'

            if errs:
                ctx.update({'errors': errs, 'form_email': email, 'form_name': fname})
            else:
                res = invitation_service.create_invitation(
                    email=email, full_name=fname,
                    invited_by_id=request.session.get('user_id')
                )
                if res['success']:
                    ctx.update({'success': f'Đã gửi lời mời tới {email}',
                                'invitation_url': res.get('invitation_url')})
                else:
                    ctx['error'] = res['error']

        ctx['invitations'] = invitation_service.get_all_invitations()

    return render(request, 'authentication/invite_create.html', ctx)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _check_password(pw: str) -> str | None:
    if len(pw) < 8:
        return 'Mật khẩu phải có ít nhất 8 ký tự'
    if not re.search(r'[A-Z]', pw):
        return 'Phải có ít nhất 1 chữ hoa (A-Z)'
    if not re.search(r'[0-9]', pw):
        return 'Phải có ít nhất 1 chữ số (0-9)'
    return None
