/* ============================================================
   main.js — Logic chính WebNoiBO Dashboard
   - Sidebar toggle (mobile)
   - Khởi tạo tooltips / dropdowns
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ── Sidebar toggle (mobile) ───────────────────────────────────────────────
    const toggle  = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Đóng sidebar khi click ngoài
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ── Active nav highlight ──────────────────────────────────────────────────
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && path.startsWith(href)) {
            link.classList.add('active');
        }
    });

    // ── Confirm xóa ──────────────────────────────────────────────────────────
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', (e) => {
            if (!confirm(el.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // ── Auto-dismiss alerts sau 5 giây ───────────────────────────────────────
    document.querySelectorAll('.alert-success').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity .5s';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 5000);
    });

});
