/**
 * Mobile Enhancements for Smart Attendance System
 * Provides touch-friendly interactions and mobile-specific features
 */

(function() {
    'use strict';

    // ===== Filter Toggle Functionality =====
    function initFilterToggle() {
        // Add toggle button to filter sections on mobile
        const filterForms = document.querySelectorAll('.card-body form.row.g-3');
        
        filterForms.forEach(form => {
            if (window.innerWidth <= 768) {
                // Check if toggle button already exists
                if (!form.parentElement.querySelector('.filter-toggle-btn')) {
                    const toggleBtn = document.createElement('button');
                    toggleBtn.type = 'button';
                    toggleBtn.className = 'filter-toggle-btn d-md-none';
                    toggleBtn.innerHTML = `
                        <span>
                            <i class="fas fa-filter me-2"></i>
                            <span class="toggle-text">Show Filters</span>
                        </span>
                        <i class="fas fa-chevron-down toggle-icon"></i>
                    `;
                    
                    // Add collapsed class to form initially
                    form.classList.add('filter-collapse-mobile', 'collapsed');
                    
                    // Insert toggle button
                    form.parentElement.insertBefore(toggleBtn, form);
                    
                    // Toggle functionality
                    toggleBtn.addEventListener('click', function() {
                        form.classList.toggle('collapsed');
                        const icon = this.querySelector('.toggle-icon');
                        const text = this.querySelector('.toggle-text');
                        
                        if (form.classList.contains('collapsed')) {
                            icon.classList.remove('fa-chevron-up');
                            icon.classList.add('fa-chevron-down');
                            text.textContent = 'Show Filters';
                        } else {
                            icon.classList.remove('fa-chevron-down');
                            icon.classList.add('fa-chevron-up');
                            text.textContent = 'Hide Filters';
                        }
                    });
                }
            }
        });
    }

    // ===== Table Responsive Enhancements =====
    function enhanceTableResponsiveness() {
        const tables = document.querySelectorAll('.table');
        
        tables.forEach(table => {
            if (window.innerWidth <= 576) {
                // Add data-label attributes to table cells for mobile view
                const headers = table.querySelectorAll('thead th');
                const rows = table.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    cells.forEach((cell, index) => {
                        if (headers[index]) {
                            const label = headers[index].textContent.trim();
                            cell.setAttribute('data-label', label);
                        }
                    });
                });
            }
        });
    }

    // ===== Mobile Navigation Enhancement =====
    function enhanceMobileNav() {
        const navbar = document.querySelector('.navbar');
        const navToggler = document.querySelector('.navbar-toggler, .glass-toggler');
        const navCollapse = document.querySelector('.navbar-collapse');
        
        if (navToggler && navCollapse) {
            // Close menu when clicking a link on mobile
            const navLinks = navCollapse.querySelectorAll('.nav-link');
            navLinks.forEach(link => {
                link.addEventListener('click', function() {
                    if (window.innerWidth < 992 && navCollapse.classList.contains('show')) {
                        navToggler.click();
                    }
                });
            });
            
            // Close menu when clicking outside on mobile
            document.addEventListener('click', function(e) {
                if (window.innerWidth < 992 && 
                    navCollapse.classList.contains('show') &&
                    !navCollapse.contains(e.target) &&
                    !navToggler.contains(e.target)) {
                    navToggler.click();
                }
            });
        }
    }

    // ===== Touch Feedback Enhancement =====
    function addTouchFeedback() {
        const touchElements = document.querySelectorAll('.btn, .nav-link, .card-clickable, .student-card');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
                this.style.opacity = '0.9';
            });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                    this.style.opacity = '';
                }, 150);
            });
        });
    }

    // ===== Button Group Mobile Enhancement =====
    function enhanceButtonGroups() {
        const buttonGroups = document.querySelectorAll('.btn-group');
        
        buttonGroups.forEach(group => {
            if (window.innerWidth <= 576) {
                // Check if buttons should stack
                const buttons = group.querySelectorAll('.btn');
                if (buttons.length > 2) {
                    group.classList.add('mobile-stack');
                }
            }
        });
    }

    // ===== Card View Toggle Enhancement =====
    function enhanceViewToggle() {
        const gridViewBtn = document.getElementById('gridViewBtn');
        const listViewBtn = document.getElementById('listViewBtn');
        const gridView = document.getElementById('gridView');
        const listView = document.getElementById('listView');
        
        if (gridViewBtn && listViewBtn) {
            // Set default view based on screen size
            if (window.innerWidth <= 576) {
                // Default to list view on mobile
                if (gridView && listView && gridViewBtn.classList.contains('active')) {
                    listViewBtn.click();
                }
            }
        }
    }

    // ===== Dashboard Cards Mobile Optimization =====
    function optimizeDashboardCards() {
        const statsCards = document.querySelectorAll('.col-lg-3.col-md-6');
        
        if (window.innerWidth <= 768) {
            statsCards.forEach(card => {
                // Adjust icon sizes
                const icons = card.querySelectorAll('.icon-container');
                icons.forEach(icon => {
                    icon.style.width = '60px';
                    icon.style.height = '60px';
                });
                
                // Adjust font sizes
                const displayText = card.querySelectorAll('.display-6, .display-4');
                displayText.forEach(text => {
                    if (text.classList.contains('display-4')) {
                        text.style.fontSize = '2rem';
                    } else if (text.classList.contains('display-6')) {
                        text.style.fontSize = '1.75rem';
                    }
                });
            });
        }
    }

    // ===== Quick Filter Buttons Mobile Enhancement =====
    function enhanceQuickFilters() {
        const quickFilterContainer = document.querySelector('.d-flex.flex-wrap.gap-2');
        
        if (quickFilterContainer && window.innerWidth <= 576) {
            // Make quick filters more touch-friendly
            const filterButtons = quickFilterContainer.querySelectorAll('.btn');
            filterButtons.forEach(btn => {
                btn.style.minHeight = '44px';
                btn.style.padding = '0.5rem 1rem';
            });
        }
    }

    // ===== Smooth Scroll Enhancement =====
    function enableSmoothScroll() {
        // Add smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
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
            });
        });
    }

    // ===== Resize Handler =====
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            initFilterToggle();
            enhanceTableResponsiveness();
            enhanceButtonGroups();
            optimizeDashboardCards();
            enhanceQuickFilters();
        }, 250);
    });

    // ===== Initialize All Enhancements =====
    function init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initializeEnhancements();
            });
        } else {
            initializeEnhancements();
        }
    }

    function initializeEnhancements() {
        initFilterToggle();
        enhanceTableResponsiveness();
        enhanceMobileNav();
        addTouchFeedback();
        enhanceButtonGroups();
        enhanceViewToggle();
        optimizeDashboardCards();
        enhanceQuickFilters();
        enableSmoothScroll();
        
        console.log('✅ Mobile enhancements initialized');
    }

    // Start initialization
    init();

})();
