/**
 * Performance Monitoring System
 * Monitors UI performance and provides optimization recommendations
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoad: {},
            animations: {},
            interactions: {},
            resources: {},
            webVitals: {}
        };
        this.thresholds = {
            lcp: 2500, // Largest Contentful Paint (ms)
            fid: 100,  // First Input Delay (ms)
            cls: 0.1,  // Cumulative Layout Shift
            fps: 55,   // Minimum acceptable FPS
            loadTime: 3000 // Maximum page load time (ms)
        };
        this.observers = [];
        this.init();
    }

    init() {
        this.setupPerformanceObservers();
        this.monitorPageLoad();
        this.monitorAnimations();
        this.monitorInteractions();
        this.monitorResources();
        this.setupReporting();
    }

    setupPerformanceObservers() {
        // Largest Contentful Paint (LCP)
        if ('PerformanceObserver' in window) {
            try {
                const lcpObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.metrics.webVitals.lcp = lastEntry.startTime;
                    
                    if (lastEntry.startTime > this.thresholds.lcp) {
                        this.reportIssue('LCP', `Slow LCP: ${lastEntry.startTime.toFixed(2)}ms`);
                    }
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
                this.observers.push(lcpObserver);
            } catch (e) {
                console.warn('LCP observer not supported');
            }

            // First Input Delay (FID)
            try {
                const fidObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    entries.forEach(entry => {
                        const fid = entry.processingStart - entry.startTime;
                        this.metrics.webVitals.fid = fid;
                        
                        if (fid > this.thresholds.fid) {
                            this.reportIssue('FID', `Slow FID: ${fid.toFixed(2)}ms`);
                        }
                    });
                });
                fidObserver.observe({ entryTypes: ['first-input'] });
                this.observers.push(fidObserver);
            } catch (e) {
                console.warn('FID observer not supported');
            }

            // Cumulative Layout Shift (CLS)
            try {
                let clsValue = 0;
                const clsObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    entries.forEach(entry => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    });
                    this.metrics.webVitals.cls = clsValue;
                    
                    if (clsValue > this.thresholds.cls) {
                        this.reportIssue('CLS', `High CLS: ${clsValue.toFixed(3)}`);
                    }
                });
                clsObserver.observe({ entryTypes: ['layout-shift'] });
                this.observers.push(clsObserver);
            } catch (e) {
                console.warn('CLS observer not supported');
            }

            // Long Tasks
            try {
                const longTaskObserver = new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    entries.forEach(entry => {
                        this.reportIssue('Long Task', 
                            `Task took ${entry.duration.toFixed(2)}ms`);
                    });
                });
                longTaskObserver.observe({ entryTypes: ['longtask'] });
                this.observers.push(longTaskObserver);
            } catch (e) {
                console.warn('Long task observer not supported');
            }
        }
    }

    monitorPageLoad() {
        const startTime = performance.now();
        
        window.addEventListener('load', () => {
            const loadTime = performance.now() - startTime;
            this.metrics.pageLoad.total = loadTime;
            
            if (loadTime > this.thresholds.loadTime) {
                this.reportIssue('Page Load', `Slow page load: ${loadTime.toFixed(2)}ms`);
            }

            // Analyze navigation timing
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.metrics.pageLoad.dns = navigation.domainLookupEnd - navigation.domainLookupStart;
                this.metrics.pageLoad.connect = navigation.connectEnd - navigation.connectStart;
                this.metrics.pageLoad.request = navigation.responseStart - navigation.requestStart;
                this.metrics.pageLoad.response = navigation.responseEnd - navigation.responseStart;
                this.metrics.pageLoad.domLoad = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
            }
        });
    }

    monitorAnimations() {
        let frameCount = 0;
        let lastTime = performance.now();
        let fpsHistory = [];

        const measureFPS = () => {
            frameCount++;
            const currentTime = performance.now();
            
            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                fpsHistory.push(fps);
                
                // Keep only last 10 measurements
                if (fpsHistory.length > 10) {
                    fpsHistory.shift();
                }
                
                const avgFPS = fpsHistory.reduce((a, b) => a + b, 0) / fpsHistory.length;
                this.metrics.animations.fps = avgFPS;
                
                if (fps < this.thresholds.fps) {
                    this.reportIssue('Animation Performance', 
                        `Low FPS detected: ${fps}fps (avg: ${avgFPS.toFixed(1)}fps)`);
                    this.optimizeAnimations();
                }
                
                frameCount = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(measureFPS);
        };

        requestAnimationFrame(measureFPS);

        // Monitor specific animation elements
        this.monitorAnimationElements();
    }

    monitorAnimationElements() {
        const animatedElements = document.querySelectorAll('.fade-in, .card-enhanced, .btn-enhanced');
        
        animatedElements.forEach(element => {
            const startTime = performance.now();
            
            element.addEventListener('animationstart', () => {
                element.dataset.animationStart = performance.now();
            });
            
            element.addEventListener('animationend', () => {
                const duration = performance.now() - parseFloat(element.dataset.animationStart || startTime);
                
                if (duration > 500) { // Animations longer than 500ms
                    this.reportIssue('Animation Duration', 
                        `Long animation: ${duration.toFixed(2)}ms on ${element.className}`);
                }
            });
        });
    }

    monitorInteractions() {
        const interactionTypes = ['click', 'touchstart', 'keydown'];
        
        interactionTypes.forEach(type => {
            document.addEventListener(type, (event) => {
                const startTime = performance.now();
                
                // Use requestAnimationFrame to measure response time
                requestAnimationFrame(() => {
                    const responseTime = performance.now() - startTime;
                    
                    if (!this.metrics.interactions[type]) {
                        this.metrics.interactions[type] = [];
                    }
                    
                    this.metrics.interactions[type].push(responseTime);
                    
                    if (responseTime > 100) { // Slow interaction
                        this.reportIssue('Interaction Performance', 
                            `Slow ${type} response: ${responseTime.toFixed(2)}ms`);
                    }
                });
            }, { passive: true });
        });
    }

    monitorResources() {
        window.addEventListener('load', () => {
            const resources = performance.getEntriesByType('resource');
            
            resources.forEach(resource => {
                const resourceData = {
                    name: resource.name,
                    duration: resource.duration,
                    size: resource.transferSize,
                    type: this.getResourceType(resource.name)
                };
                
                if (!this.metrics.resources[resourceData.type]) {
                    this.metrics.resources[resourceData.type] = [];
                }
                
                this.metrics.resources[resourceData.type].push(resourceData);
                
                // Report slow resources
                if (resource.duration > 1000) {
                    this.reportIssue('Resource Loading', 
                        `Slow resource: ${resource.name} (${resource.duration.toFixed(2)}ms)`);
                }
                
                // Report large resources
                if (resource.transferSize > 1024 * 1024) { // 1MB
                    this.reportIssue('Resource Size', 
                        `Large resource: ${resource.name} (${(resource.transferSize / 1024 / 1024).toFixed(2)}MB)`);
                }
            });
        });
    }

    getResourceType(url) {
        if (url.includes('.css')) return 'css';
        if (url.includes('.js')) return 'js';
        if (url.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i)) return 'image';
        if (url.match(/\.(woff|woff2|ttf|eot)$/i)) return 'font';
        return 'other';
    }

    optimizeAnimations() {
        // Reduce animation complexity if performance is poor
        const html = document.documentElement;
        
        if (!html.classList.contains('performance-mode')) {
            html.classList.add('performance-mode');
            
            // Disable non-essential animations
            const style = document.createElement('style');
            style.id = 'performance-optimizations';
            style.textContent = `
                .performance-mode .fade-in {
                    animation-duration: 0.1s !important;
                }
                .performance-mode .pulse-animation {
                    animation: none !important;
                }
                .performance-mode .hover-scale:hover {
                    transform: none !important;
                }
            `;
            document.head.appendChild(style);
            
            this.reportIssue('Performance Optimization', 'Reduced animation complexity due to low FPS');
        }
    }

    setupReporting() {
        // Report metrics every 30 seconds
        setInterval(() => {
            this.generateReport();
        }, 30000);

        // Report on page unload
        window.addEventListener('beforeunload', () => {
            this.generateFinalReport();
        });
    }

    reportIssue(category, message) {
        const issue = {
            category,
            message,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        console.warn(`Performance Issue [${category}]: ${message}`);
        
        // Store in session storage for debugging
        const issues = JSON.parse(sessionStorage.getItem('performanceIssues') || '[]');
        issues.push(issue);
        sessionStorage.setItem('performanceIssues', JSON.stringify(issues.slice(-50))); // Keep last 50 issues
    }

    generateReport() {
        const report = {
            timestamp: Date.now(),
            url: window.location.href,
            metrics: this.metrics,
            recommendations: this.generateRecommendations()
        };
        
        // Store report
        const reports = JSON.parse(localStorage.getItem('performanceReports') || '[]');
        reports.push(report);
        localStorage.setItem('performanceReports', JSON.stringify(reports.slice(-10))); // Keep last 10 reports
        
        return report;
    }

    generateRecommendations() {
        const recommendations = [];
        
        // LCP recommendations
        if (this.metrics.webVitals.lcp > this.thresholds.lcp) {
            recommendations.push('Optimize Largest Contentful Paint by reducing image sizes and server response times');
        }
        
        // FID recommendations
        if (this.metrics.webVitals.fid > this.thresholds.fid) {
            recommendations.push('Reduce First Input Delay by minimizing JavaScript execution time');
        }
        
        // CLS recommendations
        if (this.metrics.webVitals.cls > this.thresholds.cls) {
            recommendations.push('Improve Cumulative Layout Shift by setting dimensions for images and ads');
        }
        
        // FPS recommendations
        if (this.metrics.animations.fps < this.thresholds.fps) {
            recommendations.push('Optimize animations for better frame rate using CSS transforms and opacity');
        }
        
        // Resource recommendations
        const totalCSS = this.metrics.resources.css?.reduce((sum, r) => sum + r.size, 0) || 0;
        const totalJS = this.metrics.resources.js?.reduce((sum, r) => sum + r.size, 0) || 0;
        
        if (totalCSS > 500 * 1024) { // 500KB
            recommendations.push('Consider minifying and compressing CSS files');
        }
        
        if (totalJS > 1024 * 1024) { // 1MB
            recommendations.push('Consider code splitting and lazy loading for JavaScript');
        }
        
        return recommendations;
    }

    generateFinalReport() {
        const finalReport = this.generateReport();
        
        // Send to analytics if available
        if (typeof gtag !== 'undefined') {
            gtag('event', 'performance_report', {
                custom_parameter: JSON.stringify(finalReport)
            });
        }
        
        return finalReport;
    }

    // Public methods
    getMetrics() {
        return { ...this.metrics };
    }

    getIssues() {
        return JSON.parse(sessionStorage.getItem('performanceIssues') || '[]');
    }

    getReports() {
        return JSON.parse(localStorage.getItem('performanceReports') || '[]');
    }

    clearData() {
        sessionStorage.removeItem('performanceIssues');
        localStorage.removeItem('performanceReports');
    }

    // Method to manually trigger optimization
    triggerOptimization() {
        this.optimizeAnimations();
    }

    // Method to set custom thresholds
    setThresholds(newThresholds) {
        this.thresholds = { ...this.thresholds, ...newThresholds };
    }

    // Cleanup method
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers = [];
    }
}

// Initialize performance monitor
const performanceMonitor = new PerformanceMonitor();

// Export for use in other modules
window.PerformanceMonitor = PerformanceMonitor;
window.performanceMonitor = performanceMonitor;

// Add global methods for easy access
window.getPerformanceMetrics = () => performanceMonitor.getMetrics();
window.getPerformanceIssues = () => performanceMonitor.getIssues();
window.optimizePerformance = () => performanceMonitor.triggerOptimization();