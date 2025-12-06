// Upload functionality for cattle breed identification
class UploadManager {
    constructor() {
        this.fileInput = document.getElementById('file-input');
        this.uploadArea = document.getElementById('upload-area');
        this.uploadBtn = document.getElementById('upload-btn');
        this.uploadSection = document.getElementById('upload-section');
        this.previewSection = document.getElementById('preview-section');
        this.previewImage = document.getElementById('preview-image');
        this.identifyBtn = document.getElementById('identify-btn');
        this.loadingSection = document.getElementById('loading-section');
        this.resultsSection = document.getElementById('results-section');
        this.errorSection = document.getElementById('error-section');
        this.resetBtn = document.getElementById('reset-btn');
        
        this.selectedFile = null;
        this.maxFileSize = 16 * 1024 * 1024; // 16MB
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Upload button click
        this.uploadBtn.addEventListener('click', () => {
            this.showUploadSection();
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });
        
        // Drag and drop
        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });
        
        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('dragover');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
        
        // Identify button click
        this.identifyBtn.addEventListener('click', () => {
            this.identifyBreed();
        });
        
        // Reset button click
        this.resetBtn.addEventListener('click', () => {
            this.reset();
        });
    }
    
    showUploadSection() {
        // Hide other sections
        document.getElementById('camera-section').style.display = 'none';
        document.getElementById('preview-section').style.display = 'none';
        
        // Show upload section
        this.uploadSection.style.display = 'block';
        this.uploadSection.classList.add('fade-in');
    }
    
    handleFileSelect(file) {
        if (!file) {
            return;
        }
        
        // Validate file
        const validation = this.validateFile(file);
        if (!validation.valid) {
            this.showError(validation.message);
            return;
        }
        
        this.selectedFile = file;
        this.showPreview(file);
    }
    
    validateFile(file) {
        // Check file type
        if (!this.allowedTypes.includes(file.type)) {
            return {
                valid: false,
                message: 'Invalid file type. Please upload JPG, PNG, or GIF images only.'
            };
        }
        
        // Check file size
        if (file.size > this.maxFileSize) {
            const maxSizeMB = this.maxFileSize / (1024 * 1024);
            return {
                valid: false,
                message: `File too large. Please upload images smaller than ${maxSizeMB}MB.`
            };
        }
        
        return { valid: true };
    }
    
    showPreview(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            this.previewImage.src = e.target.result;
            this.uploadSection.style.display = 'none';
            this.previewSection.style.display = 'block';
            this.previewSection.classList.add('fade-in');
        };
        
        reader.onerror = () => {
            this.showError('Failed to read the selected file.');
        };
        
        reader.readAsDataURL(file);
    }
    
    async identifyBreed() {
        if (!this.selectedFile && !cameraManager?.getCapturedBlob()) {
            this.showError('No image selected for identification.');
            return;
        }
        
        try {
            // Show loading state
            this.showLoading();
            
            // Prepare form data
            const formData = new FormData();
            
            if (this.selectedFile) {
                formData.append('image', this.selectedFile);
            } else if (cameraManager?.getCapturedBlob()) {
                formData.append('image', cameraManager.getCapturedBlob(), 'captured_image.jpg');
            }
            
            // Make API request
            const response = await fetch('/api/identify', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showResults(result);
            } else {
                throw new Error(result.error || 'Unknown error occurred');
            }
            
        } catch (error) {
            console.error('Identification error:', error);
            this.hideLoading();
            this.showError(error.message || 'Failed to identify breed. Please try again.');
        }
    }
    
    showLoading() {
        this.previewSection.style.display = 'none';
        this.loadingSection.style.display = 'block';
        this.loadingSection.classList.add('fade-in');
        
        // Disable identify button
        this.identifyBtn.disabled = true;
    }
    
    hideLoading() {
        this.loadingSection.style.display = 'none';
        this.identifyBtn.disabled = false;
    }
    
    showResults(result) {
        this.hideLoading();
        
        // Populate results
        const resultContent = document.getElementById('result-content');
        if (resultContent && result.breed) {
            const breed = result.breed;
            const confidence = (result.confidence * 100).toFixed(1);
            
            resultContent.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h4 class="text-success mb-3">
                            <i class="fas fa-cow me-2"></i>${breed.name}
                        </h4>
                        ${breed.scientific_name ? `<p class="text-muted fst-italic mb-3">${breed.scientific_name}</p>` : ''}
                        
                        <div class="mb-3">
                            <h6 class="text-muted">Confidence Score</h6>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-success" 
                                     style="width: ${confidence}%">
                                    ${confidence}%
                                </div>
                            </div>
                        </div>
                        
                        ${breed.description ? `
                        <div class="mb-3">
                            <h6 class="text-muted">Description</h6>
                            <p>${breed.description.substring(0, 150)}${breed.description.length > 150 ? '...' : ''}</p>
                        </div>
                        ` : ''}
                        
                        <div class="d-flex flex-wrap gap-2 mb-3">
                            ${breed.origin ? `<span class="badge bg-secondary">${breed.origin}</span>` : ''}
                            ${breed.category ? `<span class="badge bg-primary">${breed.category}</span>` : ''}
                            ${breed.milk_production ? `<span class="badge bg-info">${breed.milk_production}L/day</span>` : ''}
                        </div>
                        
                        <div class="mt-3">
                            <a href="/breed/${breed.id}" class="btn btn-success me-2">
                                <i class="fas fa-info-circle me-1"></i>View Full Details
                            </a>
                            <button onclick="uploadManager.reset()" class="btn btn-outline-secondary">
                                <i class="fas fa-redo me-1"></i>Try Another
                            </button>
                        </div>
                    </div>
                    <div class="col-md-4">
                        ${breed.image_url ? `
                        <div class="text-center">
                            <h6 class="text-muted mb-2">Reference Image</h6>
                            <img src="${breed.image_url}" 
                                 class="img-fluid rounded shadow-sm" 
                                 alt="${breed.name}"
                                 style="max-height: 150px;">
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        } else if (result.breed_name) {
            // Show result for unmatched breed
            resultContent.innerHTML = `
                <div class="alert alert-warning">
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Breed Detected</h5>
                    <p>Detected: <strong>${result.breed_name}</strong></p>
                    <p>Confidence: <strong>${(result.confidence * 100).toFixed(1)}%</strong></p>
                    <p class="mb-0">This breed is not in our current database, but our AI has identified it with the confidence score above.</p>
                </div>
                <div class="text-center mt-3">
                    <button onclick="uploadManager.reset()" class="btn btn-primary">
                        <i class="fas fa-redo me-2"></i>Try Another Image
                    </button>
                </div>
            `;
        }
        
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('fade-in');
    }
    
    showError(message) {
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = message;
            this.errorSection.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.errorSection.style.display = 'none';
            }, 5000);
        }
        
        console.error('Upload error:', message);
    }
    
    reset() {
        // Reset all sections
        this.uploadSection.style.display = 'none';
        this.previewSection.style.display = 'none';
        this.loadingSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        
        // Reset file input
        this.fileInput.value = '';
        this.selectedFile = null;
        
        // Reset preview image
        this.previewImage.src = '';
        
        // Reset camera if active
        if (window.cameraManager) {
            cameraManager.reset();
        }
        
        // Re-enable identify button
        this.identifyBtn.disabled = false;
        
        console.log('Upload manager reset');
    }
    
    // Utility method to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize upload manager when DOM is loaded
let uploadManager;

document.addEventListener('DOMContentLoaded', function() {
    uploadManager = new UploadManager();
    
    // Add paste support for images
    document.addEventListener('paste', function(e) {
        const items = e.clipboardData?.items;
        if (!items) return;
        
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                if (file) {
                    uploadManager.handleFileSelect(file);
                    e.preventDefault();
                    break;
                }
            }
        }
    });
    
    console.log('Upload manager initialized');
});

// Global error handler for upload operations
window.addEventListener('error', function(e) {
    if (e.filename && e.filename.includes('upload.js')) {
        console.error('Upload script error:', e.error);
        if (uploadManager) {
            uploadManager.showError('An unexpected error occurred. Please refresh the page and try again.');
        }
    }
});
