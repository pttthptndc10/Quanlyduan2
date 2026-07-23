/* ============================================================
   auth.js — Logic cho các trang xác thực WebNoiBO
   - Toggle show/hide password
   - Password strength meter
   - Gửi OTP qua AJAX
   - Countdown 10 phút sau khi gửi OTP
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ── 1. Toggle show/hide password ─────────────────────────────────────────
    document.querySelectorAll('.toggle-pw').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target || 'password';
            const input = document.getElementById(targetId) || btn.parentElement.querySelector('input');
            if (!input) return;

            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';

            const open   = btn.querySelector('.eye-open');
            const closed = btn.querySelector('.eye-closed');
            if (open)   open.style.display   = isHidden ? 'none'  : '';
            if (closed) closed.style.display = isHidden ? ''      : 'none';
        });
    });

    // ── 2. Password strength meter ────────────────────────────────────────────
    window.checkStrength = function(value) {
        const bar  = document.getElementById('strengthBar');
        const hint = document.getElementById('strengthHint');
        if (!bar || !hint) return;

        const tests = [
            value.length >= 8,
            /[A-Z]/.test(value),
            /[0-9]/.test(value),
            /[^A-Za-z0-9]/.test(value),
        ];
        const score = tests.filter(Boolean).length;

        const levels = [
            { pct: '0%',   bg: 'transparent', text: '' },
            { pct: '25%',  bg: '#ef4444',     text: 'Quá yếu' },
            { pct: '50%',  bg: '#f59e0b',     text: 'Trung bình' },
            { pct: '75%',  bg: '#06b6d4',     text: 'Tốt' },
            { pct: '100%', bg: '#22c55e',      text: 'Mạnh ✓' },
        ];

        const { pct, bg, text } = levels[score];
        bar.style.width = pct;
        bar.style.background = bg;
        hint.textContent = text;
        hint.style.color = bg;
    };

    // ── 3. Nút gửi OTP ───────────────────────────────────────────────────────
    const btnOtp = document.getElementById('btnSendOtp');
    if (btnOtp) {
        btnOtp.addEventListener('click', async () => {
            const token = btnOtp.dataset.token || '';
            const emailInput = document.getElementById('email');
            const email = emailInput ? emailInput.value.trim() : '';
            const hint  = document.getElementById('otpHint');

            if (!token && !email) {
                if (hint) {
                    hint.textContent = '❌ Vui lòng nhập Email';
                    hint.style.color = '#fca5a5';
                }
                return;
            }

            btnOtp.disabled = true;
            btnOtp.textContent = 'Đang gửi…';
            if (hint) hint.textContent = '';

            try {
                const res = await fetch('/api/send-otp/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({ token, email }),
                });

                const data = await res.json();

                if (data.success) {
                    if (hint) hint.textContent = data.message || 'Mã OTP đã gửi!';
                    startCountdown(btnOtp, hint, 600); // 10 phút
                } else {
                    if (hint) {
                        hint.textContent = '❌ ' + (data.error || 'Lỗi gửi OTP');
                        hint.style.color = '#fca5a5';
                    }
                    btnOtp.disabled = false;
                    btnOtp.textContent = 'Gửi lại mã';
                }
            } catch (e) {
                if (hint) hint.textContent = '❌ Không thể kết nối server';
                btnOtp.disabled = false;
                btnOtp.textContent = 'Thử lại';
            }
        });
    }

    // ── 4. Countdown ─────────────────────────────────────────────────────────
    function startCountdown(btn, hint, totalSeconds) {
        let remaining = totalSeconds;
        btn.disabled = true;

        const interval = setInterval(() => {
            remaining--;
            const m = Math.floor(remaining / 60);
            const s = remaining % 60;
            btn.textContent = `${m}:${s.toString().padStart(2, '0')} còn lại`;

            if (remaining <= 0) {
                clearInterval(interval);
                btn.disabled = false;
                btn.textContent = 'Gửi lại mã';
                if (hint) hint.textContent = 'Mã đã hết hạn. Nhấn "Gửi lại mã" để lấy mã mới.';
            }
        }, 1000);
    }

    // ── 5. CSRF Token từ cookie ───────────────────────────────────────────────
    function getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            const [k, v] = c.trim().split('=');
            if (k === name) return decodeURIComponent(v);
        }
        // Fallback: lấy từ input hidden
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    // ── 6. Loading state khi submit form ─────────────────────────────────────
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', () => {
            const btn = form.querySelector('.btn-primary[type=submit]');
            if (btn) {
                btn.textContent = 'Đang xử lý…';
                btn.disabled = true;
            }
        });
    });

});
