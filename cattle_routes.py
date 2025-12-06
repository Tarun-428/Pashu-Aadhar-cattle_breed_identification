import os
import json
import uuid
import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import User, CattleRecord, CattleBreed, NutritionPlan
from utils.utils import allowed_file, save_uploaded_file
from ai_model import predict_breed
import qrcode
import io
import base64
from PIL import Image

# Create Blueprint for cattle management routes
cattle_bp = Blueprint('cattle', __name__)

@cattle_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing registered cattle"""
    user_cattle = CattleRecord.query.filter_by(user_id=current_user.id).all()
    return render_template('cattle/dashboard.html', cattle_records=user_cattle)

@cattle_bp.route('/add_cattle')
@login_required
def add_cattle():
    """Add new cattle registration form"""
    breeds = CattleBreed.query.all()
    return render_template('cattle/add_cattle.html', breeds=breeds)

@cattle_bp.route('/register_cattle', methods=['POST'])
@login_required
def register_cattle():
    """Process cattle registration"""
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        cattle_type = request.form.get('cattle_type', '').strip()
        weight = float(request.form.get('weight', 0)) if request.form.get('weight') else None
        height = float(request.form.get('height', 0)) if request.form.get('height') else None
        width = float(request.form.get('width', 0)) if request.form.get('width') else None
        color = request.form.get('color', '').strip()
        has_disease = request.form.get('has_disease') == 'yes'
        disease_description = request.form.get('disease_description', '').strip() if has_disease else None
        breed_id = int(request.form.get('breed_id')) if request.form.get('breed_id') else None

        # NEW: Insurance fields
        has_insurance = request.form.get('has_insurance') == 'yes'
        insurance_id = request.form.get('insurance_id', '').strip() if has_insurance else None

        # Validate required fields
        if not all([name, address, cattle_type, weight, height, color, breed_id]):
            flash('All required fields must be filled.', 'danger')
            return redirect(url_for('cattle.add_cattle'))

        if cattle_type not in ['dairy', 'non_dairy']:
            flash('Invalid cattle type selected.', 'danger')
            return redirect(url_for('cattle.add_cattle'))

        # Handle image uploads
        image_fields = ['front_image', 'rear_image', 'left_image', 'right_image']
        saved_images = {}

        for field in image_fields:
            if field in request.files:
                file = request.files[field]
                if file and file.filename and allowed_file(file.filename):
                    filename = save_uploaded_file(file)
                    if filename:
                        saved_images[field] = filename

        cattle_id = CattleRecord.generate_cattle_id()

        if len(saved_images) < 4:
            flash('All 4 images (front, rear, left, right) are required for registration.', 'danger')
            return redirect(url_for('cattle.add_cattle'))

        # ✅ Create cattle record with insurance info
        cattle_record = CattleRecord(
            cattle_id=cattle_id,
            user_id=current_user.id,
            breed_id=breed_id,
            name=name,
            address=address,
            cattle_type=cattle_type,
            weight=weight,
            height=height,
            width=width,
            color=color,
            has_disease=has_disease,
            disease_description=disease_description,
            has_insurance=has_insurance,
            insurance_id=insurance_id,
            front_image=saved_images.get('front_image'),
            rear_image=saved_images.get('rear_image'),
            left_image=saved_images.get('left_image'),
            right_image=saved_images.get('right_image')
        )

        db.session.add(cattle_record)
        db.session.flush()

        qr_code_path = generate_qr_code(cattle_record.id, cattle_id)
        cattle_record.qr_code_path = qr_code_path

        db.session.commit()

        flash('Cattle registered successfully!', 'success')
        return redirect(url_for('cattle.cattle_details', cattle_id=cattle_record.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to register cattle. Error: {str(e)}', 'danger')
        return redirect(url_for('cattle.add_cattle'))


@cattle_bp.route('/cattle/<int:cattle_id>')
@login_required
def cattle_details(cattle_id):
    """Display cattle details (authenticated)"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    return render_template('cattle/cattle_details.html', cattle=cattle_record)

@cattle_bp.route('/public/cattle/<int:cattle_id>')
def public_cattle_card(cattle_id):
    """Display public cattle Aadhaar card via QR code scan (no login required)"""
    cattle_record = CattleRecord.query.get_or_404(cattle_id)
    return render_template('cattle/public_cattle_card.html', cattle=cattle_record)

@cattle_bp.route('/delete_cattle_form/<int:cattle_id>')
@login_required
def delete_cattle_form(cattle_id):
    """Show secure deletion confirmation form"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    
    # Generate simple math CAPTCHA
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    captcha_answer = num1 + num2
    
    # Store CAPTCHA answer in session
    session['captcha_answer'] = captcha_answer
    session['captcha_question'] = f"{num1} + {num2}"
    
    return render_template('cattle/delete_confirmation.html', 
                         cattle=cattle_record, 
                         captcha_question=session['captcha_question'])

@cattle_bp.route('/delete_cattle/<int:cattle_id>', methods=['POST'])
@login_required
def delete_cattle(cattle_id):
    """Securely delete cattle record with password and CAPTCHA verification"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    
    # Verify password
    password = request.form.get('password')
    if not password or not current_user.check_password(password):
        flash('Incorrect password. Deletion cancelled.', 'danger')
        return redirect(url_for('cattle.delete_cattle_form', cattle_id=cattle_id))
    
    # Verify CAPTCHA
    captcha_answer = request.form.get('captcha_answer')
    if not captcha_answer or int(captcha_answer) != session.get('captcha_answer'):
        flash('Incorrect CAPTCHA. Deletion cancelled.', 'danger')
        return redirect(url_for('cattle.delete_cattle_form', cattle_id=cattle_id))
    
    # Verify confirmation text
    confirm_text = request.form.get('confirm_text', '').strip().lower()
    expected_text = f"delete {cattle_record.name or cattle_record.cattle_id}".lower()
    if confirm_text != expected_text:
        flash(f'Please type exactly: "delete {cattle_record.name or cattle_record.cattle_id}" to confirm.', 'danger')
        return redirect(url_for('cattle.delete_cattle_form', cattle_id=cattle_id))
    
    try:
        # Clear session CAPTCHA
        session.pop('captcha_answer', None)
        session.pop('captcha_question', None)
        
        # Delete associated files
        image_fields = [cattle_record.front_image, cattle_record.rear_image, 
                       cattle_record.left_image, cattle_record.right_image]
        
        for image_path in image_fields:
            if image_path:
                try:
                    full_path = os.path.join('static/uploads', image_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except:
                    pass
        
        # Delete QR code
        if cattle_record.qr_code_path:
            try:
                qr_path = os.path.join('static/qr_codes', cattle_record.qr_code_path)
                if os.path.exists(qr_path):
                    os.remove(qr_path)
            except:
                pass
        
        db.session.delete(cattle_record)
        db.session.commit()
        
        flash(f'Cattle record "{cattle_record.name or cattle_record.cattle_id}" has been permanently deleted.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete cattle record. Please try again.', 'danger')
    
    return redirect(url_for('cattle.dashboard'))

@cattle_bp.route('/create_nutrition_plan/<int:cattle_id>')
@login_required
def create_nutrition_plan_form(cattle_id):
    """Show nutrition plan creation form"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    return render_template('cattle/nutrition_plan_form.html', cattle=cattle_record)

@cattle_bp.route('/generate_nutrition_plan/<int:cattle_id>', methods=['POST'])
@login_required
def generate_nutrition_plan(cattle_id):
    """Generate nutrition plan for cattle"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    
    try:
        # Get input parameters
        daily_milk = float(request.form.get('daily_milk_production', 0))
        daily_food = float(request.form.get('daily_food_intake', 0))
        daily_water = float(request.form.get('daily_water_consumption', 0))
        
        # Generate 7-day nutrition plan
        plan_data = create_nutrition_plan_data(cattle_record, daily_milk, daily_food, daily_water)
        
        # Check if plan already exists
        existing_plan = NutritionPlan.query.filter_by(cattle_record_id=cattle_record.id).first()
        
        if existing_plan:
            # Update existing plan
            existing_plan.daily_milk_production = daily_milk
            existing_plan.daily_food_intake = daily_food
            existing_plan.daily_water_consumption = daily_water
            existing_plan.plan_data = json.dumps(plan_data)
        else:
            # Create new plan
            nutrition_plan = NutritionPlan(
                cattle_record_id=cattle_record.id,
                daily_milk_production=daily_milk,
                daily_food_intake=daily_food,
                daily_water_consumption=daily_water,
                plan_data=json.dumps(plan_data)
            )
            db.session.add(nutrition_plan)
        
        db.session.commit()
        flash('Nutrition plan created successfully!', 'success')
        return redirect(url_for('cattle.view_nutrition_plan', cattle_id=cattle_record.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to create nutrition plan.', 'danger')
        return redirect(url_for('cattle.create_nutrition_plan_form', cattle_id=cattle_id))

@cattle_bp.route('/nutrition_plan/<int:cattle_id>')
@login_required
def view_nutrition_plan(cattle_id):
    """View nutrition plan for cattle"""
    cattle_record = CattleRecord.query.filter_by(id=cattle_id, user_id=current_user.id).first_or_404()
    nutrition_plan = NutritionPlan.query.filter_by(cattle_record_id=cattle_record.id).first()
    
    if not nutrition_plan:
        flash('No nutrition plan found for this cattle.', 'warning')
        return redirect(url_for('cattle.create_nutrition_plan_form', cattle_id=cattle_id))
    
    plan_data = json.loads(nutrition_plan.plan_data) if nutrition_plan.plan_data else {}
    
    return render_template('cattle/nutrition_plan.html', 
                         cattle=cattle_record, 
                         nutrition_plan=nutrition_plan,
                         plan_data=plan_data)

@cattle_bp.route('/api/identify_breed', methods=['POST'])
@login_required
def api_identify_breed():
    """API endpoint for breed identification during registration"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save temporary file for prediction
        filename = save_uploaded_file(file)
        if not filename:
            return jsonify({'error': 'Failed to save file'}), 500
        
        # Predict breed
        prediction_result = predict_breed(filename)
        if not prediction_result:
            return jsonify({'error': 'Failed to identify breed'}), 500
        
        # Find breed in database
        breed = CattleBreed.query.filter(
            CattleBreed.name.ilike(f"%{prediction_result['breed']}%")
        ).first()
        
        result = {
            'success': True,
            'predicted_breed': prediction_result['breed'],
            'confidence': prediction_result['confidence'],
            'filename': filename
        }
        
        if breed:
            result['breed_data'] = breed.to_dict()
            # Suggest attributes based on breed
            result['suggested_attributes'] = {
                'height': breed.average_height,
                'length': breed.average_length,
                'width': breed.average_width,
                'weight': breed.average_weight_female,
                'color': breed.color_pattern
            }

        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

def generate_qr_code(cattle_record_id, cattle_id):
    """Generate QR code for cattle record"""
    try:
        # Create QR code data (URL to public cattle card - no login required)
        base_url = request.url_root.rstrip('/')
        qr_data = f"{base_url}/public/cattle/{cattle_record_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_dir = 'static/qr_codes'
        os.makedirs(qr_dir, exist_ok=True)
        
        qr_filename = f"qr_{cattle_id}.png"
        qr_path = os.path.join(qr_dir, qr_filename)
        qr_img.save(qr_path)
        
        return qr_filename
        
    except Exception as e:
        return None

def create_nutrition_plan_data(cattle_record, daily_milk, daily_food, daily_water):
    """Create 7-day nutrition plan based on cattle breed and inputs"""
    breed = cattle_record.breed
    
    # Base nutrition recommendations
    base_plan = {
        'daily_recommendations': {
            'dry_matter_intake': f"{daily_food:.1f} kg",
            'water_intake': f"{daily_water:.1f} liters",
            'milk_production': f"{daily_milk:.1f} liters"
        },
        'weekly_schedule': []
    }
    
    # Generate 7-day plan
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i, day in enumerate(days):
        daily_plan = {
            'day': day,
            'morning': {
                'time': '6:00 AM',
                'feed': f"{daily_food * 0.4:.1f} kg concentrated feed",
                'water': f"{daily_water * 0.3:.1f} liters fresh water",
                'supplements': "Vitamin A & D supplements"
            },
            'afternoon': {
                'time': '1:00 PM',
                'feed': f"{daily_food * 0.3:.1f} kg green fodder",
                'water': f"{daily_water * 0.4:.1f} liters fresh water",
                'supplements': "Mineral mixture"
            },
            'evening': {
                'time': '6:00 PM',
                'feed': f"{daily_food * 0.3:.1f} kg hay/silage",
                'water': f"{daily_water * 0.3:.1f} liters fresh water",
                'supplements': "Salt lick available"
            }
        }
        
        # Add breed-specific recommendations
        if breed and breed.category == 'Dairy':
            daily_plan['special_notes'] = "High-energy feed for milk production"
        elif breed and breed.category == 'Beef':
            daily_plan['special_notes'] = "Protein-rich feed for muscle development"
        else:
            daily_plan['special_notes'] = "Balanced nutrition for overall health"
        
        base_plan['weekly_schedule'].append(daily_plan)
    
    # Add breed-specific recommendations
    if breed:
        base_plan['breed_recommendations'] = {
            'breed_name': breed.name,
            'special_care': get_breed_specific_care(breed),
            'feeding_tips': get_feeding_tips(breed)
        }
    
    return base_plan

def get_breed_specific_care(breed):
    """Get breed-specific care recommendations"""
    if 'Holstein' in breed.name:
        return "High milk producers need extra calcium and energy-rich feed"
    elif 'Jersey' in breed.name:
        return "Efficient converters, monitor body condition carefully"
    elif 'Angus' in breed.name:
        return "Hardy breed, provide adequate roughage and minerals"
    elif 'Brahman' in breed.name:
        return "Heat tolerant, ensure shade and adequate water supply"
    else:
        return "Provide balanced nutrition and regular health monitoring"

def get_feeding_tips(breed):
    """Get breed-specific feeding tips"""
    tips = [
        "Feed at regular intervals to maintain rumen health",
        "Provide fresh, clean water at all times",
        "Monitor body condition score regularly",
        "Adjust feed quantities based on milk production"
    ]
    
    if breed.climate_adaptation and 'hot' in breed.climate_adaptation.lower():
        tips.append("Feed during cooler parts of the day in hot weather")
    
    if breed.category == 'Dairy':
        tips.append("Increase energy feed during lactation period")
    
    return tips