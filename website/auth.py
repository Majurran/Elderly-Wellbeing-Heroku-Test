from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, NursingHome, InputOptions
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login-type') # Staff/User is "login" while Guest is "login-guest"
        
        # Staff/User
        if login_type == "login":
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            if user:
                # if check_password_hash(user.password, password):
                if user.password == password:
                    # flash('Logged in successfully!', category='success')
                    admin = user.admin
                    login_user(user, remember=True)
                    if admin:
                        return redirect(url_for('views.home'))
                    else:
                        return redirect(url_for('views.home_user'))
                        
                else:
                    flash('Incorrect password, try again.', category='error')
            else:
                flash('Email does not exist.', category='error')
        # Guest
        elif login_type == "login-guest":
            nursing_home_ID = request.form.get('homeId')
            
            guest = User.query.filter_by(nursing_home_id=nursing_home_ID).first()
            if guest:
                login_user(guest, remember=True)
                return redirect(url_for('views.guest_inputs'))
            else:
                flash('Wrong Nursing Home ID', category='error')
        else:
            flash('Something went wrong, could not find the right login form', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# TODO: Needs some clean up and the front end as well, need to decide which input labels to record/keep
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Creates the one admin profile for each nursing home
        nursing_home_name = request.form.get('nursing-home-name')
        nursing_home_id = request.form.get('homeId')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        agreeCheck = request.form.get('agreeCheck')

        # Look up email and nursing home name to see if they exist in the database already
        existing_nursing_home_admin_email = User.query.filter_by(email=email).first()
        existing_nursing_home_name = NursingHome.query.filter_by(name=nursing_home_name).first()
        
        if existing_nursing_home_admin_email:
            flash('Email already exists.', category='error')
        elif existing_nursing_home_name:
            flash('Nursing Home Name already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 6:
            flash('Password must be at least 6 characters.', category='error')
        elif not nursing_home_id.isdigit():
            flash('Nursing home ID must use digits only.', category='error')
        elif len(nursing_home_id) < 6:
            flash('Nursing home ID must be at least 6 digits.', category='error')
        elif not agreeCheck:
            flash('Must agree to Terms and Conditions.', category='error')
        else:
            # Add new NursingHome
            new_nursing_home = NursingHome(id=nursing_home_id, name=nursing_home_name)
            db.session.add(new_nursing_home)
            db.session.commit()
            
            # Can use the generate_password_hash(password1) in production but for developing/testing no need 
            # Add new User (admin/guest) account associated with new NursingHome
            new_admin_account = User(email=email, password=password1, nursing_home_id=nursing_home_id, admin=True)
            db.session.add(new_admin_account)
            db.session.commit()
            
            # Add default input options for wellbeing and activity for new NursingHome
            # Default activity and wellbeing list from prototype design
            activity_list = ['Go Cycling', 'Go Travel', 'Birthday Party', 'Go Boating', 'Write Diary', 'Drinking', 'Play the Piano', 'Online Shopping']
            wellbeing_list = ['Happy', 'Upvote', 'Congratulations', 'Love', 'Upset', 'Sick', 'Sleeping', 'Angry']
            
            activity_list_file_path = [
                "./static/input_option_img/Go Cycling.png",
                "./static/input_option_img/Go Travel.png",
                "./static/input_option_img/Birthday Party.png",
                "./static/input_option_img/Go Boating.png",
                "./static/input_option_img/Write Diary.png",
                "./static/input_option_img/Drinking.png",
                "./static/input_option_img/Play the Piano.png",
                "./static/input_option_img/Online Shopping.png"
            ]
            
            wellbeing_list_file_path = [
                "./static/input_option_img/Happy.png",
                "./static/input_option_img/Upvote.png",
                "./static/input_option_img/Congratulations.png",
                "./static/input_option_img/Love.png",
                "./static/input_option_img/Upset.png",
                "./static/input_option_img/Sick.png",
                "./static/input_option_img/Sleeping.png",
                "./static/input_option_img/Angry.png"
            ]
            
            for i,activity in enumerate(activity_list):
                new_activity = InputOptions(category="activity", name=activity, file_path=activity_list_file_path[i], nursing_home_id=nursing_home_id)
                db.session.add(new_activity)
                db.session.commit()
                
            for i,wellbeing in enumerate(wellbeing_list):
                new_wellbeing = InputOptions(category="wellbeing", name=wellbeing, file_path=wellbeing_list_file_path[i], nursing_home_id=nursing_home_id)
                db.session.add(new_wellbeing)
                db.session.commit()
            
            
            # login_user(new_user, remember=True)
            # flash('Account created!', category='success')
            # return redirect(url_for('views.home'))
            return render_template("sign_up.html", success='OK')

    return render_template("sign_up.html", user=current_user, success='')


# TODO: Resident User needs to merge together with the original sign up page, for the time being just getting the functionality working
@auth.route('/sign-up-user-temp', methods=['GET', 'POST'])
def sign_up_user_temporary():
    if request.method == 'POST':       
        # User form
        nursing_home_name = request.form.get('nursing-home-name')   # Use for verification
        nursing_home_id = request.form.get('homeId')                # Use for verification
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        phone_number = request.form.get('phone-number')
        gender = request.form.get('gender')                         
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        agreeCheck = request.form.get('agreeCheck')

        # Look up nursing_home_name and nursing_home_id to verify 
        verify_nursing_home_name = NursingHome.query.filter_by(name=nursing_home_name).first()
        verify_nursing_home_id = NursingHome.query.filter_by(id=nursing_home_id).first()
        existing_email = User.query.filter_by(email=email).first()
        
        # If name and id is correct, proceed with user creation
        if verify_nursing_home_id and verify_nursing_home_name:
            if existing_email:
                flash('Email already exists.', category='error')
            elif len(email) < 4:
                flash('Email must be greater than 4 characters.', category='error')
            elif password1 != password2:
                flash('Passwords don\'t match.', category='error')
            elif len(password1) < 6:
                flash('Password must be at least 6 characters.', category='error')
            elif not agreeCheck:
                flash('Must agree to Terms and Conditions.', category='error')
            else:
                # Can use the generate_password_hash(password1) in production but for developing/testing no need 
                # Add new User (admin/guest) account associated with new NursingHome
                new_account = User(first_name=first_name, last_name=last_name, phone=phone_number, email=email, gender=gender,
                                            password=password1, nursing_home_id=nursing_home_id, admin=False)
                db.session.add(new_account)
                db.session.commit()
                
                return render_template("sign_up_custom_user.html", success='OK')
        else:
            flash('Incorrect nursing home ID and nursing home name.', category='error')

    return render_template("sign_up_custom_user.html", user=current_user, success='')