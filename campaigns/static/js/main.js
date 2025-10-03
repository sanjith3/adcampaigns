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

    // ----- FIXED: Simplified Modal and Overlay Management -----
    
    function cleanupStuckOverlays() {
        // Only clean up if there are stuck modal states
        const hasVisibleModal = document.querySelector('.modal.show');
        
        // If body says modal-open but no modal is visible, clean up
        if (document.body.classList.contains('modal-open') && !hasVisibleModal) {
            console.log('Cleaning up stuck modal state');
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // Remove orphaned backdrops (only if no modal is showing)
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });
        }
    }

    // Run cleanup after a short delay to ensure page is loaded
    setTimeout(cleanupStuckOverlays, 100);

    // ESC key closes modals (let Bootstrap handle this for Bootstrap modals)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Only handle custom overlays, let Bootstrap handle its modals
            const customOverlays = document.querySelectorAll('.modal-overlay.active');
            customOverlays.forEach(overlay => {
                overlay.classList.remove('active');
                overlay.style.display = 'none';
            });
            
            // Clean up if no modals are left
            cleanupStuckOverlays();
        }
    });

    // Click outside closes ONLY custom overlays (not Bootstrap modals)
    document.addEventListener('click', function(e) {
        // For custom overlays only
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('active');
            e.target.style.display = 'none';
            cleanupStuckOverlays();
        }
    });

    // Cleanup when page becomes visible again
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            setTimeout(cleanupStuckOverlays, 50);
        }
    });

    // Listen for Bootstrap modal events to prevent conflicts
    document.addEventListener('show.bs.modal', function() {
        console.log('Bootstrap modal opening - skipping cleanup');
    });

    document.addEventListener('hidden.bs.modal', function() {
        console.log('Bootstrap modal closed - running cleanup');
        setTimeout(cleanupStuckOverlays, 50);
    });
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

    // Modal helper functions - FIXED
    showModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            if (modal.classList.contains('modal')) {
                // Bootstrap modal - let Bootstrap handle it
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            } else {
                // Custom modal
                modal.classList.add('active');
                modal.style.display = 'flex';
            }
        }
    },

    hideModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            if (modal.classList.contains('modal')) {
                // Bootstrap modal - let Bootstrap handle it
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            } else {
                // Custom modal
                modal.classList.remove('active');
                modal.style.display = 'none';
            }
        }
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error caught:', e.error);
});

// Emergency cleanup function - call this if overlays persist
window.forceCleanupOverlays = function() {
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
    console.log('Emergency overlay cleanup completed');
};