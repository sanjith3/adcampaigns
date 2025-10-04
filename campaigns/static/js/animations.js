// Main JavaScript for animations and interactions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initAnimations();
    initSidebar();
    initLoadingScreen();
    initHoverEffects();
    initStaggerAnimations();
    initNotifications();
});

// Loading screen handler
function initLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        // Simulate loading time
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }, 1000);
    }
}

// Sidebar functionality
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            
            // Update icon
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-chevron-right');
            } else {
                icon.classList.remove('fa-chevron-right');
                icon.classList.add('fa-bars');
            }
            
            // Save sidebar state
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }
    
    // Load sidebar state
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
        sidebar?.classList.add('collapsed');
        const icon = sidebarToggle?.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-chevron-right');
        }
    }
    
    // Auto-collapse sidebar on mobile
    function handleResize() {
        if (window.innerWidth < 768) {
            sidebar?.classList.add('collapsed');
        } else {
            // Restore previous state on desktop
            const savedState = localStorage.getItem('sidebarCollapsed') === 'true';
            if (!savedState) {
                sidebar?.classList.remove('collapsed');
            }
        }
    }
    
    window.addEventListener('resize', debounce(handleResize, 250));
    handleResize(); // Initial check
}

// Initialize animations
function initAnimations() {
    // Add animation classes to elements
    const animatedElements = document.querySelectorAll('.stat-card, .section-card, .progress-card');
    
    animatedElements.forEach((element, index) => {
        element.classList.add('slide-in-up');
        element.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Add hover effects to cards
    const cards = document.querySelectorAll('.stat-card, .section-card');
    cards.forEach(card => {
        card.classList.add('hover-lift');
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn, .header-btn');
    buttons.forEach(button => {
        button.classList.add('ripple');
    });
    
    // Initialize tooltips
    initTooltips();
}

// Initialize tooltips
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        new bootstrap.Tooltip(element);
    });
}

// Initialize hover effects
function initHoverEffects() {
    // Add hover effects to table rows
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
}

// Initialize staggered animations
function initStaggerAnimations() {
    const staggerItems = document.querySelectorAll('.stagger-item');
    staggerItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.1}s`;
    });
}

// Initialize notifications
function initNotifications() {
    // Check for new notifications periodically
    setInterval(() => {
        checkNotifications();
    }, 30000); // Check every 30 seconds
    
    checkNotifications(); // Initial check
}

function checkNotifications() {
    // Simulate notification check - replace with actual API call
    const hasNotifications = Math.random() > 0.7; // 30% chance of having notifications
    
    const notificationBadge = document.getElementById('globalNotificationBadge');
    if (notificationBadge) {
        if (hasNotifications) {
            notificationBadge.style.display = 'block';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
}

// Notification handler
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show slide-in-right`;
    notification.innerHTML = `
        <div class="alert-content">
            <i class="alert-icon fas ${getNotificationIcon(type)}"></i>
            ${message}
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const contentArea = document.querySelector('.content-area');
    if (contentArea) {
        contentArea.prepend(notification);
        
        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

// Form validation with animations
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            input.classList.add('shake');
            isValid = false;
            
            // Remove shake animation after it completes
            setTimeout(() => {
                input.classList.remove('shake');
            }, 500);
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Add loading state to buttons
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        const originalText = button.innerHTML;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        button.classList.add('loading');
    } else {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.innerHTML = originalText;
        }
        button.classList.remove('loading');
    }
}

// Smooth scroll to element
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
}

// Debounce function for performance
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Export functions for global use
window.AdSoft = {
    showNotification,
    validateForm,
    setButtonLoading,
    scrollToElement,
    debounce
};