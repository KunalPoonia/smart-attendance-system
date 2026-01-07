/**
 * Loading States and Skeleton Screens JavaScript
 * Provides comprehensive loading state management with smooth transitions
 */

class LoadingStates {
    constructor() {
        this.activeLoaders = new Set();
        this.init();
    }

    init() {
        // Initialize loading state management
        this.createProgressGradient();
        this.setupGlobalLoadingHandlers();
        this.observeFormSubmissions();
        this.observeAjaxRequests();
    }

    /**
     * Create SVG gradient for circular progress indicators
     */
    createProgressGradient() {
        if (document.getElementById('progressGradient')) return;

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.style.position = 'absolute';
        svg.style.width = '0';
        svg.style.height = '0';
        
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.id = 'progressGradient';
        gradient.setAttribute('x1', '0%');
        gradient.setAttribute('y1', '0%');
        gradient.setAttribute('x2', '100%');
        gradient.setAttribute('y2', '0%');

        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('stop-color', '#667eea');

        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '100%');
        stop2.setAttribute('stop-color', '#764ba2');

        gradient.appendChild(stop1);
        gradient.appendChild(stop2);
        defs.appendChild(gradient);
        svg.appendChild(defs);
        document.body.appendChild(svg);
    }

    /**
     * Show skeleton screen for an element
     * @param {string|Element} target - Target element or selector
     * @param {Object} options - Configuration options
     */
    showSkeleton(target, options = {}) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;

        const config = {
            type: 'shimmer', // shimmer, pulse, wave
            rows: 3,
            avatar: false,
            image: false,
            button: false,
            ...options
        };

        // Store original content
        if (!element.dataset.originalContent) {
            element.dataset.originalContent = element.innerHTML;
        }

        // Generate skeleton HTML
        const skeletonHTML = this.generateSkeletonHTML(config);
        
        // Apply skeleton
        element.innerHTML = skeletonHTML;
        element.classList.add('skeleton-container');
        
        // Add to active loaders
        this.activeLoaders.add(element);
    }

    /**
     * Hide skeleton screen and restore content
     * @param {string|Element} target - Target element or selector
     */
    hideSkeleton(target) {
        const element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element || !element.dataset.originalContent) return;

        // Restore original content with fade transition
        element.style.opacity = '0';
        
        setTimeout(() => {
            element.innerHTML = element.dataset.originalContent;
            element.classList.remove('skeleton-container');
            element.classList.add('loading-fade-enter');
            
            // Trigger reflow
            element.offsetHeight;
            
            element.style.opacity = '1';
            element.classList.add('loading-fade-enter-active');
            
            setTimeout(() => {
                element.classList.remove('loading-fade-enter', 'loading-fade-enter-active');
                delete element.dataset.originalContent;
            }, 300);
        }, 150);

        // Remove from active loaders
        this.activeLoaders.delete(element);
    }

    /**
     * Generate skeleton HTML based on configuration
     * @param {Object} config - Skeleton configuration
     * @returns {string} Generated HTML
     */
    generateSkeletonHTML(config) {
        let html = '';
        const skeletonClass = `skeleton-${config.type}`;

        if (config.avatar) {
            html += `<div class="${skeletonClass} skeleton-avatar"></div>`;
        }

        if (config.image) {
            html += `<div class="${skeletonClass} skeleton-image"></div>`;
        }

        // Generate text rows
        for (let i = 0; i < config.rows; i++) {
            const width = i === config.rows - 1 ? '60%' : '100%';
            html += `<div class="${skeletonClass} skeleton-text" style="width: ${width}"></div>`;
        }

        if (config.button) {
            html += `<div class="${skeletonClass} skeleton-button"></div>`;
        }

        return html;
    }

    /**
     * Show loading spinner on button
     * @param {string|Element} button - Button element or selector
     * @param {Object} options - Configuration options
     */
    showButtonLoading(button, options = {}) {
        const btn = typeof button === 'string' ? document.querySelector(button) : button;
        if (!btn) return;

        const config = {
            type: 'spinner', // spinner, dots
            text: 'Loading...',
            ...options
        };

        // Store original state
        if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.innerHTML;
            btn.dataset.originalDisabled = btn.disabled;
        }

        // Apply loading state
        btn.disabled = true;
        btn.classList.add(config.type === 'dots' ? 'btn-loading-dots' : 'btn-loading');
        
        if (config.text) {
            btn.innerHTML = `<span class="btn-text">${config.text}</span>`;
        }

        // Add to active loaders
        this.activeLoaders.add(btn);
    }

    /**
     * Hide loading spinner from button
     * @param {string|Element} button - Button element or selector
     */
    hideButtonLoading(button) {
        const btn = typeof button === 'string' ? document.querySelector(button) : button;
        if (!btn || !btn.dataset.originalText) return;

        // Restore original state
        btn.innerHTML = btn.dataset.originalText;
        btn.disabled = btn.dataset.originalDisabled === 'true';
        btn.classList.remove('btn-loading', 'btn-loading-dots');

        // Clean up data attributes
        delete btn.dataset.originalText;
        delete btn.dataset.originalDisabled;

        // Remove from active loaders
        this.activeLoaders.delete(btn);
    }

    /**
     * Show page loading overlay
     * @param {Object} options - Configuration options
     */
    showPageLoading(options = {}) {
        const config = {
            message: 'Loading...',
            spinner: true,
            backdrop: true,
            ...options
        };

        // Remove existing overlay
        this.hidePageLoading();

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'pageLoadingOverlay';

        const content = document.createElement('div');
        content.className = 'loading-overlay-content';

        let html = '';
        if (config.spinner) {
            html += '<div class="loading-spinner-gradient mb-3"></div>';
        }
        if (config.message) {
            html += `<div class="text-white">${config.message}</div>`;
        }

        content.innerHTML = html;
        overlay.appendChild(content);
        document.body.appendChild(overlay);

        // Show with animation
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });

        return overlay;
    }

    /**
     * Hide page loading overlay
     */
    hidePageLoading() {
        const overlay = document.getElementById('pageLoadingOverlay');
        if (!overlay) return;

        overlay.classList.remove('active');
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 300);
    }

    /**
     * Show section loading state
     * @param {string|Element} section - Section element or selector
     * @param {Object} options - Configuration options
     */
    showSectionLoading(section, options = {}) {
        const element = typeof section === 'string' ? document.querySelector(section) : section;
        if (!element) return;

        const config = {
            spinner: true,
            message: '',
            ...options
        };

        element.classList.add('section-loading', 'loading');
        
        // Create loading content
        if (config.spinner || config.message) {
            const loadingContent = document.createElement('div');
            loadingContent.className = 'section-loading-content';
            loadingContent.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 10;
            `;

            let html = '';
            if (config.spinner) {
                html += '<div class="loading-spinner-gradient mb-2"></div>';
            }
            if (config.message) {
                html += `<div class="text-muted">${config.message}</div>`;
            }

            loadingContent.innerHTML = html;
            element.appendChild(loadingContent);
        }

        // Add to active loaders
        this.activeLoaders.add(element);
    }

    /**
     * Hide section loading state
     * @param {string|Element} section - Section element or selector
     */
    hideSectionLoading(section) {
        const element = typeof section === 'string' ? document.querySelector(section) : section;
        if (!element) return;

        element.classList.remove('section-loading', 'loading');
        
        // Remove loading content
        const loadingContent = element.querySelector('.section-loading-content');
        if (loadingContent) {
            loadingContent.remove();
        }

        // Remove from active loaders
        this.activeLoaders.delete(element);
    }

    /**
     * Create and show progress indicator
     * @param {string|Element} container - Container element or selector
     * @param {Object} options - Configuration options
     */
    showProgress(container, options = {}) {
        const element = typeof container === 'string' ? document.querySelector(container) : container;
        if (!element) return;

        const config = {
            type: 'linear', // linear, circular
            value: 0,
            max: 100,
            indeterminate: false,
            label: '',
            ...options
        };

        const progressId = `progress_${Date.now()}`;
        let progressHTML = '';

        if (config.type === 'circular') {
            const radius = 18;
            const circumference = 2 * Math.PI * radius;
            const strokeDasharray = circumference;
            const strokeDashoffset = config.indeterminate ? 0 : circumference - (config.value / config.max) * circumference;

            progressHTML = `
                <div class="progress-circular" id="${progressId}">
                    <svg>
                        <circle class="progress-circular-bg" cx="20" cy="20" r="${radius}"></circle>
                        <circle class="progress-circular-bar" cx="20" cy="20" r="${radius}"
                                stroke-dasharray="${strokeDasharray}"
                                stroke-dashoffset="${strokeDashoffset}"></circle>
                    </svg>
                    ${config.label ? `<div class="mt-2 text-sm">${config.label}</div>` : ''}
                </div>
            `;
        } else {
            progressHTML = `
                <div class="progress-linear ${config.indeterminate ? 'progress-linear-indeterminate' : ''}" id="${progressId}">
                    <div class="progress-linear-bar" style="width: ${config.indeterminate ? '100%' : config.value + '%'}"></div>
                </div>
                ${config.label ? `<div class="mt-2 text-sm text-center">${config.label}</div>` : ''}
            `;
        }

        element.innerHTML = progressHTML;
        return progressId;
    }

    /**
     * Update progress value
     * @param {string} progressId - Progress indicator ID
     * @param {number} value - New progress value
     * @param {string} label - Optional label update
     */
    updateProgress(progressId, value, label = null) {
        const progress = document.getElementById(progressId);
        if (!progress) return;

        const isCircular = progress.classList.contains('progress-circular');
        
        if (isCircular) {
            const circle = progress.querySelector('.progress-circular-bar');
            const radius = 18;
            const circumference = 2 * Math.PI * radius;
            const strokeDashoffset = circumference - (value / 100) * circumference;
            circle.style.strokeDashoffset = strokeDashoffset;
        } else {
            const bar = progress.querySelector('.progress-linear-bar');
            bar.style.width = value + '%';
        }

        if (label) {
            const labelElement = progress.parentNode.querySelector('.text-sm');
            if (labelElement) {
                labelElement.textContent = label;
            }
        }
    }

    /**
     * Show file upload progress
     * @param {string|Element} container - Container element or selector
     * @param {Object} options - Configuration options
     */
    showUploadProgress(container, options = {}) {
        const element = typeof container === 'string' ? document.querySelector(container) : container;
        if (!element) return;

        const config = {
            fileName: 'Uploading file...',
            progress: 0,
            ...options
        };

        const uploadHTML = `
            <div class="upload-progress">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-sm font-medium">${config.fileName}</span>
                    <span class="text-sm text-muted upload-percentage">${config.progress}%</span>
                </div>
                <div class="upload-progress-bar">
                    <div class="upload-progress-fill" style="width: ${config.progress}%"></div>
                </div>
                <div class="d-flex justify-content-between align-items-center mt-2">
                    <span class="text-xs text-muted upload-status">Uploading...</span>
                    <button type="button" class="btn btn-sm btn-outline-danger upload-cancel">Cancel</button>
                </div>
            </div>
        `;

        element.innerHTML = uploadHTML;

        // Add cancel functionality
        const cancelBtn = element.querySelector('.upload-cancel');
        if (cancelBtn && options.onCancel) {
            cancelBtn.addEventListener('click', options.onCancel);
        }

        return element.querySelector('.upload-progress');
    }

    /**
     * Update upload progress
     * @param {Element} uploadElement - Upload progress element
     * @param {number} progress - Progress percentage
     * @param {Object} options - Additional options
     */
    updateUploadProgress(uploadElement, progress, options = {}) {
        if (!uploadElement) return;

        const progressFill = uploadElement.querySelector('.upload-progress-fill');
        const percentage = uploadElement.querySelector('.upload-percentage');
        const status = uploadElement.querySelector('.upload-status');

        if (progressFill) {
            progressFill.style.width = progress + '%';
        }

        if (percentage) {
            percentage.textContent = progress + '%';
        }

        if (status && options.status) {
            status.textContent = options.status;
        }

        // Handle completion
        if (progress >= 100) {
            setTimeout(() => {
                if (status) {
                    status.textContent = 'Upload complete';
                    status.classList.remove('text-muted');
                    status.classList.add('text-success');
                }
                
                const cancelBtn = uploadElement.querySelector('.upload-cancel');
                if (cancelBtn) {
                    cancelBtn.style.display = 'none';
                }
            }, 500);
        }
    }

    /**
     * Setup global loading handlers for forms and AJAX
     */
    setupGlobalLoadingHandlers() {
        // Handle page navigation loading
        if (window.addEventListener) {
            window.addEventListener('beforeunload', () => {
                this.showPageLoading({ message: 'Loading...' });
            });
        }

        // Handle back/forward navigation
        window.addEventListener('pageshow', (event) => {
            if (event.persisted) {
                this.hidePageLoading();
                this.clearAllLoaders();
            }
        });
    }

    /**
     * Observe form submissions for automatic loading states
     */
    observeFormSubmissions() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            if (!form.matches('form')) return;

            // Skip if form has data-no-loading attribute
            if (form.hasAttribute('data-no-loading')) return;

            // Find submit button
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                this.showButtonLoading(submitBtn, { text: 'Processing...' });
            }

            // Show form loading state
            this.showSectionLoading(form, { message: 'Processing form...' });
        });
    }

    /**
     * Observe AJAX requests for automatic loading states
     */
    observeAjaxRequests() {
        // Override fetch for automatic loading
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            const loadingId = 'fetch_' + Date.now();
            this.showPageLoading({ message: 'Loading data...' });
            
            return originalFetch(...args)
                .finally(() => {
                    this.hidePageLoading();
                });
        };

        // Override XMLHttpRequest for automatic loading
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;

        XMLHttpRequest.prototype.open = function(...args) {
            this._loadingId = 'xhr_' + Date.now();
            return originalXHROpen.apply(this, args);
        };

        XMLHttpRequest.prototype.send = function(...args) {
            if (!this.hasAttribute || !this.hasAttribute('data-no-loading')) {
                loadingStates.showPageLoading({ message: 'Loading...' });
            }

            this.addEventListener('loadend', () => {
                loadingStates.hidePageLoading();
            });

            return originalXHRSend.apply(this, args);
        };
    }

    /**
     * Clear all active loaders
     */
    clearAllLoaders() {
        this.activeLoaders.forEach(element => {
            if (element.classList.contains('skeleton-container')) {
                this.hideSkeleton(element);
            } else if (element.classList.contains('btn-loading') || element.classList.contains('btn-loading-dots')) {
                this.hideButtonLoading(element);
            } else if (element.classList.contains('section-loading')) {
                this.hideSectionLoading(element);
            }
        });

        this.hidePageLoading();
        this.activeLoaders.clear();
    }

    /**
     * Create skeleton for dashboard cards
     */
    createDashboardSkeleton() {
        return `
            <div class="skeleton-dashboard">
                ${Array(4).fill().map(() => `
                    <div class="skeleton-stat-card">
                        <div class="skeleton skeleton-stat-icon"></div>
                        <div class="skeleton skeleton-stat-value"></div>
                        <div class="skeleton skeleton-stat-label"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Create skeleton for table
     */
    createTableSkeleton(rows = 5, columns = 4) {
        return `
            <table class="skeleton-table">
                <thead>
                    <tr>
                        ${Array(columns).fill().map(() => `
                            <th><div class="skeleton skeleton-text"></div></th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${Array(rows).fill().map(() => `
                        <tr>
                            ${Array(columns).fill().map((_, i) => `
                                <td><div class="skeleton skeleton-table-cell ${i % 2 === 0 ? 'skeleton-table-cell-sm' : ''}"></div></td>
                            `).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    /**
     * Create skeleton for list items
     */
    createListSkeleton(items = 5) {
        return `
            <div class="skeleton-list">
                ${Array(items).fill().map(() => `
                    <div class="skeleton-list-item">
                        <div class="skeleton skeleton-list-avatar"></div>
                        <div class="skeleton-list-content">
                            <div class="skeleton skeleton-list-title"></div>
                            <div class="skeleton skeleton-list-subtitle"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

// Initialize loading states system
const loadingStates = new LoadingStates();

// Export for use in other scripts
window.LoadingStates = LoadingStates;
window.loadingStates = loadingStates;

// jQuery integration if available
if (typeof jQuery !== 'undefined') {
    jQuery.fn.showSkeleton = function(options) {
        return this.each(function() {
            loadingStates.showSkeleton(this, options);
        });
    };

    jQuery.fn.hideSkeleton = function() {
        return this.each(function() {
            loadingStates.hideSkeleton(this);
        });
    };

    jQuery.fn.showLoading = function(options) {
        return this.each(function() {
            if (this.tagName === 'BUTTON') {
                loadingStates.showButtonLoading(this, options);
            } else {
                loadingStates.showSectionLoading(this, options);
            }
        });
    };

    jQuery.fn.hideLoading = function() {
        return this.each(function() {
            if (this.tagName === 'BUTTON') {
                loadingStates.hideButtonLoading(this);
            } else {
                loadingStates.hideSectionLoading(this);
            }
        });
    };
}

// Utility functions for common loading patterns
window.showPageLoader = (message = 'Loading...') => loadingStates.showPageLoading({ message });
window.hidePageLoader = () => loadingStates.hidePageLoading();
window.showButtonLoader = (button, text = 'Loading...') => loadingStates.showButtonLoading(button, { text });
window.hideButtonLoader = (button) => loadingStates.hideButtonLoading(button);