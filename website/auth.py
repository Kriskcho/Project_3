from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from website import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import re
from sqlalchemy.exc import IntegrityError

auth = Blueprint('auth', __name__)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        existing_username = User.query.filter_by(username=username).first()
        
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif not is_valid_email(email):
            flash('Invalid email format.', category='error')
        elif existing_username:
            flash('Username already exists.', category='error')
        elif len(username) < 2:
            flash('Username must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            try:
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.myaccount'))
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred. Please try again.', category='error')

    return render_template('sign_up.html', user=current_user)
                    
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.myaccount'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')  
    return render_template('myaccount.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('currentPassword')
        new_password1 = request.form.get('newPassword1')
        new_password2 = request.form.get('newPassword2')

        if not check_password_hash(current_user.password, current_password):
            flash('Current password is incorrect.', category='error')
        elif current_password == new_password1:
            flash('New password must be different from the current password.', category='error')
        elif new_password1 != new_password2:
            flash('New passwords do not match.', category='error')
        elif len(new_password1) < 7:
            flash('New password must be at least 7 characters long.', category='error')
        else:
            current_user.password = generate_password_hash(new_password1, method='pbkdf2:sha256')
            db.session.commit()
            flash('Password changed successfully!', category='success')
            return redirect(url_for('views.home'))

    return render_template('change_password.html', user=current_user)

@auth.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        confirm = request.form.get('confirm')
        if confirm == 'DELETE':
            user = User.query.get(current_user.id)
            db.session.delete(user)
            db.session.commit()
            logout_user()
            flash('Your account has been deleted.', category='success')
            return redirect(url_for('views.myaccount'))
        else:
            flash('Please type DELETE to confirm.', category='error')
    
    return render_template('delete_account.html', user=current_user)
    
