// Camera functionality for cattle breed identification
class CameraManager {
    constructor() {
        this.video = document.getElementById('camera-preview');
        this.canvas = document.getElementById('capture-canvas');
        this.captureBtn = document.getElementById('capture-btn');
        this.stopCameraBtn = document.getElementById('stop-camera-btn');
        this.cameraSection = document.getElementById('camera-section');
        this.previewSection = document.getElementById('preview-section');
        this.previewImage = document.getElementById('preview-image');
        
        this.stream = null;
        this.isStreaming = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Capture photo button
        this.captureBtn.addEventListener('click', () => {
            this.capturePhoto();
        });
        
        // Stop camera button
        this.stopCameraBtn.addEventListener('click', () => {
            this.stopCamera();
        });
    }
    
    async startCamera() {
        try {
            // Request camera access with high quality settings
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment' // Prefer back camera on mobile
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            this.isStreaming = true;
            
            // Show camera section
            this.cameraSection.style.display = 'block';
            this.previewSection.style.display = 'none';
            
            console.log('Camera started successfully');
            
            // Wait for video to load and play
            return new Promise((resolve) => {
                this.video.addEventListener('loadedmetadata', () => {
                    this.video.play();
                    resolve();
                });
            });
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.handleCameraError(error);
            throw error;
        }
    }
    
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            this.isStreaming = false;
        }
        
        this.video.srcObject = null;
        this.cameraSection.style.display = 'none';
        
        console.log('Camera stopped');
    }
    
    capturePhoto() {
        if (!this.isStreaming || !this.video.videoWidth) {
            console.error('Camera not ready for capture');
            return;
        }
        
        try {
            // Set canvas dimensions to match video
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            
            // Draw current frame to canvas
            const context = this.canvas.getContext('2d');
            context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Convert to blob
            this.canvas.toBlob((blob) => {
                if (blob) {
                    this.handleCapturedPhoto(blob);
                } else {
                    console.error('Failed to capture photo');
                    this.showError('Failed to capture photo. Please try again.');
                }
            }, 'image/jpeg', 0.8);
            
        } catch (error) {
            console.error('Error capturing photo:', error);
            this.showError('Error capturing photo. Please try again.');
        }
    }
    
    handleCapturedPhoto(blob) {
        // Create object URL for preview
        const imageUrl = URL.createObjectURL(blob);
        this.previewImage.src = imageUrl;
        
        // Store blob for upload
        this.capturedBlob = blob;
        
        // Stop camera and show preview
        this.stopCamera();
        this.showPreview();
        
        console.log('Photo captured successfully');
    }
    
    showPreview() {
        this.cameraSection.style.display = 'none';
        this.previewSection.style.display = 'block';
        this.previewSection.classList.add('fade-in');
    }
    
    getCapturedBlob() {
        return this.capturedBlob;
    }
    
    handleCameraError(error) {
        let errorMessage = 'Unable to access camera. ';
        
        switch (error.name) {
            case 'NotAllowedError':
                errorMessage += 'Please allow camera permissions and try again.';
                break;
            case 'NotFoundError':
                errorMessage += 'No camera found on this device.';
                break;
            case 'NotReadableError':
                errorMessage += 'Camera is already in use by another application.';
                break;
            case 'OverconstrainedError':
                errorMessage += 'Camera does not support the requested settings.';
                break;
            case 'SecurityError':
                errorMessage += 'Camera access blocked due to security restrictions.';
                break;
            default:
                errorMessage += error.message || 'Unknown camera error occurred.';
        }
        
        this.showError(errorMessage);
    }
    
    showError(message) {
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');
        
        if (errorSection && errorMessage) {
            errorMessage.textContent = message;
            errorSection.style.display = 'block';
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorSection.style.display = 'none';
            }, 5000);
        }
        
        console.error('Camera error:', message);
    }
    
    reset() {
        this.stopCamera();
        this.previewSection.style.display = 'none';
        this.capturedBlob = null;
        
        // Clean up object URLs
        if (this.previewImage.src.startsWith('blob:')) {
            URL.revokeObjectURL(this.previewImage.src);
            this.previewImage.src = '';
        }
    }
    
    // Check if camera is supported
    static isSupported() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }
}

// Initialize camera manager when DOM is loaded
let cameraManager;

document.addEventListener('DOMContentLoaded', function() {
    // Check camera support
    if (!CameraManager.isSupported()) {
        console.warn('Camera not supported on this device');
        const cameraBtn = document.getElementById('camera-btn');
        if (cameraBtn) {
            cameraBtn.disabled = true;
            cameraBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Camera Not Supported';
        }
        return;
    }
    
    // Initialize camera manager
    cameraManager = new CameraManager();
    
    // Camera button click handler
    const cameraBtn = document.getElementById('camera-btn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', async function() {
            try {
                // Hide other sections
                document.getElementById('upload-section').style.display = 'none';
                document.getElementById('preview-section').style.display = 'none';
                
                // Show loading state
                cameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting Camera...';
                cameraBtn.disabled = true;
                
                await cameraManager.startCamera();
                
                // Reset button
                cameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Use Camera';
                cameraBtn.disabled = false;
                
            } catch (error) {
                console.error('Failed to start camera:', error);
                cameraBtn.innerHTML = '<i class="fas fa-camera me-2"></i>Use Camera';
                cameraBtn.disabled = false;
            }
        });
    }
    
    // Reset button handler
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            if (cameraManager) {
                cameraManager.reset();
            }
            
            // Hide all sections
            document.getElementById('camera-section').style.display = 'none';
            document.getElementById('upload-section').style.display = 'none';
            document.getElementById('preview-section').style.display = 'none';
            document.getElementById('loading-section').style.display = 'none';
            document.getElementById('results-section').style.display = 'none';
            document.getElementById('error-section').style.display = 'none';
        });
    }
});

// Clean up when page unloads
window.addEventListener('beforeunload', function() {
    if (cameraManager) {
        cameraManager.reset();
    }
});
