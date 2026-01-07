/* Mobile Touch Interactions and Swipe Gestures */
/* Enhanced mobile experience with touch-friendly interactions */

(function() {
    'use strict';
    
    // Mobile interaction configuration
    const config = {
        swipeThreshold: 50,
        swipeVelocity: 0.3,
        touchFeedbackDuration: 300,
        debounceDelay: 100
    };
    
    // Touch interaction state
    let touchState = {
        startX: 0,
        startY: 0,
        startTime: 0,
        isScrolling: false,
        activeElement: null
    };
    
    // Initialize mobile interactions when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeMobileInteractions();
    });
    
    /**
     * Initialize all mobile interaction features
     */
    function initializeMobileInteractions() {
        setupTouchFeedback();
        setupSwipeGestures();
        setupMobileNavigation();
        setupMobileCards();
        setupMobileForms();
        setupMobileModals();
        setupOrientationHandling();
        setupSafeAreaSupport();
        
        console.log('Mobile interactions initialized');
    }
    
    /**
     * Setup touch feedback for interactive elements
     */
    function setupTouchFeedback() {
        const touchElements = document.querySelectorAll('.btn, .nav-link, .card-clickable, .dropdown-item');
        
        touchElements.forEach(element => {
            if (!element.classList.contains('touch-feedback')) {
                element.classList.add('touch-feedback');
            }
            
            // Add touch start handler
            element.addEventListener('touchstart', handleTouchStart, { passive: true });
            element.addEventListener('touchend', handleTouchEnd, { passive: true });
            element.addEventListener('touchcancel', handleTouchCancel, { passive: true });
        });
    }
    
    /**
     * Handle touch start events
     */
    function handleTouchStart(event) {
        const element = event.currentTarget;
        touchState.activeElement = element;
        
        // Add active class for visual feedback
        element.classList.add('touch-active');
        
        // Create ripple effect
        createRippleEffect(element, event.touches[0]);
        
        // Haptic feedback if supported
        if (navigator.vibrate) {
            navigator.vibrate(10);
        }
    }
    
    /**
     * Handle touch end events
     */
    function handleTouchEnd(event) {
        const element = event.currentTarget;
        
        // Remove active class after delay
        setTimeout(() => {
            element.classList.remove('touch-active');
        }, config.touchFeedbackDuration);
        
        touchState.activeElement = null;
    }
    
    /**
     * Handle touch cancel events
     */
    function handleTouchCancel(event) {
        const element = event.currentTarget;
        element.classList.remove('touch-active');
        touchState.activeElement = null;
    }
    
    /**
     * Create ripple effect for touch feedback
     */
    function createRippleEffect(element, touch) {
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('div');
        const size = Math.max(rect.width, rect.height);
        const x = touch.clientX - rect.left - size / 2;
        const y = touch.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
            z-index: 1000;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }
    
    /**
     * Setup swipe gestures for cards and navigation
     */
    function setupSwipeGestures() {
        const swipeableElements = document.querySelectorAll('.swipeable, .student-card, .attendance-record');
        
        swipeableElements.forEach(element => {
            element.addEventListener('touchstart', handleSwipeStart, { passive: false });
            element.addEventListener('touchmove', handleSwipeMove, { passive: false });
            element.addEventListener('touchend', handleSwipeEnd, { passive: false });
        });
        
        // Setup navigation swipe
        setupNavigationSwipe();
    }
    
    /**
     * Handle swipe start
     */
    function handleSwipeStart(event) {
        const touch = event.touches[0];
        touchState.startX = touch.clientX;
        touchState.startY = touch.clientY;
        touchState.startTime = Date.now();
        touchState.isScrolling = false;
        
        // Add swipe indicators if element supports swipe actions
        const element = event.currentTarget;
        if (element.dataset.swipeActions) {
            showSwipeIndicators(element);
        }
    }
    
    /**
     * Handle swipe move
     */
    function handleSwipeMove(event) {
        if (!touchState.startX || !touchState.startY) return;
        
        const touch = event.touches[0];
        const deltaX = touch.clientX - touchState.startX;
        const deltaY = touch.clientY - touchState.startY;
        
        // Determine if this is a scroll gesture
        if (!touchState.isScrolling) {
            touchState.isScrolling = Math.abs(deltaY) > Math.abs(deltaX);
        }
        
        // If scrolling, don't handle swipe
        if (touchState.isScrolling) return;
        
        // Prevent default to avoid scrolling
        event.preventDefault();
        
        const element = event.currentTarget;
        const maxSwipe = element.offsetWidth * 0.3;
        const swipeDistance = Math.min(Math.abs(deltaX), maxSwipe);
        const direction = deltaX > 0 ? 'right' : 'left';
        
        // Apply transform for visual feedback
        element.style.transform = `translateX(${deltaX * 0.5}px)`;
        element.style.transition = 'none';
        
        // Update swipe indicators
        updateSwipeIndicators(element, direction, swipeDistance / maxSwipe);
    }
    
    /**
     * Handle swipe end
     */
    function handleSwipeEnd(event) {
        const element = event.currentTarget;
        const deltaX = event.changedTouches[0].clientX - touchState.startX;
        const deltaY = event.changedTouches[0].clientY - touchState.startY;
        const deltaTime = Date.now() - touchState.startTime;
        const velocity = Math.abs(deltaX) / deltaTime;
        
        // Reset transform
        element.style.transform = '';
        element.style.transition = '';
        
        // Hide swipe indicators
        hideSwipeIndicators(element);
        
        // Check if this was a valid swipe
        if (!touchState.isScrolling && 
            Math.abs(deltaX) > config.swipeThreshold && 
            velocity > config.swipeVelocity) {
            
            const direction = deltaX > 0 ? 'right' : 'left';
            handleSwipeAction(element, direction);
        }
        
        // Reset touch state
        touchState = {
            startX: 0,
            startY: 0,
            startTime: 0,
            isScrolling: false,
            activeElement: null
        };
    }
    
    /**
     * Show swipe indicators
     */
    function showSwipeIndicators(element) {
        const actions = JSON.parse(element.dataset.swipeActions || '{}');
        
        Object.keys(actions).forEach(direction => {
            let indicator = element.querySelector(`.swipe-indicator.${direction}`);
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = `swipe-indicator ${direction}`;
                indicator.innerHTML = `<i class="fas fa-${actions[direction].icon}"></i>`;
                element.appendChild(indicator);
            }
            indicator.classList.add('active');
        });
    }
    
    /**
     * Update swipe indicators based on swipe progress
     */
    function updateSwipeIndicators(element, direction, progress) {
        const indicator = element.querySelector(`.swipe-indicator.${direction}`);
        if (indicator) {
            const scale = 1 + (progress * 0.5);
            indicator.style.transform = `translateY(-50%) scale(${scale})`;
            indicator.style.opacity = Math.min(progress * 2, 1);
        }
    }
    
    /**
     * Hide swipe indicators
     */
    function hideSwipeIndicators(element) {
        const indicators = element.querySelectorAll('.swipe-indicator');
        indicators.forEach(indicator => {
            indicator.classList.remove('active');
            indicator.style.transform = '';
            indicator.style.opacity = '';
        });
    }
    
    /**
     * Handle swipe actions
     */
    function handleSwipeAction(element, direction) {
        const actions = JSON.parse(element.dataset.swipeActions || '{}');
        const action = actions[direction];
        
        if (action) {
            // Trigger the action
            if (action.callback && window[action.callback]) {
                window[action.callback](element, direction);
            } else if (action.url) {
                window.location.href = action.url;
            } else if (action.event) {
                element.dispatchEvent(new CustomEvent(action.event, {
                    detail: { direction, element }
                }));
            }
            
            // Visual feedback
            element.style.transform = `translateX(${direction === 'right' ? '100%' : '-100%'})`;
            element.style.transition = 'transform 0.3s ease-out';
            element.style.opacity = '0.5';
            
            // Reset after animation
            setTimeout(() => {
                element.style.transform = '';
                element.style.transition = '';
                element.style.opacity = '';
            }, 300);
        }
    }
    
    /**
     * Setup navigation swipe for mobile menu
     */
    function setupNavigationSwipe() {
        const navbar = document.querySelector('.navbar-collapse');
        if (!navbar) return;
        
        let startX = 0;
        let isOpen = false;
        
        document.addEventListener('touchstart', (event) => {
            startX = event.touches[0].clientX;
            isOpen = navbar.classList.contains('show');
        }, { passive: true });
        
        document.addEventListener('touchmove', (event) => {
            const currentX = event.touches[0].clientX;
            const deltaX = currentX - startX;
            
            // Swipe right from left edge to open menu
            if (!isOpen && startX < 50 && deltaX > 50) {
                const toggler = document.querySelector('.navbar-toggler');
                if (toggler && !navbar.classList.contains('show')) {
                    toggler.click();
                }
            }
            
            // Swipe left to close menu
            if (isOpen && deltaX < -50) {
                const toggler = document.querySelector('.navbar-toggler');
                if (toggler && navbar.classList.contains('show')) {
                    toggler.click();
                }
            }
        }, { passive: true });
    }
    
    /**
     * Setup mobile navigation enhancements
     */
    function setupMobileNavigation() {
        const navLinks = document.querySelectorAll('.nav-link-enhanced');
        
        navLinks.forEach(link => {
            // Add touch-friendly spacing
            link.style.minHeight = '44px';
            
            // Enhanced touch feedback
            link.addEventListener('touchstart', function() {
                this.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
            }, { passive: true });
            
            link.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.backgroundColor = '';
                }, 150);
            }, { passive: true });
        });
        
        // Auto-close mobile menu on link click
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) {
                    const navbar = document.querySelector('.navbar-collapse');
                    const toggler = document.querySelector('.navbar-toggler');
                    
                    if (navbar && navbar.classList.contains('show')) {
                        setTimeout(() => {
                            toggler.click();
                        }, 100);
                    }
                }
            });
        });
    }
    
    /**
     * Setup mobile card interactions
     */
    function setupMobileCards() {
        const cards = document.querySelectorAll('.card, .student-card, .stats-card');
        
        cards.forEach(card => {
            // Add touch feedback
            card.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                this.style.transition = 'transform 0.1s ease';
            }, { passive: true });
            
            card.addEventListener('touchend', function() {
                this.style.transform = '';
                this.style.transition = '';
            }, { passive: true });
            
            // Add swipe actions for student cards
            if (card.classList.contains('student-card')) {
                card.dataset.swipeActions = JSON.stringify({
                    left: { icon: 'edit', event: 'editStudent' },
                    right: { icon: 'trash', event: 'deleteStudent' }
                });
                card.classList.add('swipeable');
            }
        });
    }
    
    /**
     * Setup mobile form enhancements
     */
    function setupMobileForms() {
        const formControls = document.querySelectorAll('.form-control, .form-select');
        
        formControls.forEach(control => {
            // Ensure minimum touch target size
            if (control.offsetHeight < 44) {
                control.style.minHeight = '44px';
                control.style.padding = '0.75rem 1rem';
            }
            
            // Enhanced focus handling for mobile
            control.addEventListener('focus', function() {
                // Scroll element into view on mobile
                if (window.innerWidth < 768) {
                    setTimeout(() => {
                        this.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });
                    }, 300);
                }
            });
        });
        
        // File input enhancements for mobile
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', function() {
                // Add haptic feedback
                if (navigator.vibrate) {
                    navigator.vibrate(50);
                }
            });
        });
    }
    
    /**
     * Setup mobile modal enhancements
     */
    function setupMobileModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', function() {
                // Focus management for mobile
                const firstInput = this.querySelector('input, select, textarea, button');
                if (firstInput && window.innerWidth < 768) {
                    setTimeout(() => {
                        firstInput.focus();
                    }, 300);
                }
            });
            
            // Swipe down to close modal on mobile
            let startY = 0;
            const modalContent = modal.querySelector('.modal-content');
            
            if (modalContent) {
                modalContent.addEventListener('touchstart', (event) => {
                    startY = event.touches[0].clientY;
                }, { passive: true });
                
                modalContent.addEventListener('touchmove', (event) => {
                    const currentY = event.touches[0].clientY;
                    const deltaY = currentY - startY;
                    
                    // Only allow swipe down from top of modal
                    if (startY < 100 && deltaY > 100) {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                    }
                }, { passive: true });
            }
        });
    }
    
    /**
     * Setup orientation change handling
     */
    function setupOrientationHandling() {
        window.addEventListener('orientationchange', function() {
            // Delay to allow orientation change to complete
            setTimeout(() => {
                // Recalculate viewport height
                document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
                
                // Trigger resize event for components that need it
                window.dispatchEvent(new Event('resize'));
                
                // Close mobile menu if open
                const navbar = document.querySelector('.navbar-collapse');
                const toggler = document.querySelector('.navbar-toggler');
                
                if (navbar && navbar.classList.contains('show')) {
                    toggler.click();
                }
            }, 100);
        });
        
        // Initial viewport height calculation
        document.documentElement.style.setProperty('--vh', `${window.innerHeight * 0.01}px`);
    }
    
    /**
     * Setup safe area support for devices with notches
     */
    function setupSafeAreaSupport() {
        // Check if device supports safe areas
        if (CSS.supports('padding: max(0px)')) {
            document.documentElement.classList.add('safe-area-supported');
            
            // Apply safe area insets to key elements
            const safeAreaElements = document.querySelectorAll('.glass-nav, .container, .toast-container');
            safeAreaElements.forEach(element => {
                element.classList.add('safe-area-aware');
            });
        }
    }
    
    /**
     * Utility function to detect if device is mobile
     */
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (navigator.maxTouchPoints && navigator.maxTouchPoints > 2);
    }
    
    /**
     * Utility function to detect touch capability
     */
    function isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    /**
     * Debounce function for performance
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
    
    // Add CSS for ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .touch-active {
            transform: scale(0.98) !important;
            transition: transform 0.1s ease !important;
        }
        
        .safe-area-aware {
            padding-left: max(1rem, env(safe-area-inset-left)) !important;
            padding-right: max(1rem, env(safe-area-inset-right)) !important;
        }
        
        .safe-area-supported .glass-nav {
            padding-top: max(0.5rem, env(safe-area-inset-top)) !important;
        }
        
        .safe-area-supported .toast-container {
            bottom: max(2rem, env(safe-area-inset-bottom) + 1rem) !important;
        }
    `;
    document.head.appendChild(style);
    
    // Export functions for global access
    window.MobileInteractions = {
        setupTouchFeedback,
        setupSwipeGestures,
        isMobileDevice,
        isTouchDevice,
        config
    };
    
})();