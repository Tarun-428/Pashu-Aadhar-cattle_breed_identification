import os
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User
from utils.sms_service import send_otp, verify_otp
import json
from sqlalchemy import or_

auth_bp = Blueprint('auth', __name__)

# ✅ Registration Page
@auth_bp.route('/register', methods=['GET'])
def register():
    return render_template('auth/register.html')

# ✅ API: Step 1 - Send OTP and store data in session (not DB)
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp_api():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    mobile = request.form.get('mobile', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    # ✅ Validations
    if not all([name, email, mobile, password, confirm_password]):
        return jsonify({'status': 'error', 'message': 'All fields are required.'})

    if password != confirm_password:
        return jsonify({'status': 'error', 'message': 'Passwords do not match.'})

    if len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters long.'})

    if User.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': 'Email already registered.'})

    if User.query.filter_by(mobile=mobile).first():
        return jsonify({'status': 'error', 'message': 'Mobile number already registered.'})

    # ✅ Store user data in session temporarily (not in DB yet)
    session['pending_user'] = {
        'name': name,
        'email': email,
        'mobile': mobile,
        'password': password
    }

    # ✅ Send OTP via Twilio
    otp_response = send_otp(mobile)
    if not otp_response:
        return jsonify({'status': 'error', 'message': 'Failed to send OTP. Check Twilio configuration.'})

    return jsonify({'status': 'success', 'message': 'OTP sent successfully. Please verify to complete registration.'})

# ✅ API: Step 2 - Verify OTP and insert user in DB
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp_api():
    otp = request.form.get('otp', '').strip()
    pending_user = session.get('pending_user')

    if not pending_user:
        return jsonify({'status': 'error', 'message': 'No pending registration found.'})

    mobile = pending_user['mobile']

    # ✅ Verify OTP with Twilio
    if verify_otp(mobile, otp):
        username = User.generate_username(pending_user['name'])
        user = User(username=username,
                    name=pending_user['name'],
                    email=pending_user['email'],
                    mobile=pending_user['mobile'],
                    is_verified=True)
        user.set_password(pending_user['password'])

        try:
            db.session.add(user)
            db.session.commit()

            # ✅ Clear session after success
            session.pop('pending_user', None)

            # ✅ Return success + user ID for popup
            return jsonify({
                'status': 'success',
                'username': user.username,
                'user_id': user.id,
                'message': 'Registration successful!'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Database error. Please try again.'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid or expired OTP.'})

# ✅ Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username_or_email or not password:
            flash('Username/Email and password are required.', 'danger')
            return render_template('auth/login.html')

        # Check if input matches username OR email
        user = User.query.filter(
            or_(User.username == username_or_email, User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            if not user.is_verified:
                flash('Account not verified. Please complete OTP verification.', 'warning')
                return redirect(url_for('auth.register'))

            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')

# ✅ Logout Route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

# ✅ Profile Page
@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    
    if not name or not email:
        flash('Name and email are required.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Check if email is taken by another user
    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Email is already taken by another user.', 'danger')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.name = name
        current_user.email = email
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except:
        db.session.rollback()
        flash('Failed to update profile.', 'danger')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if len(new_password) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    except:
        db.session.rollback()
        flash('Failed to change password.', 'danger')
    
    return redirect(url_for('auth.profile'))