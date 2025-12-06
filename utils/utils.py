import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import logging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    try:
        if not file or not allowed_file(file.filename):
            return None
        
        # Create uploads directory if it doesn't exist
        upload_dir = 'static/uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save the file
        file.save(file_path)
        
        # Optimize image size
        optimize_image(file_path)
        
        logging.info(f"File saved successfully: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        return None

def optimize_image(file_path, max_size=(800, 800), quality=85):
    """Optimize image size and quality"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(file_path, 'JPEG', quality=quality, optimize=True)
            
        logging.info(f"Image optimized: {file_path}")
        
    except Exception as e:
        logging.error(f"Error optimizing image: {str(e)}")

def get_file_size(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except:
        return 0
