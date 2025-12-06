from app import db
from datetime import datetime, timedelta
from sqlalchemy import Text, Float, Boolean
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import random
import string

class CattleBreed(db.Model):
    __tablename__ = 'cattle_breeds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    scientific_name = db.Column(db.String(150))
    origin = db.Column(db.String(100))
    category = db.Column(db.String(50))  # Dairy, Beef, Dual Purpose
    description = db.Column(Text)
    characteristics = db.Column(Text)
    average_weight_male = db.Column(Float)  # in kg
    average_weight_female = db.Column(Float)  # in kg
    average_height = db.Column(Float)  # in cm
    
    # ✅ New fields added here
    average_length = db.Column(Float)  # in cm
    average_width = db.Column(Float)   # in cm
    
    milk_production = db.Column(Float)  # liters per day
    color_pattern = db.Column(db.String(200))
    temperament = db.Column(db.String(100))
    climate_adaptation = db.Column(db.String(100))
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'scientific_name': self.scientific_name,
            'origin': self.origin,
            'category': self.category,
            'description': self.description,
            'characteristics': self.characteristics,
            'average_weight_male': self.average_weight_male,
            'average_weight_female': self.average_weight_female,
            'average_height': self.average_height,
            'average_length': self.average_length,  # ✅ Included
            'average_width': self.average_width,    # ✅ Included
            'milk_production': self.milk_production,
            'color_pattern': self.color_pattern,
            'temperament': self.temperament,
            'climate_adaptation': self.climate_adaptation,
            'image_url': self.image_url
        }

class IdentificationResult(db.Model):
    __tablename__ = 'identification_results'
    
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(200), nullable=False)
    predicted_breed_id = db.Column(db.Integer, db.ForeignKey('cattle_breeds.id'))
    confidence_score = db.Column(Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    predicted_breed = db.relationship('CattleBreed', backref='predictions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'image_filename': self.image_filename,
            'predicted_breed': self.predicted_breed.to_dict() if self.predicted_breed else None,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat()
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # OTP-related fields
    is_verified = db.Column(Boolean, default=False)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cattle = db.relationship('CattleRecord', backref='owner', lazy=True, cascade='all, delete-orphan')

    # ---------------- PASSWORD METHODS ---------------- #
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    # ---------------- USERNAME GENERATOR ---------------- #
    @staticmethod
    def generate_username(name):
        """Generate unique username from name"""
        base_username = ''.join(name.lower().split())[:8]
        random_suffix = ''.join(random.choices(string.digits, k=4))
        username = f"{base_username}{random_suffix}"
        
        # Ensure uniqueness
        while User.query.filter_by(username=username).first():
            random_suffix = ''.join(random.choices(string.digits, k=4))
            username = f"{base_username}{random_suffix}"
        
        return username

    # ---------------- OTP METHODS ---------------- #
    def generate_otp(self, minutes=5):
        """Generate OTP and set expiry"""
        self.otp_code = str(random.randint(100000, 999999))
        self.otp_expiry = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
        return self.otp_code

    def verify_otp(self, otp):
        """Verify OTP and expiry"""
        if self.otp_code == otp and datetime.utcnow() < self.otp_expiry:
            self.is_verified = True
            self.otp_code = None
            self.otp_expiry = None
            db.session.commit()
            return True
        return False

    def otp_is_expired(self):
        return datetime.utcnow() > self.otp_expiry if self.otp_expiry else True

    # ---------------- SERIALIZER ---------------- #
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'mobile': self.mobile,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat()
        }

class CattleRecord(db.Model):
    __tablename__ = 'cattle_records'
    
    id = db.Column(db.Integer, primary_key=True)
    cattle_id = db.Column(db.String(12), unique=True, nullable=False)  # 12-digit unique ID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    breed_id = db.Column(db.Integer, db.ForeignKey('cattle_breeds.id'))
    
    # Basic Information
    name = db.Column(db.String(100))  # Optional animal name
    address = db.Column(Text)
    cattle_type = db.Column(db.String(20), nullable=False)  # 'dairy' or 'non_dairy'
    
    # Physical Attributes (from AI + user input)
    weight = db.Column(Float)  # in kg
    height = db.Column(Float)  # in cm
    width = db.Column(Float)  # in cm
    color = db.Column(db.String(100))
    
    # Health Information
    has_disease = db.Column(Boolean, default=False)
    disease_description = db.Column(Text)

    # 🆕 Insurance Information
    has_insurance = db.Column(Boolean, default=False)
    insurance_id = db.Column(db.String(50), nullable=True)
    
    # Images
    front_image = db.Column(db.String(200))
    rear_image = db.Column(db.String(200))
    left_image = db.Column(db.String(200))
    right_image = db.Column(db.String(200))
    
    # QR Code
    qr_code_path = db.Column(db.String(200))
    
    # Timestamps
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    breed = db.relationship('CattleBreed', backref='registered_cattle')
    nutrition_plans = db.relationship('NutritionPlan', backref='cattle', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def generate_cattle_id():
        """Generate unique 12-digit cattle ID"""
        while True:
            cattle_id = ''.join(random.choices(string.digits, k=12))
            if not CattleRecord.query.filter_by(cattle_id=cattle_id).first():
                return cattle_id
    
    def get_images(self):
        """Get all animal images as list"""
        images = []
        for img_field in ['front_image', 'rear_image', 'left_image', 'right_image']:
            img_path = getattr(self, img_field)
            if img_path:
                images.append({
                    'type': img_field.replace('_image', '').title(),
                    'path': img_path
                })
        return images
    
    def to_dict(self):
        return {
            'id': self.id,
            'cattle_id': self.cattle_id,
            'name': self.name,
            'breed': self.breed.to_dict() if self.breed else None,
            'address': self.address,
            'weight': self.weight,
            'height': self.height,
            'width': self.width,
            'color': self.color,
            'has_disease': self.has_disease,
            'disease_description': self.disease_description,
            'has_insurance': self.has_insurance,
            'insurance_id': self.insurance_id,
            'images': self.get_images(),
            'qr_code_path': self.qr_code_path,
            'registration_date': self.registration_date.isoformat(),
            'created_at': self.created_at.isoformat()
        }

class NutritionPlan(db.Model):
    __tablename__ = 'nutrition_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    cattle_record_id = db.Column(db.Integer, db.ForeignKey('cattle_records.id'), nullable=False)
    
    # Input parameters
    daily_milk_production = db.Column(Float)  # liters
    daily_food_intake = db.Column(Float)  # kg
    daily_water_consumption = db.Column(Float)  # liters
    
    # Generated plan (stored as JSON-like text)
    plan_data = db.Column(Text)  # 7-day nutrition plan
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cattle_record_id': self.cattle_record_id,
            'daily_milk_production': self.daily_milk_production,
            'daily_food_intake': self.daily_food_intake,
            'daily_water_consumption': self.daily_water_consumption,
            'plan_data': self.plan_data,
            'created_at': self.created_at.isoformat()
        }
