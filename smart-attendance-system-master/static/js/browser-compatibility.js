/**
 * Browser Compatibility and Feature Detection
 * Handles cross-browser compatibility issues and provides fallbacks
 */

class BrowserCompatibility {
    constructor() {
        this.features = {};
        this.browser = this.detectBrowser();
        this.init();
    }

    init() {
        this.detectFeatures();
        this.applyPolyfills();
        this.addBrowserClasses();
        this.setupEventListeners();
    }

    detectBrowser() {
        const userAgent = navigator.userAgent;
        const browsers = {
            chrome: /Chrome/.test(userAgent) && /Google Inc/.test(navigator.vendor),
            firefox: /Firefox/.test(userAgent),
            safari: /Safari/.test(userAgent) && /Apple Computer/.test(navigator.vendor),
            edge: /Edg/.test(userAgent),
            ie: /MSIE|Trident/.test(userAgent)
        };

        for (const [name, test] of Object.entries(browsers)) {
            if (test) return name;
        }
        return 'unknown';
    }

    detectFeatures() {
        // CSS Feature Detection
        this.features.backdropFilter = CSS.supports('backdrop-filter', 'blur(20px)') || 
                                      CSS.supports('-webkit-backdrop-filter', 'blur(20px)');
        
        this.features.cssGrid = CSS.supports('display', 'grid');
        this.features.flexbox = CSS.supports('display', 'flex');
        this.features.customProperties = CSS.supports('--custom', 'property');
        this.features.transforms3d = CSS.supports('transform', 'translateZ(0px)');
        
        // JavaScript Feature Detection
        this.features.intersectionObserver = 'IntersectionObserver' in window;
        this.features.requestIdleCallback = 'requestIdleCallback' in window;
        this.features.webAnimations = 'animate' in document.createElement('div');
        this.features.performanceObserver = 'PerformanceObserver' in window;
        
        // Touch and Mobile Detection
        this.features.touchEvents = 'ontouchstart' in window;
        this.features.pointerEvents = 'onpointerdown' in window;
        this.features.deviceMotion = 'DeviceMotionEvent' in window;
        
        // Media Query Support
        this.features.matchMedia = 'matchMedia' in window;
        this.features.prefersReducedMotion = this.features.matchMedia && 
                                           window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    applyPolyfills() {
        // Polyfill for requestIdleCallback
        if (!this.features.requestIdleCallback) {
            window.requestIdleCallback = function(callback, options = {}) {
                const timeout = options.timeout || 0;
                const startTime = performance.now();
                
                return setTimeout(() => {
                    callback({
                        didTimeout: false,
                        timeRemaining() {
                            return Math.max(0, 50 - (performance.now() - startTime));
                        }
                    });
                }, timeout);
            };
            
            window.cancelIdleCallback = function(id) {
                clearTimeout(id);
            };
        }

        // Polyfill for IntersectionObserver
        if (!this.features.intersectionObserver) {
            this.loadPolyfill('https://polyfill.io/v3/polyfill.min.js?features=IntersectionObserver');
        }

        // Polyfill for CSS Custom Properties (IE11)
        if (!this.features.customProperties && this.browser === 'ie') {
            this.loadPolyfill('https://cdn.jsdelivr.net/npm/css-vars-ponyfill@2');
        }

        // Polyfill for Web Animations API
        if (!this.features.webAnimations) {
            this.loadPolyfill('https://cdn.jsdelivr.net/npm/web-animations-js@2.3.2/web-animations.min.js');
        }
    }

    loadPolyfill(url) {
        const script = document.createElement('script');
        script.src = url;
        script.async = true;
        document.head.appendChild(script);
    }

    addBrowserClasses() {
        const html = document.documentElement;
        
        // Add browser class
        html.classList.add(`browser-${this.browser}`);
        
        // Add feature classes
        Object.entries(this.features).forEach(([feature, supported]) => {
            html.classList.add(supported ? `has-${feature}` : `no-${feature}`);
        });

        // Add specific browser fixes
        this.applyBrowserSpecificFixes();
    }

    applyBrowserSpecificFixes() {
        const html = document.documentElement;

        switch (this.browser) {
            case 'ie':
                this.applyIEFixes();
                break;
            case 'safari':
                this.applySafariFixes();
                break;
            case 'firefox':
                this.applyFirefoxFixes();
                break;
            case 'edge':
                this.applyEdgeFixes();
                break;
        }
    }

    applyIEFixes() {
        // IE11 specific fixes
        const style = document.createElement('style');
        style.textContent = `
            .glass {
                background: rgba(255, 255, 255, 0.2) !important;
                filter: none !important;
            }
            .flex-container {
                display: -ms-flexbox !important;
            }
            .flex-item {
                -ms-flex: 1 1 auto !important;
            }
        `;
        document.head.appendChild(style);

        // Disable animations in IE
        document.documentElement.classList.add('no-animations');
    }

    applySafariFixes() {
        // Safari specific fixes for backdrop-filter
        if (!this.features.backdropFilter) {
            const style = document.createElement('style');
            style.textContent = `
                .glass {
                    background: rgba(255, 255, 255, 0.25) !important;
                }
            `;
            document.head.appendChild(style);
        }

        // Fix for Safari's aggressive caching
        window.addEventListener('pageshow', (event) => {
            if (event.persisted) {
                window.location.reload();
            }
        });
    }

    applyFirefoxFixes() {
        // Firefox specific backdrop-filter fallback
        const style = document.createElement('style');
        style.textContent = `
            @-moz-document url-prefix() {
                .glass {
                    background: rgba(255, 255, 255, 0.15) !important;
                }
            }
        `;
        document.head.appendChild(style);
    }

    applyEdgeFixes() {
        // Edge specific fixes
        if (!this.features.backdropFilter) {
            const style = document.createElement('style');
            style.textContent = `
                .glass {
                    background: rgba(255, 255, 255, 0.2) !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    setupEventListeners() {
        // Handle orientation changes on mobile
        if (this.features.touchEvents) {
            window.addEventListener('orientationchange', () => {
                setTimeout(() => {
                    this.recalculateViewport();
                }, 100);
            });
        }

        // Handle reduced motion preference changes
        if (this.features.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            mediaQuery.addListener((e) => {
                if (e.matches) {
                    document.documentElement.classList.add('reduce-motion');
                } else {
                    document.documentElement.classList.remove('reduce-motion');
                }
            });
        }

        // Handle connection changes
        if ('connection' in navigator) {
            navigator.connection.addEventListener('change', () => {
                this.handleConnectionChange();
            });
        }
    }

    recalculateViewport() {
        // Fix viewport issues on mobile browsers
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, user-scalable=no');
        }
    }

    handleConnectionChange() {
        const connection = navigator.connection;
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            // Disable animations on slow connections
            document.documentElement.classList.add('slow-connection');
        } else {
            document.documentElement.classList.remove('slow-connection');
        }
    }

    // Public methods for feature detection
    supportsFeature(feature) {
        return this.features[feature] || false;
    }

    getBrowser() {
        return this.browser;
    }

    getFeatures() {
        return { ...this.features };
    }

    // Method to test CSS support
    testCSS(property, value) {
        return CSS.supports(property, value);
    }

    // Method to add custom feature detection
    addFeatureTest(name, test) {
        this.features[name] = typeof test === 'function' ? test() : test;
        
        const html = document.documentElement;
        html.classList.add(this.features[name] ? `has-${name}` : `no-${name}`);
    }

    // Method to load conditional resources
    loadConditionalResource(condition, resource) {
        if (this.supportsFeature(condition) || this.browser === condition) {
            if (resource.endsWith('.css')) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = resource;
                document.head.appendChild(link);
            } else if (resource.endsWith('.js')) {
                const script = document.createElement('script');
                script.src = resource;
                script.async = true;
                document.head.appendChild(script);
            }
        }
    }
}

// Initialize browser compatibility
const browserCompatibility = new BrowserCompatibility();

// Export for use in other modules
window.BrowserCompatibility = BrowserCompatibility;
window.browserCompatibility = browserCompatibility;

// Add to global scope for easy access
window.supportsFeature = (feature) => browserCompatibility.supportsFeature(feature);
window.getBrowser = () => browserCompatibility.getBrowser();