/**
 * Enhanced Forms JavaScript
 * Provides interactive functionality for the enhanced form system
 */

(function() {
    'use strict';

    // Initialize enhanced forms when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeEnhancedForms();
        initializeFormValidation();
        initializeFormAnimations();
        initializeAccessibility();
    });

    /**
     * Initialize enhanced form functionality
     */
    function initializeEnhancedForms() {
        // Handle floating labels for dynamically filled inputs
        const formControls = document.querySelectorAll('.form-control-glass, .form-select-glass');
        formControls.forEach(control => {
            // Check if input has value on load
            checkFloatingLabel(control);
            
            // Add event listeners
            control.addEventListener('input', function() {
                checkFloatingLabel(this);
            });
            
            control.addEventListener('change', function() {
                checkFloatingLabel(this);
            });
            
            // Add focus animations
            control.addEventListener('focus', function() {
                this.closest('.form-floating-glass')?.classList.add('focused');
                addFocusRing(this);
            });
            
            control.addEventListener('blur', function() {
                this.closest('.form-floating-glass')?.classList.remove('focused');
            });
        });
    }

    /**
     * Check and update floating label state
     */
    function checkFloatingLabel(element) {
        const container = element.closest('.form-floating-glass');
        if (!container) return;
        
        const label = container.querySelector('label');
        if (!label) return;
        
        // Check if element has value
        const hasValue = element.value && element.value.trim() !== '';
        const isSelect = element.tagName === 'SELECT';
        const isSelectWithValue = isSelect && element.value !== '';
        
        if (hasValue || isSelectWithValue) {
            label.classList.add('active');
        } else {
            label.classList.remove('active');
        }
    }

    /**
     * Add focus ring animation
     */
    function addFocusRing(element) {
        element.style.animation = 'focusRing 0.6s ease-out';
        element.addEventListener('animationend', function() {
            this.style.animation = '';
        }, { once: true });
    }

    /**
     * Initialize form validation
     */
    function initializeFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validateForm(this)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                this.classList.add('was-validated');
            });
        });

        // Real-time validation
        const validatableInputs = document.querySelectorAll('.form-control-glass[required], .form-select-glass[required]');
        validatableInputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    }

    /**
     * Validate individual field
     */
    function validateField(field) {
        const isValid = field.checkValidity();
        const container = field.closest('.form-floating-glass') || field.parentElement;
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Add appropriate validation class
        if (isValid && field.value.trim() !== '') {
            field.classList.add('is-valid');
            showValidationMessage(container, 'valid', 'Looks good!');
        } else if (!isValid) {
            field.classList.add('is-invalid');
            showValidationMessage(container, 'invalid', field.validationMessage);
        }
        
        return isValid;
    }

    /**
     * Validate entire form
     */
    function validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('.form-control-glass[required], .form-select-glass[required]');
        let invalidCount = 0;
        
        requiredFields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
                invalidCount++;
            }
        });
        
        // Show toast notification for validation results
        if (!isValid && window.Toast) {
            const message = invalidCount === 1 
                ? 'Please fill the required field correctly.' 
                : `Please fill all ${invalidCount} required fields correctly.`;
            window.Toast.warning(message, { duration: 4000 });
        }
        
        return isValid;
    }

    /**
     * Show validation message
     */
    function showValidationMessage(container, type, message) {
        // Remove existing feedback
        const existingFeedback = container.querySelector('.valid-feedback, .invalid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        // Create new feedback element
        const feedback = document.createElement('div');
        feedback.className = type === 'valid' ? 'valid-feedback' : 'invalid-feedback';
        feedback.textContent = message;
        feedback.style.display = 'block';
        
        container.appendChild(feedback);
        
        // Animate in
        feedback.style.animation = 'slideInUp 0.3s ease-out';
    }

    /**
     * Initialize form animations
     */
    function initializeFormAnimations() {
        // Button hover effects
        const enhancedButtons = document.querySelectorAll('.btn-enhanced');
        enhancedButtons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = '';
            });
            
            button.addEventListener('mousedown', function() {
                this.style.transform = 'translateY(0)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'translateY(-2px)';
            });
        });

        // Enhanced checkbox animations
        const enhancedCheckboxes = document.querySelectorAll('.form-check-enhanced .form-check-input');
        enhancedCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const label = this.nextElementSibling;
                if (this.checked) {
                    label.style.animation = 'pulse 0.3s ease-out';
                }
                label.addEventListener('animationend', function() {
                    this.style.animation = '';
                }, { once: true });
            });
        });
    }

    /**
     * Initialize accessibility features
     */
    function initializeAccessibility() {
        // Keyboard navigation for custom elements
        const customControls = document.querySelectorAll('.btn-enhanced, .form-check-enhanced .form-check-input');
        customControls.forEach(control => {
            control.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    if (this.type === 'checkbox') {
                        this.checked = !this.checked;
                        this.dispatchEvent(new Event('change'));
                    } else if (this.tagName === 'BUTTON') {
                        this.click();
                    }
                }
            });
        });

        // Enhanced focus indicators
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', function() {
            document.body.classList.remove('keyboard-navigation');
        });

        // Screen reader announcements for validation
        const validationObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const element = mutation.target;
                    if (element.classList.contains('is-invalid')) {
                        announceToScreenReader('Form field has an error: ' + element.validationMessage);
                    } else if (element.classList.contains('is-valid')) {
                        announceToScreenReader('Form field is valid');
                    }
                }
            });
        });

        // Observe form controls for validation changes
        const formControls = document.querySelectorAll('.form-control-glass, .form-select-glass');
        formControls.forEach(control => {
            validationObserver.observe(control, { attributes: true });
        });
    }

    /**
     * Announce message to screen readers
     */
    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    /**
     * Utility function to debounce events
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Show success message for form submission
     */
    function showFormSuccess(message) {
        if (window.Toast) {
            window.Toast.success(message || 'Form submitted successfully!');
        }
    }

    /**
     * Show error message for form submission
     */
    function showFormError(message) {
        if (window.Toast) {
            window.Toast.error(message || 'An error occurred while submitting the form.');
        }
    }

    /**
     * Public API for external use
     */
    window.EnhancedForms = {
        validateField: validateField,
        validateForm: validateForm,
        checkFloatingLabel: checkFloatingLabel,
        announceToScreenReader: announceToScreenReader,
        showSuccess: showFormSuccess,
        showError: showFormError
    };

})();