/**
 * Certivo Blog - Admin Editor JavaScript
 * Handles Quill rich-text editor, mode toggling, and image library modal.
 */

document.addEventListener('DOMContentLoaded', () => {
    const quillContainer = document.getElementById('quill-editor');
    const rawTextarea = document.getElementById('post-content-raw');
    const visualBtn = document.getElementById('visual-mode-btn');
    const htmlBtn = document.getElementById('html-mode-btn');

    if (!quillContainer || !rawTextarea) return;

    // ─── Initialize Quill ──────────────────────────────────────────────────
    const quill = new Quill('#quill-editor', {
        theme: 'snow',
        modules: {
            toolbar: [
                [{ 'header': [2, 3, 4, false] }],
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                [{ 'script': 'sub'}, { 'script': 'super' }],
                ['link', 'image', 'video'],
                ['clean']
            ]
        },
        placeholder: 'Write your story here...'
    });

    // ─── Mode Toggling (Visual / HTML) ──────────────────────────────────────
    if (visualBtn && htmlBtn) {
        visualBtn.addEventListener('click', () => {
            if (visualBtn.classList.contains('admin-editor-mode-btn--active')) return;
            
            // Sync HTML to Quill
            quill.root.innerHTML = rawTextarea.value;
            
            // Toggle Visibility
            rawTextarea.style.display = 'none';
            quillContainer.style.display = 'block';
            document.querySelector('.ql-toolbar').style.display = 'block';
            
            // Toggle Active State
            visualBtn.classList.add('admin-editor-mode-btn--active');
            htmlBtn.classList.remove('admin-editor-mode-btn--active');
        });

        htmlBtn.addEventListener('click', () => {
            if (htmlBtn.classList.contains('admin-editor-mode-btn--active')) return;
            
            // Sync Quill to HTML
            rawTextarea.value = quill.root.innerHTML;
            
            // Toggle Visibility
            quillContainer.style.display = 'none';
            document.querySelector('.ql-toolbar').style.display = 'none';
            rawTextarea.style.display = 'block';
            
            // Toggle Active State
            htmlBtn.classList.add('admin-editor-mode-btn--active');
            visualBtn.classList.remove('admin-editor-mode-btn--active');
        });
    }

    // Sync content to hidden textarea on every change
    quill.on('text-change', () => {
        rawTextarea.value = quill.root.innerHTML;
        updateStats();
    });

    // ─── Stats (Word Count & Read Time) ─────────────────────────────────────
    const wordCountEl = document.getElementById('word-count');
    const readTimeEl = document.getElementById('read-time');

    function updateStats() {
        const text = quill.getText().trim();
        const words = text ? text.split(/\s+/).length : 0;
        const readTime = Math.ceil(words / 200);

        if (wordCountEl) wordCountEl.textContent = `${words} word${words !== 1 ? 's' : ''}`;
        if (readTimeEl) readTimeEl.textContent = `~ ${readTime} min read`;
    }

    // Initial stats
    updateStats();

    // ─── Image Library Modal ────────────────────────────────────────────────
    const imageLibraryModal = document.getElementById('image-library-modal');
    const openModalBtn = document.getElementById('editor-image-btn');
    const closeModalBtns = [
        document.getElementById('image-library-close'),
        document.getElementById('image-library-cancel'),
        document.getElementById('image-library-backdrop')
    ];
    const imageGrid = document.getElementById('image-library-grid');
    let imagesLoaded = false;

    if (openModalBtn && imageLibraryModal) {
        openModalBtn.addEventListener('click', () => {
            imageLibraryModal.removeAttribute('hidden');
            imageLibraryModal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';

            if (!imagesLoaded) {
                fetchImages();
            }
        });

        closeModalBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    imageLibraryModal.setAttribute('hidden', '');
                    imageLibraryModal.setAttribute('aria-hidden', 'true');
                    document.body.style.overflow = '';
                });
            }
        });
    }

    async function fetchImages() {
        if (!imageGrid) return;

        try {
            const response = await fetch('/admin/api/images');
            const images = await response.json();

            if (images.length === 0) {
                imageGrid.innerHTML = '<div class="admin-image-library__empty">No images found. Upload some in the Media section!</div>';
            } else {
                imageGrid.innerHTML = ''; // Clear loading
                images.forEach(img => {
                    const item = document.createElement('div');
                    item.className = 'admin-image-library__item';
                    item.innerHTML = `
                        <img src="${img.url}" alt="${img.filename}" title="${img.filename}" loading="lazy">
                        <div class="admin-image-library__name">${img.filename}</div>
                    `;
                    item.addEventListener('click', () => {
                        copyToClipboard(img.url, item);
                    });
                    imageGrid.appendChild(item);
                });
            }
            imagesLoaded = true;
        } catch (error) {
            imageGrid.innerHTML = '<div class="admin-image-library__error">Failed to load images.</div>';
            console.error('Error fetching images:', error);
        }
    }

    function copyToClipboard(text, element) {
        navigator.clipboard.writeText(text).then(() => {
            const originalName = element.querySelector('.admin-image-library__name').textContent;
            element.querySelector('.admin-image-library__name').textContent = 'Copied URL!';
            element.classList.add('admin-image-library__item--copied');
            
            setTimeout(() => {
                element.querySelector('.admin-image-library__name').textContent = originalName;
                element.classList.remove('admin-image-library__item--copied');
            }, 2000);
        });
    }
});
