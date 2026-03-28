// ============================================================================
// CERTIVO BLOG - MAIN JAVASCRIPT
// ============================================================================

(function() {
  'use strict';

  // ─── Constants ──────────────────────────────────────────────────────────────
  const THEME_KEY = 'certivo_theme';
  const MOBILE_BREAKPOINT = 992;

  // ─── DOM Ready ──────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
    initTheme();
    initSearch();
    initLazyLoading();
    initSmoothScroll();
    initBackToTop();
    initFlashMessages();
    initPostDetail();
  });

  // ─── Post Detail Functionality ──────────────────────────────────────────────

  function initPostDetail() {
    const postContent = document.getElementById('post-content');
    const tocList = document.getElementById('toc-list');
    const tocToggle = document.getElementById('toc-toggle');
    const copyLinkBtn = document.getElementById('copy-link-btn');

    if (!postContent) return;

    // --- Table of Contents Generation ---
    if (tocList) {
      const headings = postContent.querySelectorAll('h2, h3');
      
      if (headings.length === 0) {
        const tocContainer = document.getElementById('table-of-contents');
        if (tocContainer) tocContainer.style.display = 'none';
      } else {
        headings.forEach((heading, index) => {
          const id = heading.id || `heading-${index}`;
          heading.id = id;

          const li = document.createElement('li');
          li.className = `toc__item toc__item--${heading.tagName.toLowerCase()}`;
          
          const a = document.createElement('a');
          a.href = `#${id}`;
          a.className = 'toc__link';
          a.textContent = heading.textContent;
          
          li.appendChild(a);
          tocList.appendChild(li);
        });
      }
    }

    // --- TOC Toggle ---
    if (tocToggle && tocList) {
      tocToggle.addEventListener('click', function() {
        const expanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', !expanded);
        tocList.setAttribute('aria-hidden', expanded);
        tocList.style.display = expanded ? 'none' : 'flex';
      });
    }

    // --- Copy Link Button ---
    if (copyLinkBtn) {
      copyLinkBtn.addEventListener('click', function() {
        const url = this.getAttribute('data-url');
        navigator.clipboard.writeText(url).then(() => {
          const originalHTML = this.innerHTML;
          this.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
          this.classList.add('btn--success');
          
          setTimeout(() => {
            this.innerHTML = originalHTML;
            this.classList.remove('btn--success');
          }, 2000);
        });
      });
    }
  }

  // ─── Navbar Functionality ───────────────────────────────────────────────────

  function initNavbar() {
    const navbar = document.getElementById('navbar');
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileOverlay = document.getElementById('mobile-overlay');
    const searchToggleBtn = document.getElementById('search-toggle-btn');
    const searchOverlay = document.getElementById('search-overlay');
    const searchCloseBtn = document.getElementById('search-close-btn');
    const searchInput = document.getElementById('search-input');

    if (!navbar) return;

    // Mobile menu toggle
    if (hamburgerBtn) {
      hamburgerBtn.addEventListener('click', function() {
        const expanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', !expanded);
        this.classList.toggle('active');
        mobileMenu?.classList.toggle('active');
        mobileOverlay?.classList.toggle('active');
        document.body.style.overflow = !expanded ? 'hidden' : '';
      });
    }

    // Close menu when clicking overlay
    if (mobileOverlay) {
      mobileOverlay.addEventListener('click', function() {
        closeMenu();
      });
    }

    function closeMenu() {
      hamburgerBtn?.setAttribute('aria-expanded', 'false');
      hamburgerBtn?.classList.remove('active');
      mobileMenu?.classList.remove('active');
      mobileOverlay?.classList.remove('active');
      document.body.style.overflow = '';
    }

    // Search overlay toggle
    if (searchToggleBtn) {
      searchToggleBtn.addEventListener('click', function() {
        searchOverlay?.classList.add('active');
        searchOverlay?.setAttribute('aria-hidden', 'false');
        setTimeout(() => searchInput?.focus(), 100);
        document.body.style.overflow = 'hidden';
      });
    }

    if (searchCloseBtn) {
      searchCloseBtn.addEventListener('click', function() {
        closeSearch();
      });
    }

    function closeSearch() {
      searchOverlay?.classList.remove('active');
      searchOverlay?.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    // Close search on Esc
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && searchOverlay?.classList.contains('active')) {
        closeSearch();
      }
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
      if (window.pageYOffset > 50) {
        navbar.classList.add('navbar--scrolled');
      } else {
        navbar.classList.remove('navbar--scrolled');
      }
    });
  }

  // ─── Theme Toggle ───────────────────────────────────────────────────────────

  function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
    const html = document.documentElement;

    // Check for saved preference
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme) {
      html.setAttribute('data-theme', savedTheme);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      html.setAttribute('data-theme', 'dark');
    }

    const toggleTheme = () => {
      const currentTheme = html.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem(THEME_KEY, newTheme);
    };

    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }

    if (mobileThemeToggle) {
      mobileThemeToggle.addEventListener('click', toggleTheme);
    }
  }

  // ─── Search Functionality ───────────────────────────────────────────────────

  function initSearch() {
    const searchForm = document.querySelector('.search-overlay__form');
    if (searchForm) {
      searchForm.addEventListener('submit', function(e) {
        const input = this.querySelector('input');
        if (!input.value.trim()) {
          e.preventDefault();
          input.focus();
        }
      });
    }
  }

  // ─── Lazy Loading ───────────────────────────────────────────────────────────

  function initLazyLoading() {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
            }
            observer.unobserve(img);
          }
        });
      });

      document.querySelectorAll('img[loading="lazy"]').forEach(img => observer.observe(img));
    }
  }

  // ─── Smooth Scroll ──────────────────────────────────────────────────────────

  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          const offset = 80;
          const bodyRect = document.body.getBoundingClientRect().top;
          const elementRect = target.getBoundingClientRect().top;
          const elementPosition = elementRect - bodyRect;
          const offsetPosition = elementPosition - offset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // ─── Back to Top ────────────────────────────────────────────────────────────

  function initBackToTop() {
    const btn = document.getElementById('back-to-top');
    if (!btn) return;

    window.addEventListener('scroll', () => {
      if (window.pageYOffset > 400) {
        btn.classList.add('visible');
      } else {
        btn.classList.remove('visible');
      }
    });

    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ─── Flash Messages ─────────────────────────────────────────────────────────

  function initFlashMessages() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
      setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
      }, 5000);
    });
  }

})();
