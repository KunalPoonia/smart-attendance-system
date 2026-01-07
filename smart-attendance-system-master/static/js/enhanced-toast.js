/**
 * Enhanced Toast Notification System
 * Provides modern toast notifications with animations and auto-dismiss functionality
 */

class EnhancedToast {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.defaultOptions = {
            duration: 5000,
            showProgress: true,
            closable: true,
            position: 'top-right',
            maxToasts: 5
        };
        
        this.init();
    }
    
    /**
     * Initialize the toast system
     */
    init() {
        this.createContainer();
        this.bindEvents();
        this.convertExistingAlerts();
    }
    
    /**
     * Create the toast container
     */
    createContainer() {
        if (this.container) return;
        
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        this.container.setAttribute('aria-live', 'polite');
        this.container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(this.container);
    }
    
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Toast type: success, error, warning, info
     * @param {Object} options - Additional options
     */
    show(message, type = 'info', options = {}) {
        const config = { ...this.defaultOptions, ...options };
        
        // Limit number of toasts
        if (this.toasts.length >= config.maxToasts) {
            this.removeOldestToast();
        }
        
        const toast = this.createToast(message, type, config);
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        // Trigger show animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto dismiss
        if (config.duration > 0) {
            this.startAutoDismiss(toast, config.duration);
        }
        
        return toast;
    }
    
    /**
     * Create a toast element
     * @param {string} message - The message to display
     * @param {string} type - Toast type
     * @param {Object} config - Configuration options
     */
    createToast(message, type, config) {
        const toast = document.createElement('div');
        toast.className = `toast-enhanced toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const iconMap = {
            success: 'fas fa-check',
            error: 'fas fa-times',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info'
        };
        
        const titleMap = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        
        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-icon">
                    <i class="${iconMap[type]}"></i>
                </div>
                <strong class="toast-title">${titleMap[type]}</strong>
                ${config.closable ? '<button type="button" class="toast-close" aria-label="Close"><i class="fas fa-times"></i></button>' : ''}
            </div>
            <div class="toast-body">${message}</div>
            ${config.showProgress ? '<div class="toast-progress"></div>' : ''}
        `;
        
        // Add close functionality
        if (config.closable) {
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => this.hide(toast));
        }
        
        // Add click to dismiss (optional)
        toast.addEventListener('click', (e) => {
            if (!e.target.closest('.toast-close')) {
                this.hide(toast);
            }
        });
        
        return toast;
    }
    
    /**
     * Start auto-dismiss timer with progress bar
     * @param {HTMLElement} toast - Toast element
     * @param {number} duration - Duration in milliseconds
     */
    startAutoDismiss(toast, duration) {
        const progressBar = toast.querySelector('.toast-progress');
        
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.style.transitionDuration = `${duration}ms`;
            
            requestAnimationFrame(() => {
                progressBar.style.width = '0%';
            });
        }
        
        const timer = setTimeout(() => {
            this.hide(toast);
        }, duration);
        
        toast.dataset.timer = timer;
        
        // Pause on hover
        toast.addEventListener('mouseenter', () => {
            clearTimeout(timer);
            if (progressBar) {
                const currentWidth = progressBar.getBoundingClientRect().width;
                const containerWidth = progressBar.parentElement.getBoundingClientRect().width;
                const percentage = (currentWidth / containerWidth) * 100;
                progressBar.style.width = `${percentage}%`;
                progressBar.style.transitionDuration = '0s';
            }
        });
        
        // Resume on mouse leave
        toast.addEventListener('mouseleave', () => {
            if (progressBar) {
                const currentWidth = progressBar.getBoundingClientRect().width;
                const containerWidth = progressBar.parentElement.getBoundingClientRect().width;
                const percentage = (currentWidth / containerWidth) * 100;
                const remainingTime = (percentage / 100) * duration;
                
                progressBar.style.transitionDuration = `${remainingTime}ms`;
                progressBar.style.width = '0%';
                
                const newTimer = setTimeout(() => {
                    this.hide(toast);
                }, remainingTime);
                
                toast.dataset.timer = newTimer;
            }
        });
    }
    
    /**
     * Hide a toast notification
     * @param {HTMLElement} toast - Toast element to hide
     */
    hide(toast) {
        if (!toast || !toast.parentElement) return;
        
        // Clear timer
        if (toast.dataset.timer) {
            clearTimeout(parseInt(toast.dataset.timer));
        }
        
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
                this.toasts = this.toasts.filter(t => t !== toast);
            }
        }, 400);
    }
    
    /**
     * Remove the oldest toast when limit is reached
     */
    removeOldestToast() {
        if (this.toasts.length > 0) {
            this.hide(this.toasts[0]);
        }
    }
    
    /**
     * Clear all toasts
     */
    clearAll() {
        this.toasts.forEach(toast => this.hide(toast));
    }
    
    /**
     * Bind global events
     */
    bindEvents() {
        // Keyboard accessibility
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearAll();
            }
        });
        
        // Handle window resize for mobile
        window.addEventListener('resize', () => {
            this.adjustForMobile();
        });
        
        this.adjustForMobile();
    }
    
    /**
     * Adjust toast positioning for mobile devices
     */
    adjustForMobile() {
        if (window.innerWidth <= 768) {
            this.container.style.left = '10px';
            this.container.style.right = '10px';
            this.container.style.maxWidth = 'none';
        } else {
            this.container.style.left = 'auto';
            this.container.style.right = '20px';
            this.container.style.maxWidth = '400px';
        }
    }
    
    /**
     * Convert existing Bootstrap alerts to enhanced alerts
     */
    convertExistingAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-enhanced)');
        
        alerts.forEach(alert => {
            // Add enhanced styling
            alert.classList.add('alert-enhanced');
            
            // Add icon if not present
            if (!alert.querySelector('.alert-icon')) {
                const type = this.getAlertType(alert);
                const iconMap = {
                    success: 'fas fa-check',
                    danger: 'fas fa-times',
                    warning: 'fas fa-exclamation-triangle',
                    info: 'fas fa-info'
                };
                
                const icon = document.createElement('span');
                icon.className = 'alert-icon';
                icon.innerHTML = `<i class="${iconMap[type] || iconMap.info}"></i>`;
                
                alert.insertBefore(icon, alert.firstChild);
            }
            
            // Convert to toast after a delay (optional)
            setTimeout(() => {
                const message = alert.textContent.trim();
                const type = this.getAlertType(alert);
                
                // Remove the alert
                alert.style.transition = 'all 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-20px)';
                
                setTimeout(() => {
                    if (alert.parentElement) {
                        alert.parentElement.removeChild(alert);
                    }
                    
                    // Show as toast
                    this.show(message, type === 'danger' ? 'error' : type);
                }, 300);
            }, 1000);
        });
    }
    
    /**
     * Get alert type from Bootstrap classes
     * @param {HTMLElement} alert - Alert element
     */
    getAlertType(alert) {
        if (alert.classList.contains('alert-success')) return 'success';
        if (alert.classList.contains('alert-danger')) return 'danger';
        if (alert.classList.contains('alert-warning')) return 'warning';
        if (alert.classList.contains('alert-info')) return 'info';
        return 'info';
    }
    
    /**
     * Convenience methods for different toast types
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }
    
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }
    
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }
    
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Global toast instance
let toastSystem = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    toastSystem = new EnhancedToast();
    
    // Make it globally available
    window.Toast = toastSystem;
    
    // jQuery integration if available
    if (typeof $ !== 'undefined') {
        $.toast = function(message, type = 'info', options = {}) {
            return toastSystem.show(message, type, options);
        };
        
        // Convenience methods
        $.toast.success = (message, options) => toastSystem.success(message, options);
        $.toast.error = (message, options) => toastSystem.error(message, options);
        $.toast.warning = (message, options) => toastSystem.warning(message, options);
        $.toast.info = (message, options) => toastSystem.info(message, options);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedToast;
}

/**
 * Usage Examples:
 * 
 * // Basic usage
 * Toast.success('Student registered successfully!');
 * Toast.error('Failed to save student data');
 * Toast.warning('Please fill all required fields');
 * Toast.info('Processing your request...');
 * 
 * // With options
 * Toast.show('Custom message', 'success', {
 *     duration: 3000,
 *     closable: false,
 *     showProgress: false
 * });
 * 
 * // jQuery integration
 * $.toast.success('Operation completed!');
 * $.toast('Custom message', 'warning');
 * 
 * // Manual control
 * const toast = Toast.success('Manual toast');
 * setTimeout(() => Toast.hide(toast), 2000);
 */