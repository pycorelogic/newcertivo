# Task: Certivo Blog UI Overhaul & Bug Fixes

## Current Status
- [x] Fix `TemplateSyntaxError` in blog routing and pagination.
- [x] Fix SQLAlchemy `CompileError` in `order_by` (converted string to column reference).
- [x] Overhaul UI to Matte Orange/Black/White theme.
- [x] Fix broken Breadcrumbs UI.
- [x] Fixed Mixin name error (`text-truncate` -> `truncate`).
- [x] Manually compiled SCSS to verify all styles are applied.
- [x] Cleaned up AdSense/Affiliate placeholders and modernized the comments/form UI.
- [x] Fixed YouTube subscribe link visibility and contrast.
- [x] Implemented dynamic Table of Contents (TOC) with modern styling and toggle logic.
- [x] Verified Admin Dashboard and Login functionality (server restarted on port 5000).
- [x] Fixed Image Library modal bug (stuck loading/visible on load) and restored `editor.js`.
- [x] Fixed dark mode toggle not working on blog detail page (removed duplicate `main.js` inclusion).
- [x] Clean up database placeholder content (e.g., "Link Broken") via Admin Panel.
- [x] Review remaining pages (Contact, Search, About) for styling consistency.

## Progress Log

### 2026-03-07
1. **Redesigned UI**: Updated SCSS variables to use Matte Orange (`#FF7043`), Matte Black (`#121212`), and Crisp White (`#FFFFFF`).
2. **Fixed Template Syntax**: Resolved invalid Jinja2 syntax in `pagination.html`.
3. **Fixed SQLAlchemy Errors**: 
   - Found and fixed `CompileError: Can't resolve label reference for ORDER BY`.
   - Updated `app/templates/blog/detail.html` to use model property `approved_replies`.
   - Updated `Post` and `Comment` models to use explicit column references in `order_by`.
4. **Resolved UI Regression**:
   - Identified that `breadcrumb-bar` and `breadcrumb` classes were missing from SCSS.
   - Created `app/static/scss/components/_breadcrumbs.scss` and imported it in `main.scss`.
   - Fixed a mixin name error (`text-truncate` was called but `truncate` was defined).
   - Manually compiled SCSS using a helper script to ensure `main.css` is updated with the new theme and component styles.
5. **Modernized Blog Detail UI & Cleanup**:
   - **Comments & Forms**: Populated `_comments.scss` with a premium, modern design for the comment list and reply forms, ensuring full-width inputs and better focus states.
   - **Cleanup**: Stripped all remaining AdSense and Affiliate placeholders from `detail.html`, `sidebar.html`, and `index.html` to reduce visual bloat.
   - **Theming**: Updated default user avatar background and sidebar about avatar to use the Matte Orange (`#FF7043`) theme.
   - **Affiliate CTA**: Styled the `.affiliate-cta-block` in `_affiliate.scss` to match the new premium aesthetic.
   - **Re-compiled SCSS**: Regenerated `main.css` to include the new component styles.
6. **YouTube & Table of Contents (TOC) Enhancements**:
   - **YouTube Visibility**: Fixed the subscribe link in `_single-post.scss` and `_buttons.scss` by ensuring white text on red backgrounds for accessibility and brand consistency.
   - **Dynamic TOC**: Created `_toc.scss` and updated `main.js` to automatically generate a functional, toggleable Table of Contents from `<h2>` and `<h3>` tags in post content.
   - **Copy Link**: Implemented "Copy Link" button functionality in `main.js` with visual feedback on success.
   - **Cache Busting**: Bumped CSS version to `v=1.0.4` in `base.html` and updated `main.scss` version comment to ensure users receive the latest styling updates.
   - **Avatar Sync**: Updated `app/models/comment.py` to use Matte Orange (`#FF7043`) as the default background for comment avatars.
7. **Admin Editor & Image Library Fix**:
   - **Bug Fix**: Resolved an issue where the Image Library modal was visible on page load and stuck in a "Loading" state. Added `hidden` attribute to the modal in `post_form.html`.
   - **Editor Logic**: Restored the missing `app/static/js/editor.js` file, implementing Quill editor initialization, Visual/HTML mode toggling, and the Image Library fetch/copy-to-clipboard functionality.
8. **Dark Mode Toggle Fix**:
   - **Bug Fix**: Identified that the dark mode toggle was failing on blog detail pages because `main.js` was being included twice (once in `base.html` and again in `detail.html`), causing the toggle logic to run twice and instantly revert its state.
   - **Resolution**: Removed the duplicate `<script>` tag from `app/templates/blog/detail.html`.
9. **Final Audit & Cleanup**:
   - Verified that the Contact, Search, and About pages are visually consistent with the Matte Orange/Black theme.
   - Performed a final check of the Admin Panel, ensuring all dynamic features (TOC, Image Library, Editor) are functioning correctly.
   - Closed active Python server processes to finalize the session.
