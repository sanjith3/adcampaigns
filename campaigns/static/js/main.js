// Main JavaScript file for AdSoft

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Enhanced form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ----- ENHANCED: Modal and Overlay Management -----
    
    function anyOverlayActive() {
        const overlays = document.querySelectorAll('.modal-overlay, .modal, [class*="overlay"]');
        for (let overlay of overlays) {
            const style = getComputedStyle(overlay);
            if (overlay.classList.contains('active') || 
                overlay.classList.contains('show') ||
                style.display === 'flex' || 
                style.display === 'block' ||
                overlay.style.display === 'flex' ||
                overlay.style.display === 'block') {
                return true;
            }
        }
        return false;
    }

    function closeAllCustomOverlays() {
        // Close custom overlays
        document.querySelectorAll('.modal-overlay').forEach(function(ov) {
            ov.classList.remove('active');
            ov.style.display = 'none';
        });
        
        // Close Bootstrap modals
        const bootstrapModals = document.querySelectorAll('.modal');
        bootstrapModals.forEach(modal => {
            if (modal.classList.contains('show')) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                } else {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                }
            }
        });
        
        // Remove backdrop and reset body
        document.querySelectorAll('.modal-backdrop').forEach(function(el) { 
            el.remove(); 
        });
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    function cleanupStuckOverlays() {
        const hasVisibleModal = document.querySelector('.modal.show, .modal-overlay.active');
        const hasBackdrop = document.querySelector('.modal-backdrop');
        
        // If body says modal-open but no modal is visible, clean up
        if (document.body.classList.contains('modal-open') && !hasVisibleModal) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
        
        // Remove orphaned backdrops
        if (hasBackdrop && !hasVisibleModal) {
            hasBackdrop.remove();
        }
    }

    // Run cleanup on load
    cleanupStuckOverlays();

    // ESC key closes overlays
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllCustomOverlays();
        }
    });

    // Click outside closes custom overlays
    document.addEventListener('click', function(e) {
        // For custom overlays
        const customOverlay = e.target.closest('.modal-overlay');
        if (customOverlay && e.target === customOverlay) {
            closeAllCustomOverlays();
        }
        
        // For Bootstrap modals
        const bootstrapModal = e.target.closest('.modal');
        if (bootstrapModal && e.target === bootstrapModal) {
            const bsModal = bootstrap.Modal.getInstance(bootstrapModal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    });

    // Cleanup on page visibility changes
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            setTimeout(cleanupStuckOverlays, 100);
        }
    });

    // Cleanup when navigating away
    window.addEventListener('beforeunload', cleanupStuckOverlays);
    
    // Additional cleanup after page fully loads
    window.addEventListener('load', cleanupStuckOverlays);
});

// Utility functions
const AdSoft = {
    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0
        }).format(amount);
    },

    // Format date
    formatDate: function(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleDateString('en-IN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return 'Invalid Date';
        }
    },

    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        // Remove existing notifications first
        document.querySelectorAll('.adsoft-notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed adsoft-notification`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px; max-width: 500px;';
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                const bsAlert = new bootstrap.Alert(notification);
                bsAlert.close();
            }
        }, 5000);
    },

    getNotificationIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    // New: Modal helper functions
    showModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            if (modal.classList.contains('modal')) {
                // Bootstrap modal
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            } else {
                // Custom modal
                modal.classList.add('active');
                modal.style.display = 'flex';
                document.body.classList.add('modal-open');
            }
        }
    },

    hideModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            if (modal.classList.contains('modal')) {
                // Bootstrap modal
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                } else {
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                }
            } else {
                // Custom modal
                modal.classList.remove('active');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
            }
        }
    }
};

// Global error handler to catch any remaining issues
window.addEventListener('error', function(e) {
    console.error('Global error caught:', e.error);
    // You can add error reporting here
});