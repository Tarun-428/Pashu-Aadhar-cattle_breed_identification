import os
import uuid
from flask import render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app import app, db
from models import CattleBreed, IdentificationResult, User, CattleRecord
from ai_model import predict_breed
from utils.utils import allowed_file, save_uploaded_file
import logging

# Import and register blueprints
from auth_routes import auth_bp
from cattle_routes import cattle_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(cattle_bp)

@app.route('/')
def index():
    """Home page displaying cattle breed information"""
    breeds = CattleBreed.query.all()
    return render_template('index.html', breeds=breeds)

@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect to cattle dashboard"""
    return redirect(url_for('cattle.dashboard'))

@app.route('/breed/<int:breed_id>')
def breed_details(breed_id):
    """Display detailed information about a specific breed"""
    breed = CattleBreed.query.get_or_404(breed_id)
    return render_template('breed_details.html', breed=breed)

@app.route('/identify')
def identify():
    """Breed identification page"""
    return render_template('identify.html')

@app.route('/api/identify', methods=['POST'])
def api_identify():
    """API endpoint for breed identification"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload JPG, JPEG, PNG, or GIF files.'}), 400
        
        # Save the uploaded file
        filename = save_uploaded_file(file)
        if not filename:
            return jsonify({'error': 'Failed to save uploaded file'}), 500
        
        # Predict the breed
        try:
            prediction_result = predict_breed(filename)
            if not prediction_result:
                return jsonify({'error': 'Failed to process image for breed identification'}), 500
            
            breed_name = prediction_result['breed']
            confidence = prediction_result['confidence']
            
            # Find the breed in database
            breed = CattleBreed.query.filter(
                CattleBreed.name.ilike(f'%{breed_name}%')
            ).first()
            
            if breed:
                # Save identification result
                result = IdentificationResult(
                    image_filename=filename,
                    predicted_breed_id=breed.id,
                    confidence_score=confidence
                )
                db.session.add(result)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'breed': breed.to_dict(),
                    'confidence': confidence,
                    'image_filename': filename,
                    'result_id': result.id
                })
            else:
                # Save result without breed match
                result = IdentificationResult(
                    image_filename=filename,
                    confidence_score=confidence
                )
                db.session.add(result)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'breed_name': breed_name,
                    'confidence': confidence,
                    'image_filename': filename,
                    'message': 'Breed identified but not found in our database',
                    'result_id': result.id
                })
                
        except Exception as e:
            logging.error(f"Prediction error: {str(e)}")
            return jsonify({'error': 'Failed to identify breed from image'}), 500
            
    except Exception as e:
        logging.error(f"API identify error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/results/<int:result_id>')
def results(result_id):
    """Display identification results"""
    result = IdentificationResult.query.get_or_404(result_id)
    return render_template('results.html', result=result)

@app.route('/api/breeds')
def api_breeds():
    """API endpoint to get all breeds"""
    breeds = CattleBreed.query.all()
    return jsonify([breed.to_dict() for breed in breeds])

@app.route('/api/breeds/<int:breed_id>')
def api_breed_details(breed_id):
    """API endpoint to get specific breed details"""
    breed = CattleBreed.query.get_or_404(breed_id)
    return jsonify(breed.to_dict())

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
