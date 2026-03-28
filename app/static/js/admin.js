/**
 * Certivo Blog - Admin Panel JavaScript
 * Handles sidebar toggles, theme switching, and basic UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ─── Sidebar Toggle (Mobile) ─────────────────────────────────────────────
    const sidebar = document.getElementById('admin-sidebar');
    const sidebarToggle = document.getElementById('admin-sidebar-toggle');
    const sidebarOverlay = document.getElementById('admin-sidebar-overlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            const isExpanded = sidebarToggle.getAttribute('aria-expanded') === 'true';
            sidebarToggle.setAttribute('aria-expanded', !isExpanded);
            sidebar.classList.toggle('admin-sidebar--open');
            sidebarOverlay.classList.toggle('admin-sidebar-overlay--active');
            document.body.classList.toggle('overflow-hidden');
        });

        // Close when clicking overlay
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => {
                sidebarToggle.setAttribute('aria-expanded', 'false');
                sidebar.classList.remove('admin-sidebar--open');
                sidebarOverlay.classList.remove('admin-sidebar-overlay--active');
                document.body.classList.remove('overflow-hidden');
            });
        }
    }

    // ─── User Menu Dropdown ──────────────────────────────────────────────────
    const userMenuBtn = document.getElementById('admin-user-menu-btn');
    const userDropdown = document.getElementById('admin-user-dropdown');

    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = userMenuBtn.getAttribute('aria-expanded') === 'true';
            userMenuBtn.setAttribute('aria-expanded', !isExpanded);
            userDropdown.classList.toggle('admin-topbar__user-dropdown--active');
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                userMenuBtn.setAttribute('aria-expanded', 'false');
                userDropdown.classList.remove('admin-topbar__user-dropdown--active');
            }
        });
    }

    // ─── Theme Toggle (Dark Mode) ───────────────────────────────────────────
    const themeToggle = document.getElementById('admin-theme-toggle');
    const htmlElement = document.documentElement;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('admin-theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('admin-theme', newTheme);
            
            // Optional: Dispatch event for other components
            window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: newTheme } }));
        });
    }

    // ─── Auto-dismiss Alerts ───────────────────────────────────────────────
    const alerts = document.querySelectorAll('.admin-alert');
    alerts.forEach(alert => {
        const timeout = alert.classList.contains('alert--danger') ? 10000 : 5000;
        setTimeout(() => {
            alert.classList.add('fade-out');
            setTimeout(() => alert.remove(), 500);
        }, timeout);
    });
});
