// KitabGhar Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this book? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // File size validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const maxSize = 50 * 1024 * 1024; // 50MB
                if (file.size > maxSize) {
                    alert('File size exceeds 50MB limit!');
                    e.target.value = '';
                    return;
                }
                
                // Show file info
                const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
                const helpText = e.target.nextElementSibling;
                if (helpText && helpText.classList.contains('form-text')) {
                    helpText.innerHTML = `<i class="fas fa-info-circle me-1"></i>Selected: ${file.name} (${sizeMB} MB)`;
                }
            }
        });
    });

    // Search form enhancement
    const searchForm = document.querySelector('form[method="GET"]');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        if (searchInput) {
            // Auto-submit on category/sort change
            const selects = searchForm.querySelectorAll('select');
            selects.forEach(function(select) {
                select.addEventListener('change', function() {
                    searchForm.submit();
                });
            });

            // Enter key handling
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchForm.submit();
                }
            });
        }
    }

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Loading states for form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitBtn.disabled = true;
                
                // Re-enable after 10 seconds as fallback
                setTimeout(function() {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });

    // Copy to clipboard functionality (if needed)
    const copyButtons = document.querySelectorAll('[data-clipboard-text]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-clipboard-text');
            navigator.clipboard.writeText(text).then(function() {
                // Show temporary success message
                const originalText = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
                setTimeout(function() {
                    button.innerHTML = originalText;
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy: ', err);
            });
        });
    });

    // Enhanced card interactions
    const bookCards = document.querySelectorAll('.card');
    bookCards.forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Social sharing for selected text
    document.addEventListener('mouseup', function(event) {
        const selection = window.getSelection().toString().trim();
        if (selection && selection.length > 5) {
            const shareData = {
                title: 'Quote from KitabGhar',
                text: `"${selection}" — via KitabGhar`,
                url: window.location.href
            };
            if (navigator.share) {
                // Show a tiny tooltip/button near cursor to share
                const btn = document.createElement('button');
                btn.className = 'btn btn-sm btn-success position-fixed';
                btn.style.left = (event.pageX + 10) + 'px';
                btn.style.top = (event.pageY + 10) + 'px';
                btn.textContent = 'Share quote';
                document.body.appendChild(btn);
                const cleanup = ()=>{ btn.remove(); document.removeEventListener('scroll', cleanup); };
                document.addEventListener('scroll', cleanup, { once: true });
                btn.addEventListener('click', async ()=>{
                    try { await navigator.share(shareData); } catch(e) {}
                    cleanup();
                }, { once: true });
                setTimeout(cleanup, 4000);
            }
        }
    });

    // Persist client-side reading position as a quick fallback
    document.addEventListener('kg:page-changed', function(e){
        const { ebookId, page } = e.detail || {};
        if (ebookId && page) localStorage.setItem(`book_${ebookId}_page`, page);
    });

    // Navigation active state
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath === href) {
            link.classList.add('active');
        }
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Smooth scrolling for anchor links
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href^="#"]');
        if (link) {
            const href = link.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
});

// Utility functions
window.KitabGhar = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                const alert = new bootstrap.Alert(alertDiv);
                alert.close();
            }, 5000);
        }
    },

    // Confirm action
    confirmAction: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    }
};
