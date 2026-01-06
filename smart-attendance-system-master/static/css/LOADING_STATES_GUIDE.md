# Loading States & Skeleton Screens Guide

This guide explains how to use the comprehensive loading states and skeleton screens system implemented for the Smart Attendance System.

## Overview

The loading states system provides:
- **Skeleton screens** for content loading states
- **Loading spinners** for button actions and form submissions
- **Progress indicators** for file uploads and long-running operations
- **Smooth transitions** between loading and loaded states
- **Accessibility compliance** with reduced motion support

## Files Included

### CSS Files
- `loading-states.css` - Complete loading states and skeleton screens styles
- `enhanced-design-system.css` - Base design system (already included)

### JavaScript Files
- `loading-states.js` - Loading states management and functionality

### Test Files
- `test-loading-states.html` - Comprehensive demo and testing interface

## Quick Start

### 1. Include Required Files

The loading states system is already integrated into the base template:

```html
<!-- CSS -->
<link href="{{ url_for('static', filename='css/loading-states.css') }}" rel="stylesheet">

<!-- JavaScript -->
<script src="{{ url_for('static', filename='js/loading-states.js') }}"></script>
```

### 2. Basic Usage

The system provides a global `loadingStates` object with easy-to-use methods:

```javascript
// Show skeleton screen
loadingStates.showSkeleton('#myContainer', {
    type: 'shimmer',
    rows: 3,
    avatar: true
});

// Hide skeleton screen
loadingStates.hideSkeleton('#myContainer');

// Show button loading
loadingStates.showButtonLoading('#myButton', {
    text: 'Processing...'
});

// Hide button loading
loadingStates.hideButtonLoading('#myButton');
```

## Skeleton Screens

### Basic Skeleton Types

```javascript
// Shimmer effect (default)
loadingStates.showSkeleton('#container', {
    type: 'shimmer',
    rows: 3
});

// Pulse effect
loadingStates.showSkeleton('#container', {
    type: 'pulse',
    rows: 4,
    avatar: true
});

// Wave effect
loadingStates.showSkeleton('#container', {
    type: 'wave',
    rows: 2,
    button: true
});
```

### Pre-built Skeleton Layouts

```javascript
// Dashboard skeleton
const dashboardHTML = loadingStates.createDashboardSkeleton();
document.getElementById('dashboard').innerHTML = dashboardHTML;

// Table skeleton
const tableHTML = loadingStates.createTableSkeleton(5, 4); // 5 rows, 4 columns
document.getElementById('table').innerHTML = tableHTML;

// List skeleton
const listHTML = loadingStates.createListSkeleton(5); // 5 items
document.getElementById('list').innerHTML = listHTML;
```

### CSS-Only Skeletons

You can also use CSS classes directly:

```html
<!-- Basic skeleton elements -->
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-heading"></div>
<div class="skeleton skeleton-avatar"></div>
<div class="skeleton skeleton-button"></div>

<!-- Skeleton card -->
<div class="skeleton-card">
    <div class="skeleton-card-header">
        <div class="skeleton skeleton-avatar"></div>
        <div class="skeleton skeleton-heading"></div>
    </div>
    <div class="skeleton-card-body">
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-button"></div>
    </div>
</div>
```

## Loading Spinners

### Button Loading States

```javascript
// Show spinner loading
loadingStates.showButtonLoading('#saveButton', {
    type: 'spinner',
    text: 'Saving...'
});

// Show dots loading
loadingStates.showButtonLoading('#uploadButton', {
    type: 'dots',
    text: 'Uploading...'
});

// Hide loading
loadingStates.hideButtonLoading('#saveButton');
```

### Spinner Variants

```html
<!-- Default spinner -->
<div class="loading-spinner"></div>

<!-- Gradient spinner -->
<div class="loading-spinner-gradient"></div>

<!-- Dots spinner -->
<div class="loading-dots">
    <span></span>
    <span></span>
    <span></span>
</div>

<!-- Pulse ring -->
<div class="loading-pulse-ring"></div>
```

## Progress Indicators

### Linear Progress

```javascript
// Show progress bar
const progressId = loadingStates.showProgress('#container', {
    type: 'linear',
    value: 0,
    label: 'Processing... 0%'
});

// Update progress
loadingStates.updateProgress(progressId, 50, 'Processing... 50%');

// Indeterminate progress
loadingStates.showProgress('#container', {
    type: 'linear',
    indeterminate: true,
    label: 'Loading...'
});
```

### Circular Progress

```javascript
// Show circular progress
const progressId = loadingStates.showProgress('#container', {
    type: 'circular',
    value: 25,
    label: 'Loading... 25%'
});

// Update progress
loadingStates.updateProgress(progressId, 75, 'Loading... 75%');
```

### File Upload Progress

```javascript
// Show upload progress
const uploadElement = loadingStates.showUploadProgress('#uploadContainer', {
    fileName: 'document.pdf',
    progress: 0,
    onCancel: () => {
        console.log('Upload cancelled');
    }
});

// Update upload progress
loadingStates.updateUploadProgress(uploadElement, 45, {
    status: 'Uploading...'
});

// Complete upload
loadingStates.updateUploadProgress(uploadElement, 100, {
    status: 'Upload complete!'
});
```

## Loading Overlays

### Page Loading Overlay

```javascript
// Show page loading
loadingStates.showPageLoading({
    message: 'Loading application...',
    spinner: true
});

// Hide page loading
loadingStates.hidePageLoading();
```

### Section Loading Overlay

```javascript
// Show section loading
loadingStates.showSectionLoading('#dataSection', {
    message: 'Loading data...',
    spinner: true
});

// Hide section loading
loadingStates.hideSectionLoading('#dataSection');
```

## jQuery Integration

If jQuery is available, additional methods are provided:

```javascript
// Show skeleton
$('#container').showSkeleton({
    type: 'pulse',
    rows: 3
});

// Hide skeleton
$('#container').hideSkeleton();

// Show loading
$('#button').showLoading({
    text: 'Processing...'
});

// Hide loading
$('#button').hideLoading();
```

## Utility Functions

Global utility functions for common patterns:

```javascript
// Quick page loader
showPageLoader('Loading...');
hidePageLoader();

// Quick button loader
showButtonLoader('#myButton', 'Saving...');
hideButtonLoader('#myButton');
```

## Automatic Loading States

The system automatically handles:

### Form Submissions
```html
<!-- Automatic loading on form submit -->
<form id="myForm">
    <button type="submit">Submit</button>
</form>

<!-- Skip automatic loading -->
<form data-no-loading>
    <button type="submit">Submit</button>
</form>
```

### AJAX Requests
```javascript
// Automatic page loading for fetch requests
fetch('/api/data')
    .then(response => response.json())
    .then(data => console.log(data));

// Skip automatic loading
fetch('/api/data', {
    headers: {
        'X-No-Loading': 'true'
    }
});
```

## CSS Classes Reference

### Skeleton Classes
- `.skeleton` - Base skeleton element
- `.skeleton-pulse` - Pulse animation
- `.skeleton-wave` - Wave animation
- `.skeleton-text` - Text line skeleton
- `.skeleton-heading` - Heading skeleton
- `.skeleton-avatar` - Avatar/profile picture skeleton
- `.skeleton-button` - Button skeleton
- `.skeleton-image` - Image placeholder skeleton

### Loading Classes
- `.loading-spinner` - Default spinner
- `.loading-spinner-gradient` - Gradient spinner
- `.loading-dots` - Dots animation
- `.loading-pulse-ring` - Pulse ring animation

### State Classes
- `.is-loading` - General loading state
- `.loading-disabled` - Disabled during loading
- `.btn-loading` - Button loading state
- `.section-loading` - Section loading state

### Utility Classes
- `.no-animation` - Disable animations
- `.slow-animation` - Slower animations
- `.fast-animation` - Faster animations

## Accessibility Features

### Reduced Motion Support
The system respects `prefers-reduced-motion` settings:

```css
@media (prefers-reduced-motion: reduce) {
    /* Animations are disabled or simplified */
}
```

### Screen Reader Support
```html
<!-- Screen reader text -->
<span class="sr-only">Loading content, please wait...</span>

<!-- ARIA labels -->
<div class="loading-spinner" aria-label="Loading" role="status"></div>
```

### Keyboard Navigation
```javascript
// Focus management during loading states
loadingStates.showPageLoading({
    message: 'Loading...',
    maintainFocus: true
});
```

## Performance Optimization

### GPU Acceleration
Animations use GPU acceleration for smooth performance:

```css
.skeleton {
    transform: translateZ(0);
    backface-visibility: hidden;
}
```

### Efficient Animations
- Uses `transform` and `opacity` for animations
- Avoids layout-triggering properties
- Optimized for 60fps performance

## Browser Support

- **Modern Browsers**: Full support with all features
- **IE11+**: Basic support with fallbacks
- **Mobile**: Optimized for touch devices
- **High Contrast**: Supports high contrast mode

## Examples in the Codebase

### Dashboard Loading
```javascript
// Show skeleton while loading statistics
showDashboardSkeleton();
loadStatistics().then(() => {
    hideDashboardSkeleton();
});
```

### File Upload
```javascript
// Show upload progress
const uploadElement = loadingStates.showUploadProgress('#uploadArea', {
    fileName: file.name,
    progress: 0
});

// Update progress during upload
xhr.upload.onprogress = (e) => {
    const progress = (e.loaded / e.total) * 100;
    loadingStates.updateUploadProgress(uploadElement, progress);
};
```

### Form Submission
```javascript
// Automatic loading on form submit
$('#registrationForm').on('submit', function(e) {
    // Loading state is automatically shown
    // Will be hidden when page redirects or on error
});
```

## Customization

### Custom Skeleton Types
```css
.skeleton-custom {
    background: linear-gradient(90deg, 
        rgba(255, 255, 255, 0.1) 25%, 
        rgba(255, 255, 255, 0.3) 50%, 
        rgba(255, 255, 255, 0.1) 75%);
    animation: customShimmer 2s infinite;
}
```

### Custom Spinners
```css
.loading-spinner-custom {
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-top: 3px solid #your-color;
    animation: spin 1s linear infinite;
}
```

## Best Practices

1. **Show loading states for operations > 200ms**
2. **Use skeleton screens for initial page loads**
3. **Use spinners for button actions**
4. **Use progress bars for file uploads**
5. **Provide cancel options for long operations**
6. **Test with reduced motion settings**
7. **Ensure proper focus management**
8. **Use appropriate loading messages**

## Troubleshooting

### Common Issues

**Skeleton not showing:**
- Check if container has content
- Verify CSS files are loaded
- Check JavaScript console for errors

**Loading state not hiding:**
- Ensure `hideButtonLoading()` is called
- Check for JavaScript errors
- Verify element selectors are correct

**Animations not smooth:**
- Check for CSS conflicts
- Verify GPU acceleration is working
- Test on different devices

### Debug Mode
```javascript
// Enable debug logging
window.loadingStates.debug = true;
```

This comprehensive loading states system enhances the user experience by providing clear visual feedback during all loading operations while maintaining accessibility and performance standards.