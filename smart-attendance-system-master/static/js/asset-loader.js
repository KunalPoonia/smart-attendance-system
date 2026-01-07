/**
 * Optimized Asset Loader for Enhanced UI Components
 * Implements lazy loading and performance monitoring
 */

class AssetLoader {
    constructor() {
        this.loadedAssets = new Set();
        this.performanceMetrics = {
            cssLoadTime: 0,
            jsLoadTime: 0,
            totalAssets: 0,
            loadedAssets: 0
        };
        this.init();
    }

    init() {
        // Load critical CSS immediately
        this.loadCriticalCSS();
        
        // Load non-critical assets after page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.loadNonCriticalAssets();
            });
        } else {
            this.loadNonCriticalAssets();
        }

        // Monitor performance
        this.setupPerformanceMonitoring();
    }

    loadCriticalCSS() {
        const criticalCSS = [
            '/static/css/minified-bundle.css',
            '/static/css/performance-optimizations.css'
        ];

        criticalCSS.forEach(href => {
            if (!this.loadedAssets.has(href)) {
                this.loadCSS(href, true);
            }
        });
    }

    loadNonCriticalAssets() {
        // Use requestIdleCallback for non-critical assets
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                this.loadEnhancedComponents();
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            setTimeout(() => {
                this.loadEnhancedComponents();
            }, 100);
        }
    }

    loadEnhancedComponents() {
        const nonCriticalCSS = [
            '/static/css/enhanced-forms.css',
            '/static/css/enhanced-toast.css',
            '/static/css/loading-states.css',
            '/static/css/mobile-responsive.css',
            '/static/css/accessibility-enhancements.css'
        ];

        const nonCriticalJS = [
            '/static/js/enhanced-forms.js',
            '/static/js/enhanced-toast.js',
            '/static/js/loading-states.js',
            '/static/js/mobile-interactions.js',
            '/static/js/accessibility-enhancements.js'
        ];

        // Load CSS first, then JS
        Promise.all(nonCriticalCSS.map(href => this.loadCSS(href)))
            .then(() => {
                return Promise.all(nonCriticalJS.map(src => this.loadJS(src)));
            })
            .then(() => {
                this.onAllAssetsLoaded();
            })
            .catch(error => {
                console.warn('Some non-critical assets failed to load:', error);
            });
    }

    loadCSS(href, critical = false) {
        return new Promise((resolve, reject) => {
            if (this.loadedAssets.has(href)) {
                resolve();
                return;
            }

            const startTime = performance.now();
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            
            if (!critical) {
                link.media = 'print';
                link.onload = () => {
                    link.media = 'all';
                    this.performanceMetrics.cssLoadTime += performance.now() - startTime;
                    this.loadedAssets.add(href);
                    this.performanceMetrics.loadedAssets++;
                    resolve();
                };
            } else {
                link.onload = () => {
                    this.loadedAssets.add(href);
                    resolve();
                };
            }

            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    loadJS(src) {
        return new Promise((resolve, reject) => {
            if (this.loadedAssets.has(src)) {
                resolve();
                return;
            }

            const startTime = performance.now();
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            
            script.onload = () => {
                this.performanceMetrics.jsLoadTime += performance.now() - startTime;
                this.loadedAssets.add(src);
                this.performanceMetrics.loadedAssets++;
                resolve();
            };

            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('web-vital' in window) {
            this.monitorWebVitals();
        }

        // Monitor animation performance
        this.monitorAnimationPerformance();

        // Monitor resource loading
        this.monitorResourceLoading();
    }

    monitorWebVitals() {
        // Largest Contentful Paint (LCP)
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const lastEntry = entries[entries.length - 1];
            console.log('LCP:', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay (FID)
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            entries.forEach(entry => {
                console.log('FID:', entry.processingStart - entry.startTime);
            });
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift (CLS)
        new PerformanceObserver((entryList) => {
            let clsValue = 0;
            const entries = entryList.getEntries();
            entries.forEach(entry => {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            });
            console.log('CLS:', clsValue);
        }).observe({ entryTypes: ['layout-shift'] });
    }

    monitorAnimationPerformance() {
        let frameCount = 0;
        let lastTime = performance.now();

        const measureFPS = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                
                if (fps < 55) {
                    console.warn(`Low FPS detected: ${fps}fps`);
                    this.optimizeAnimations();
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(measureFPS);
        };

        requestAnimationFrame(measureFPS);
    }

    monitorResourceLoading() {
        // Monitor resource timing
        window.addEventListener('load', () => {
            const resources = performance.getEntriesByType('resource');
            const slowResources = resources.filter(resource => 
                resource.duration > 1000 // Resources taking more than 1 second
            );

            if (slowResources.length > 0) {
                console.warn('Slow loading resources detected:', slowResources);
            }
        });
    }

    optimizeAnimations() {
        // Reduce animation complexity if performance is poor
        document.documentElement.classList.add('reduce-animations');
        
        // Disable non-essential animations
        const nonEssentialAnimations = document.querySelectorAll('.fade-in, .pulse-animation');
        nonEssentialAnimations.forEach(element => {
            element.style.animation = 'none';
            element.style.transition = 'none';
        });
    }

    onAllAssetsLoaded() {
        // Trigger custom event when all assets are loaded
        const event = new CustomEvent('assetsLoaded', {
            detail: this.performanceMetrics
        });
        document.dispatchEvent(event);

        // Initialize enhanced components
        this.initializeEnhancedComponents();
    }

    initializeEnhancedComponents() {
        // Initialize components that require all assets to be loaded
        if (window.EnhancedToast) {
            window.EnhancedToast.init();
        }

        if (window.LoadingStates) {
            window.LoadingStates.init();
        }

        if (window.MobileInteractions) {
            window.MobileInteractions.init();
        }

        if (window.AccessibilityEnhancements) {
            window.AccessibilityEnhancements.init();
        }
    }

    // Public method to get performance metrics
    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            loadedAssets: Array.from(this.loadedAssets)
        };
    }

    // Public method to preload specific assets
    preloadAsset(url, type = 'auto') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = url;
        
        if (type === 'css') {
            link.as = 'style';
        } else if (type === 'js') {
            link.as = 'script';
        }
        
        document.head.appendChild(link);
    }
}

// Initialize asset loader
const assetLoader = new AssetLoader();

// Export for use in other modules
window.AssetLoader = AssetLoader;
window.assetLoader = assetLoader;