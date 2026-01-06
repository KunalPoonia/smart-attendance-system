/* ===== ACCESSIBILITY ENHANCEMENTS JAVASCRIPT ===== */
/* Comprehensive accessibility improvements for Smart Attendance System */

(function() {
    'use strict';

    // ===== INITIALIZATION =====
    document.addEventListener('DOMContentLoaded', function() {
        initializeAccessibility();
    });

    function initializeAccessibility() {
        addSkipToMainContent();
        enhanceKeyboardNavigation();
        addAriaLabelsAndRoles();
        setupFocusManagement();
        enhanceFormAccessibility();
        setupScreenReaderAnnouncements();
        handleReducedMotionPreferences();
        setupAccessibleTooltips();
        enhanceTableAccessibility();
        setupAccessibleModals();
        addLiveRegions();
        console.log('Accessibility enhancements initialized');
    }

    // ===== SKIP TO MAIN CONTENT =====
    function addSkipToMainContent() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-to-main';
        skipLink.textContent = 'Skip to main content';
        skipLink.setAttribute('aria-label', 'Skip to main content');
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Add main content ID if it doesn't exist
        const mainContent = document.querySelector('main') || document.querySelector('.container').parentElement;
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
            mainContent.setAttribute('tabindex', '-1');
        }
        
        // Handle skip link click
        skipLink.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.getElementById('main-content');
            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }

    // ===== KEYBOARD NAVIGATION ENHANCEMENTS =====
    function enhanceKeyboardNavigation() {
        // Add keyboard support for custom interactive elements
        const interactiveElements = document.querySelectorAll(
            '.card-clickable, .student-card, .attendance-card, .stats-card, [data-clickable="true"]'
        );
        
        interactiveElements.forEach(element => {
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
            
            if (!element.hasAttribute('role')) {
                element.setAttribute('role', 'button');
            }
            
            element.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
        
        // Enhanced navigation for dropdown menus
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        dropdownToggles.forEach(toggle => {
            toggle.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    const menu = this.nextElementSibling;
                    if (menu) {
                        const firstItem = menu.querySelector('.dropdown-item');
                        if (firstItem) {
                            firstItem.focus();
                        }
                    }
                }
            });
        });
        
        // Arrow key navigation in dropdown menus
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach((item, index, items) => {
            item.addEventListener('keydown', function(e) {
                let nextIndex;
                switch(e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        nextIndex = (index + 1) % items.length;
                        items[nextIndex].focus();
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        nextIndex = (index - 1 + items.length) % items.length;
                        items[nextIndex].focus();
                        break;
                    case 'Escape':
                        e.preventDefault();
                        const toggle = this.closest('.dropdown').querySelector('.dropdown-toggle');
                        if (toggle) {
                            toggle.focus();
                            // Close dropdown
                            const dropdown = bootstrap.Dropdown.getInstance(toggle);
                            if (dropdown) {
                                dropdown.hide();
                            }
                        }
                        break;
                }
            });
        });
    }

    // ===== ARIA LABELS AND ROLES =====
    function addAriaLabelsAndRoles() {
        // Add ARIA labels to navigation
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.setAttribute('role', 'navigation');
            navbar.setAttribute('aria-label', 'Main navigation');
        }
        
        // Add ARIA labels to buttons without text
        const iconButtons = document.querySelectorAll('button:not([aria-label]) i.fa');
        iconButtons.forEach(icon => {
            const button = icon.closest('button');
            if (button && !button.getAttribute('aria-label')) {
                const iconClass = icon.className;
                let label = 'Button';
                
                if (iconClass.includes('fa-edit')) label = 'Edit';
                else if (iconClass.includes('fa-trash')) label = 'Delete';
                else if (iconClass.includes('fa-eye')) label = 'View';
                else if (iconClass.includes('fa-download')) label = 'Download';
                else if (iconClass.includes('fa-upload')) label = 'Upload';
                else if (iconClass.includes('fa-search')) label = 'Search';
                else if (iconClass.includes('fa-filter')) label = 'Filter';
                else if (iconClass.includes('fa-sort')) label = 'Sort';
                else if (iconClass.includes('fa-camera')) label = 'Camera';
                else if (iconClass.includes('fa-user-plus')) label = 'Add student';
                else if (iconClass.includes('fa-check')) label = 'Confirm';
                else if (iconClass.includes('fa-times')) label = 'Cancel';
                
                button.setAttribute('aria-label', label);
            }
        });
        
        // Add ARIA labels to form controls
        const formControls = document.querySelectorAll('.form-control:not([aria-label]):not([aria-labelledby])');
        formControls.forEach(control => {
            const label = control.closest('.form-group, .mb-3, .floating-label-group')?.querySelector('label');
            if (label) {
                if (!label.id) {
                    label.id = 'label-' + Math.random().toString(36).substr(2, 9);
                }
                control.setAttribute('aria-labelledby', label.id);
            }
        });
        
        // Add ARIA labels to cards
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const title = card.querySelector('.card-title, h1, h2, h3, h4, h5, h6');
            if (title && !card.getAttribute('aria-label')) {
                card.setAttribute('aria-label', title.textContent.trim());
            }
        });
        
        // Add ARIA labels to statistics cards
        const statsCards = document.querySelectorAll('.stats-card, .stat-card');
        statsCards.forEach(card => {
            const value = card.querySelector('.stat-value, .card-text');
            const label = card.querySelector('.stat-label, .card-title');
            if (value && label) {
                card.setAttribute('aria-label', `${label.textContent.trim()}: ${value.textContent.trim()}`);
            }
        });
        
        // Add ARIA roles to custom components
        const customComponents = {
            '.toast-container': 'region',
            '.breadcrumb': 'navigation',
            '.pagination': 'navigation',
            '.alert': 'alert',
            '.progress': 'progressbar'
        };
        
        Object.entries(customComponents).forEach(([selector, role]) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                if (!element.getAttribute('role')) {
                    element.setAttribute('role', role);
                }
            });
        });
        
        // Add ARIA expanded states to collapsible elements
        const collapsibleToggles = document.querySelectorAll('[data-bs-toggle="collapse"]');
        collapsibleToggles.forEach(toggle => {
            const target = document.querySelector(toggle.getAttribute('data-bs-target'));
            if (target) {
                const isExpanded = target.classList.contains('show');
                toggle.setAttribute('aria-expanded', isExpanded.toString());
                
                // Update on toggle
                toggle.addEventListener('click', function() {
                    setTimeout(() => {
                        const isNowExpanded = target.classList.contains('show');
                        this.setAttribute('aria-expanded', isNowExpanded.toString());
                    }, 100);
                });
            }
        });
    }

    // ===== FOCUS MANAGEMENT =====
    function setupFocusManagement() {
        // Focus trap for modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', function() {
                trapFocus(this);
                const firstFocusable = this.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
            });
            
            modal.addEventListener('hidden.bs.modal', function() {
                const trigger = document.querySelector(`[data-bs-target="#${this.id}"]`);
                if (trigger) {
                    trigger.focus();
                }
            });
        });
        
        // Focus management for toast notifications
        function focusToast(toast) {
            if (toast && toast.getAttribute('role') === 'alert') {
                toast.setAttribute('tabindex', '-1');
                toast.focus();
            }
        }
        
        // Observe for new toast notifications
        const toastContainer = document.querySelector('.toast-container');
        if (toastContainer) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList.contains('toast')) {
                            setTimeout(() => focusToast(node), 100);
                        }
                    });
                });
            });
            observer.observe(toastContainer, { childList: true });
        }
    }

    // ===== FOCUS TRAP UTILITY =====
    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        });
    }

    // ===== FORM ACCESSIBILITY ENHANCEMENTS =====
    function enhanceFormAccessibility() {
        // Add required indicators
        const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
        requiredFields.forEach(field => {
            const label = document.querySelector(`label[for="${field.id}"]`) || 
                         field.closest('.form-group, .mb-3')?.querySelector('label');
            if (label && !label.classList.contains('required')) {
                label.classList.add('required');
                label.setAttribute('aria-required', 'true');
            }
            field.setAttribute('aria-required', 'true');
        });
        
        // Enhanced form validation
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const invalidFields = this.querySelectorAll(':invalid');
                if (invalidFields.length > 0) {
                    e.preventDefault();
                    const firstInvalid = invalidFields[0];
                    firstInvalid.focus();
                    announceToScreenReader(`Form has ${invalidFields.length} error${invalidFields.length > 1 ? 's' : ''}. Please correct and try again.`);
                }
            });
        });
        
        // Real-time validation feedback
        const validatableFields = document.querySelectorAll('input, select, textarea');
        validatableFields.forEach(field => {
            field.addEventListener('blur', function() {
                validateField(this);
            });
            
            field.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    }

    // ===== FIELD VALIDATION =====
    function validateField(field) {
        const isValid = field.checkValidity();
        const feedbackContainer = field.parentNode.querySelector('.invalid-feedback') || 
                                field.parentNode.querySelector('.valid-feedback');
        
        // Remove existing feedback
        field.classList.remove('is-valid', 'is-invalid');
        if (feedbackContainer) {
            feedbackContainer.remove();
        }
        
        // Add new feedback
        const feedback = document.createElement('div');
        feedback.className = isValid ? 'valid-feedback' : 'invalid-feedback';
        feedback.setAttribute('role', 'alert');
        feedback.setAttribute('aria-live', 'polite');
        
        if (isValid) {
            feedback.textContent = 'Valid input';
            field.classList.add('is-valid');
        } else {
            feedback.textContent = field.validationMessage || 'Invalid input';
            field.classList.add('is-invalid');
            field.setAttribute('aria-describedby', feedback.id = 'feedback-' + Math.random().toString(36).substr(2, 9));
        }
        
        field.parentNode.appendChild(feedback);
    }

    // ===== SCREEN READER ANNOUNCEMENTS =====
    function setupScreenReaderAnnouncements() {
        // Create live region for announcements
        if (!document.getElementById('sr-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'sr-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        // Announce page changes
        const originalTitle = document.title;
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.target === document.head) {
                    const newTitle = document.title;
                    if (newTitle !== originalTitle) {
                        announceToScreenReader(`Page changed to ${newTitle}`);
                    }
                }
            });
        });
        observer.observe(document.head, { childList: true, subtree: true });
    }

    // ===== SCREEN READER ANNOUNCEMENT UTILITY =====
    function announceToScreenReader(message) {
        const liveRegion = document.getElementById('sr-live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    // ===== REDUCED MOTION PREFERENCES =====
    function handleReducedMotionPreferences() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        function updateMotionPreference(mediaQuery) {
            if (mediaQuery.matches) {
                document.body.classList.add('reduce-motion');
                announceToScreenReader('Animations disabled for accessibility');
            } else {
                document.body.classList.remove('reduce-motion');
            }
        }
        
        updateMotionPreference(prefersReducedMotion);
        prefersReducedMotion.addEventListener('change', updateMotionPreference);
    }

    // ===== ACCESSIBLE TOOLTIPS =====
    function setupAccessibleTooltips() {
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipElements.forEach(element => {
            element.setAttribute('aria-describedby', element.getAttribute('data-bs-target') || 'tooltip-' + Math.random().toString(36).substr(2, 9));
            
            element.addEventListener('mouseenter', function() {
                announceToScreenReader(this.getAttribute('title') || this.getAttribute('data-bs-original-title'));
            });
        });
    }

    // ===== TABLE ACCESSIBILITY =====
    function enhanceTableAccessibility() {
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {
            // Add table role and caption if missing
            if (!table.getAttribute('role')) {
                table.setAttribute('role', 'table');
            }
            
            if (!table.querySelector('caption')) {
                const caption = document.createElement('caption');
                caption.textContent = 'Data table';
                caption.className = 'sr-only';
                table.insertBefore(caption, table.firstChild);
            }
            
            // Add scope attributes to headers
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {
                if (!header.getAttribute('scope')) {
                    const isInThead = header.closest('thead');
                    header.setAttribute('scope', isInThead ? 'col' : 'row');
                }
            });
            
            // Add row and column headers
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                row.setAttribute('role', 'row');
                const cells = row.querySelectorAll('td, th');
                cells.forEach(cell => {
                    cell.setAttribute('role', cell.tagName.toLowerCase() === 'th' ? 'rowheader' : 'cell');
                });
            });
        });
    }

    // ===== ACCESSIBLE MODALS =====
    function setupAccessibleModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            // Add ARIA attributes
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            
            const title = modal.querySelector('.modal-title');
            if (title && !modal.getAttribute('aria-labelledby')) {
                if (!title.id) {
                    title.id = 'modal-title-' + Math.random().toString(36).substr(2, 9);
                }
                modal.setAttribute('aria-labelledby', title.id);
            }
            
            // Handle escape key
            modal.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    const modalInstance = bootstrap.Modal.getInstance(this);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                }
            });
        });
    }

    // ===== LIVE REGIONS =====
    function addLiveRegions() {
        // Add live regions for dynamic content
        const dynamicContainers = document.querySelectorAll('.toast-container, .alert-container, .loading-container');
        dynamicContainers.forEach(container => {
            if (!container.getAttribute('aria-live')) {
                container.setAttribute('aria-live', 'polite');
                container.setAttribute('aria-atomic', 'false');
            }
        });
        
        // Add live region for search results
        const searchContainers = document.querySelectorAll('.search-results, .filter-results');
        searchContainers.forEach(container => {
            container.setAttribute('aria-live', 'polite');
            container.setAttribute('aria-atomic', 'true');
        });
    }

    // ===== UTILITY FUNCTIONS =====
    
    // Check if element is visible
    function isElementVisible(element) {
        return element.offsetWidth > 0 && element.offsetHeight > 0;
    }
    
    // Get all focusable elements
    function getFocusableElements(container) {
        return container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
    }
    
    // Announce loading states
    function announceLoadingState(isLoading, message = '') {
        const defaultMessage = isLoading ? 'Loading content' : 'Content loaded';
        announceToScreenReader(message || defaultMessage);
    }
    
    // Export utility functions for use in other scripts
    window.AccessibilityUtils = {
        announceToScreenReader,
        announceLoadingState,
        validateField,
        trapFocus,
        getFocusableElements,
        isElementVisible
    };

    // ===== INTEGRATION WITH EXISTING COMPONENTS =====
    
    // Enhance existing toast notifications
    document.addEventListener('DOMContentLoaded', function() {
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => {
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
        });
    });
    
    // Enhance existing loading states
    document.addEventListener('DOMContentLoaded', function() {
        const loadingElements = document.querySelectorAll('.loading, .spinner-border, .loading-spinner');
        loadingElements.forEach(element => {
            element.setAttribute('role', 'status');
            element.setAttribute('aria-label', 'Loading');
            
            if (!element.querySelector('.sr-only')) {
                const srText = document.createElement('span');
                srText.className = 'sr-only';
                srText.textContent = 'Loading...';
                element.appendChild(srText);
            }
        });
    });

})();