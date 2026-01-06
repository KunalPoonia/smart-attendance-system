/**
 * Toast Integration Examples
 * Shows how to integrate the Enhanced Toast System with existing application features
 */

// Example integrations for different parts of the attendance system

/**
 * Student Registration Success/Error Handling
 */
function handleStudentRegistration(success, studentName, errorMessage) {
    if (success) {
        Toast.success(`Student "${studentName}" has been registered successfully!`, {
            duration: 6000
        });
    } else {
        Toast.error(errorMessage || 'Failed to register student. Please try again.', {
            duration: 8000
        });
    }
}

/**
 * Attendance Marking Feedback
 */
function handleAttendanceMarking(detected, studentName, confidence) {
    if (detected) {
        Toast.success(`Attendance marked for ${studentName} (${Math.round(confidence * 100)}% confidence)`, {
            duration: 4000
        });
    } else {
        Toast.warning('No face detected. Please position yourself in front of the camera.', {
            duration: 5000
        });
    }
}

/**
 * File Upload Progress
 */
function handleFileUpload(stage, progress, fileName) {
    switch (stage) {
        case 'start':
            Toast.info(`Uploading ${fileName}...`, {
                duration: 0,
                closable: false,
                showProgress: false
            });
            break;
        case 'progress':
            // Update existing toast or show progress
            Toast.info(`Uploading ${fileName}... ${progress}%`, {
                duration: 0,
                closable: false
            });
            break;
        case 'success':
            Toast.clearAll(); // Clear upload progress
            Toast.success(`${fileName} uploaded successfully!`);
            break;
        case 'error':
            Toast.clearAll(); // Clear upload progress
            Toast.error(`Failed to upload ${fileName}. Please try again.`);
            break;
    }
}

/**
 * Data Export Notifications
 */
function handleDataExport(format, recordCount) {
    Toast.info(`Preparing ${recordCount} records for ${format.toUpperCase()} export...`, {
        duration: 3000
    });
    
    // Simulate export completion
    setTimeout(() => {
        Toast.success(`Export completed! ${recordCount} records exported to ${format.toUpperCase()}.`, {
            duration: 6000
        });
    }, 3000);
}

/**
 * System Status Updates
 */
function handleSystemStatus(status, message) {
    switch (status) {
        case 'online':
            Toast.success('System is online and ready.', { duration: 3000 });
            break;
        case 'offline':
            Toast.error('System is offline. Please check your connection.', { duration: 0 });
            break;
        case 'maintenance':
            Toast.warning('System maintenance in progress. Some features may be unavailable.', { 
                duration: 10000 
            });
            break;
        case 'update':
            Toast.info(message || 'System update available.', { duration: 8000 });
            break;
    }
}

/**
 * Form Validation Integration
 */
function enhanceFormValidation() {
    // Override default form submission to use toasts
    document.addEventListener('DOMContentLoaded', function() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const formData = new FormData(this);
                const formName = this.getAttribute('name') || 'form';
                
                // Show processing toast
                Toast.info(`Processing ${formName}...`, {
                    duration: 0,
                    closable: false,
                    showProgress: false
                });
            });
        });
    });
}

/**
 * Camera Permission Handling
 */
function handleCameraPermission(granted, error) {
    if (granted) {
        Toast.success('Camera access granted. You can now mark attendance.', {
            duration: 4000
        });
    } else {
        Toast.error(error || 'Camera access denied. Please allow camera access to mark attendance.', {
            duration: 8000,
            closable: true
        });
    }
}

/**
 * Batch Operations
 */
function handleBatchOperation(operation, total, processed, failed) {
    if (processed === total) {
        if (failed === 0) {
            Toast.success(`${operation} completed successfully! ${processed} items processed.`, {
                duration: 6000
            });
        } else {
            Toast.warning(`${operation} completed with ${failed} errors. ${processed - failed} items processed successfully.`, {
                duration: 8000
            });
        }
    }
}

/**
 * Real-time Updates
 */
function handleRealTimeUpdate(type, data) {
    switch (type) {
        case 'new_attendance':
            Toast.info(`New attendance record: ${data.studentName} at ${data.time}`, {
                duration: 4000
            });
            break;
        case 'new_student':
            Toast.info(`New student registered: ${data.studentName}`, {
                duration: 4000
            });
            break;
        case 'system_alert':
            Toast.warning(data.message, {
                duration: data.duration || 6000
            });
            break;
    }
}

/**
 * Keyboard Shortcuts Integration
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Shift + combinations for quick actions
        if ((e.ctrlKey || e.metaKey) && e.shiftKey) {
            switch (e.key) {
                case 'S':
                    e.preventDefault();
                    Toast.success('Quick save shortcut activated!');
                    break;
                case 'E':
                    e.preventDefault();
                    Toast.info('Quick export shortcut activated!');
                    break;
                case 'R':
                    e.preventDefault();
                    Toast.warning('Quick refresh shortcut activated!');
                    break;
            }
        }
    });
}

/**
 * Auto-save Notifications
 */
function handleAutoSave(success, lastSaved) {
    if (success) {
        Toast.info(`Auto-saved at ${lastSaved}`, {
            duration: 2000,
            showProgress: false
        });
    } else {
        Toast.warning('Auto-save failed. Please save manually.', {
            duration: 5000
        });
    }
}

/**
 * Connection Status Monitoring
 */
function monitorConnectionStatus() {
    window.addEventListener('online', function() {
        Toast.success('Connection restored. All features are now available.', {
            duration: 4000
        });
    });
    
    window.addEventListener('offline', function() {
        Toast.error('Connection lost. Working in offline mode.', {
            duration: 0,
            closable: true
        });
    });
}

/**
 * Initialize all integrations
 */
function initializeToastIntegrations() {
    enhanceFormValidation();
    setupKeyboardShortcuts();
    monitorConnectionStatus();
    
    // Show welcome message
    setTimeout(() => {
        Toast.info('Enhanced notification system is active!', {
            duration: 3000
        });
    }, 1000);
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeToastIntegrations);

// Export functions for global use
window.ToastIntegration = {
    studentRegistration: handleStudentRegistration,
    attendanceMarking: handleAttendanceMarking,
    fileUpload: handleFileUpload,
    dataExport: handleDataExport,
    systemStatus: handleSystemStatus,
    cameraPermission: handleCameraPermission,
    batchOperation: handleBatchOperation,
    realTimeUpdate: handleRealTimeUpdate,
    autoSave: handleAutoSave
};

/**
 * Usage Examples:
 * 
 * // Student registration
 * ToastIntegration.studentRegistration(true, 'John Doe');
 * ToastIntegration.studentRegistration(false, null, 'Email already exists');
 * 
 * // Attendance marking
 * ToastIntegration.attendanceMarking(true, 'Jane Smith', 0.95);
 * ToastIntegration.attendanceMarking(false);
 * 
 * // File upload
 * ToastIntegration.fileUpload('start', 0, 'student_photo.jpg');
 * ToastIntegration.fileUpload('progress', 50, 'student_photo.jpg');
 * ToastIntegration.fileUpload('success', 100, 'student_photo.jpg');
 * 
 * // System status
 * ToastIntegration.systemStatus('online');
 * ToastIntegration.systemStatus('maintenance');
 * 
 * // Batch operations
 * ToastIntegration.batchOperation('Student Import', 100, 95, 5);
 */