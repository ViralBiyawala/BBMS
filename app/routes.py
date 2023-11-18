from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    make_response,
    abort,
    jsonify,
)
from flask_login import (
    LoginManager,
    login_user,
    current_user,
    logout_user,
    login_required,
)
# from flask_mail import Message
from app.models import *
from datetime import datetime, timedelta, date
import os
from app import app,myemail,server,app_login_key,mypass
import re, random
from email.mime.text import MIMEText
# from werkzeug.utils import secure_filename
from sqlalchemy import desc,func,asc
import pandas as pd 
pas = False
from functools import wraps



pt = os.path.join(app.root_path, 'city.csv')
city = pd.read_csv(pt)
cities = city["City"]

# For sending list of cities to JS file
@app.route('/get_cities_json')
def get_cities_json():
    cities = city["City"].tolist()
    return jsonify(cities=cities)

#initialization
# Store OTPs for email verification with their creation time
otp_storage = {}

# Define the OTP timeout duration in seconds (240 seconds in this case)
OTP_TIMEOUT = 240

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define custom role-based decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated :
            if current_user.has_role('admin'):
                return f(*args, **kwargs)
            else:
                return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))
    return decorated_function

def no_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated :
            if not current_user.has_role('admin'):
                return f(*args, **kwargs)
            else:
                return redirect(url_for('Admin'))
        else:
            return f(*args, **kwargs)
    return decorated_function


def hos_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated :
            if current_user.has_role('hospital'):
                return f(*args, **kwargs)
            else:
                return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.has_role('donor'):
                return f(*args, **kwargs)
            else:
                return redirect(url_for('Admin'))
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route('/Admin',methods=['GET','POST'])
@login_required
@admin_required
def Admin():
    selected_city = cities[0]
    sb = 'ALL'
    if request.method == 'POST':
        selected_city  = request.form['city']
        sb = request.form['Btype']
    
    # Define the order of blood types
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    
    

    # Create a list to store the summarized data
    summarized_data = []
    
    # Create a list to store the summarized data of Transfusion record
    summarized_data_tr = []
    
    # Create a list to store the summarized data from BloodInventory
    summarized_data_inventory = []

    # Query the database to group by blood type and sum up quantities
    for blood_type in blood_types:
        result = (
            db.session.query(
                func.sum(BloodDonationRecord.quantity_donated).label('total_quantity')
            )
            .filter(BloodDonationRecord.donation_type == blood_type)
            .first()
        )
        summarized_data.append(result.total_quantity if result[0] != None else 0.0)
        
    # Query the Blood Transfusion DB to group by blood type and sum up quantities
    for blood_type in blood_types:
        result = (
            db.session.query(
                func.sum(BloodTransfusionRecord.quantity_transfused).label('total_quantity')
            )
            .filter(BloodTransfusionRecord.blood_type == blood_type)
            .filter(BloodTransfusionRecord.status == 1)
            .first()
        )
        summarized_data_tr.append(result.total_quantity if result[0] != None else 0.0)
        
    # Query the database to group by blood type and sum up quantities for BloodInventory
    for blood_type in blood_types:
        result = (
            db.session.query(
                func.sum(BloodInventory.quantity_donated).label('total_quantity')
            )
            .filter(BloodInventory.blood_type == blood_type)
            .first()
        )
        summarized_data_inventory.append(result.total_quantity if result[0] is not None else 0.0)
    
    
    
    
    
    # Create a list to store the summarized data
    sd_city = {}
    
    # Query the database to find appointment IDs where city == selected_city
    appointment_ids = (
        DonationAppointment.query
        .filter(DonationAppointment.place == selected_city)
        .with_entities(DonationAppointment.appointment_id)
        .all()
    )
    
    blood_bag_nums = (
        BloodDonationRecord.query
        .filter(BloodDonationRecord.storage_location == selected_city)
        .with_entities(BloodDonationRecord.blood_bag_number)
        .all()
    )
    
    if sb == 'ALL' :
        # Query the database to group by blood type and sum up quantities
        for blood_type in blood_types:
                total_quantity = 0
                sd_city[blood_type] = []
                for appointment_id in appointment_ids:
                    result = (
                        db.session.query(
                            func.sum(BloodDonationRecord.quantity_donated).label('total_quantity')
                        )
                        .filter(BloodDonationRecord.donation_type == blood_type)
                        .filter(BloodDonationRecord.appointment_id == appointment_id[0])
                        .first()
                    )

                    if result and result.total_quantity:
                        total_quantity += result.total_quantity

                sd_city[blood_type].append(total_quantity)
                
        for blood_type in blood_types:
            total_quantity = 0
            result = (
                db.session.query(
                    func.sum(BloodTransfusionRecord.quantity_transfused).label('total_quantity')
                )
                .filter(BloodTransfusionRecord.blood_type == blood_type)
                .filter(BloodTransfusionRecord.status == 1)
                .filter(BloodTransfusionRecord.city1 == selected_city)
                .first()
            )
                
            if result and result.total_quantity:
                total_quantity += result.total_quantity
                    
            sd_city[blood_type].append(total_quantity)
                
        for blood_type in blood_types:
                total_quantity = 0

                result = (
                    db.session.query(
                        func.sum(BloodInventory.quantity_donated).label('total_quantity')
                    )
                    .filter(BloodInventory.blood_type == blood_type)
                    .filter(BloodInventory.storage_location == selected_city)
                    .first()
                )
                
                if result and result.total_quantity:
                    total_quantity += result.total_quantity

                sd_city[blood_type].append(total_quantity)
    else :
        total_quantity = 0
        sd_city[sb] = []
        for appointment_id in appointment_ids:
            result = (
                db.session.query(
                    func.sum(BloodDonationRecord.quantity_donated).label('total_quantity')
                )
                .filter(BloodDonationRecord.donation_type == sb)
                .filter(BloodDonationRecord.appointment_id == appointment_id[0])
                .first()
            )
            
            if result and result.total_quantity:
                total_quantity += result.total_quantity
        sd_city[sb].append(total_quantity)
        
        total_quantity = 0
        result = (
            db.session.query(
                func.sum(BloodTransfusionRecord.quantity_transfused).label('total_quantity')
            )
            .filter(BloodTransfusionRecord.blood_type == sb)
            .filter(BloodTransfusionRecord.status == 1)
            .filter(BloodTransfusionRecord.city1 == selected_city)
            .first()
        )
                
        if result and result.total_quantity:
            total_quantity += result.total_quantity
                
        sd_city[sb].append(total_quantity)
        
        total_quantity = 0
        result = (
            db.session.query(
                func.sum(BloodInventory.quantity_donated).label('total_quantity')
            )
            .filter(BloodInventory.blood_type == sb)
            # .filter(BloodInventory.blood_bag_number == blood_bag_num[0])
            .filter(BloodInventory.storage_location == selected_city)
            .first()
        )
        
        if result and result.total_quantity:
            total_quantity += result.total_quantity
        sd_city[sb].append(total_quantity)
    

    return render_template('Admin/Admin_Home.html',cities=cities,in_qu=summarized_data,inv=summarized_data_inventory,out_qu=summarized_data_tr,sd_city=sd_city,sc=selected_city,sb=sb)


#Helper functions
#loading user
@login_manager.user_loader
def load_user(user_id):
    # Check if the user_id is for an RDonor
    donor = RDonor.query.get(user_id)
    if donor:
        return donor

    # Check if the user_id is for an RHospital
    hospital = RHospital.query.get(user_id)
    if hospital:
        return hospital
    
    admin = AdminUser.query.get(user_id)
    if admin:
        return admin
    # If the user_id doesn't match either type, return None
    return None

# Email ID validation
def is_valid_email(email):
    # Regular expression for basic email validation
    email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
    return re.match(email_regex, email)

#Page Routing
#Route to Contact Page
@app.route('/contact')
@no_admin_required
def contact():
    src = "../static/images/profile.png"
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin') else None
    if user != None and user.has_role('donor'):
        donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
        if donor:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            # Check if an image file exists for the user
            current_path = os.getcwd() 
            for extension in allowed_extensions:
                image_path = f"/app/static/images/{donor.donor_id}.{extension}"
                filename = current_path + image_path
                if os.path.isfile(filename) == True:
                    src = f"../static/images/{donor.donor_id}.{extension}"
    elif user != None and user.has_role('hospital'):
        allowed_extensions = ['jpg', 'jpeg', 'png']
        # Check if an image file exists for the user
        current_path = os.getcwd() 
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"
    return render_template('contact.html',src=src,user=user)


@app.route('/about')
@no_admin_required
def about():
    src = "../static/images/profile.png"
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin') else None
    if user != None and user.has_role('donor'):
        donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
        if donor:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            # Check if an image file exists for the user
            current_path = os.getcwd() 
            for extension in allowed_extensions:
                image_path = f"/app/static/images/{donor.donor_id}.{extension}"
                filename = current_path + image_path
                if os.path.isfile(filename) == True:
                    src = f"../static/images/{donor.donor_id}.{extension}"
    elif user != None and user.has_role('hospital'):
        allowed_extensions = ['jpg', 'jpeg', 'png']
        # Check if an image file exists for the user
        current_path = os.getcwd() 
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"
    return render_template('AboutUs.html',src=src,user=user)

#By default Page
@app.route('/')
@no_admin_required
def base():
    src = "../static/images/profile.png"
    notifications = None
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    if user == None:
        initials = None
    elif current_user.has_role('donor'):
        donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
        if donor:
            id_noti = Donor.query.filter_by(d_email_id=user.d_email_id).first().donor_id
            appointment_ids = [appointment.appointment_id for appointment in DonationAppointment.query.filter_by(donor_id=id_noti).all()]
            latest_record = None
            if appointment_ids:
                # Step 2: Retrieve the latest BloodDonationRecord
                latest_record = BloodDonationRecord.query.filter(BloodDonationRecord.appointment_id.in_(appointment_ids)).order_by(BloodDonationRecord.collection_date.desc()).first()

                if latest_record:
                    # Step 3: Calculate the difference in days
                    difference_in_days = (datetime.now().date() - latest_record.collection_date).days

                    if difference_in_days >= 5:
                        # Add a record to the Notification table
                        notification_message = "Now you can donate Blood Again."
                        existing_notification = Notification.query.filter_by(donor_id=id_noti, appointment_id=latest_record.appointment_id, message=notification_message).first()

                        if not existing_notification:
                            # If the notification does not exist, create and commit a new one
                            new_notification = Notification(donor_id=id_noti, appointment_id=latest_record.appointment_id, message=notification_message,read=False)
                            db.session.add(new_notification)
                            db.session.commit()

            notifications = Notification.query.filter_by(donor_id=id_noti).order_by(Notification.timestamp.desc()).all()
            allowed_extensions = ['jpg', 'jpeg', 'png']
            # Check if an image file exists for the user
            current_path = os.getcwd() 
            for extension in allowed_extensions:
                image_path = f"/app/static/images/{donor.donor_id}.{extension}"
                filename = current_path + image_path
                if os.path.isfile(filename) == True:
                    src = f"../static/images/{donor.donor_id}.{extension}"
        else :
            flash("Fill Donor Information First")
            return redirect(url_for('profile'))
    else :
        notifications = HospitalNotification.query.filter_by(h_email_id=current_user.h_email_id).order_by(HospitalNotification.timestamp.desc()).all()
        
        allowed_extensions = ['jpg', 'jpeg', 'png']
        # Check if an image file exists for the user
        current_path = os.getcwd()
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"

    return render_template('index.html',user=user, src = src, notifications = notifications)

#Home Page
@app.route('/index')
@no_admin_required
def index():
    src = "../static/images/profile.png"
    notifications = None
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    if user == None:
        initials = None
    elif current_user.has_role('donor'):
        donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
        if donor:
            id_noti = Donor.query.filter_by(d_email_id=user.d_email_id).first().donor_id
            appointment_ids = [appointment.appointment_id for appointment in DonationAppointment.query.filter_by(donor_id=id_noti).all()]
            latest_record = None
            if appointment_ids:
                # Step 2: Retrieve the latest BloodDonationRecord
                latest_record = BloodDonationRecord.query.filter(BloodDonationRecord.appointment_id.in_(appointment_ids)).order_by(BloodDonationRecord.collection_date.desc()).first()

                if latest_record:
                    # Step 3: Calculate the difference in days
                    difference_in_days = (datetime.now().date() - latest_record.collection_date).days

                    if difference_in_days >= 5:
                        # Add a record to the Notification table
                        notification_message = "Now you can donate Blood Again."
                        existing_notification = Notification.query.filter_by(donor_id=id_noti, appointment_id=latest_record.appointment_id, message=notification_message).first()

                        if not existing_notification:
                            # If the notification does not exist, create and commit a new one
                            new_notification = Notification(donor_id=id_noti, appointment_id=latest_record.appointment_id, message=notification_message,read=False)
                            db.session.add(new_notification)
                            db.session.commit()

            notifications = Notification.query.filter_by(donor_id=id_noti).order_by(Notification.timestamp.desc()).all()

            allowed_extensions = ['jpg', 'jpeg', 'png']
            # Check if an image file exists for the user
            current_path = os.getcwd()
            for extension in allowed_extensions:
                image_path = f"/app/static/images/{donor.donor_id}.{extension}"
                filename = current_path + image_path
                if os.path.isfile(filename) == True:
                    src = f"../static/images/{donor.donor_id}.{extension}"
        else :
            flash("Fill Donor Information First")
            return redirect(url_for('profile'))
    else :
        
        notifications = HospitalNotification.query.filter_by(h_email_id=current_user.h_email_id).order_by(HospitalNotification.timestamp.desc()).all()
        
        allowed_extensions = ['jpg', 'jpeg', 'png']
        # Check if an image file exists for the user
        current_path = os.getcwd()
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"

    return render_template('index.html',user=user, src = src, notifications = notifications)

# generating basic template for certficate
@app.route('/certificate', methods=['GET'])
@login_required
@user_required
def verify():
    return render_template('Donor/certificate.html',name=('Life Saver Blood Donor',"DD-MM-YYYY","City"))

# route to confirm otp page
@app.route('/forget')
def forget():
    return render_template('confirm.html')

# Logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#Route to OTP Page
# @app.route('/otp')
# def otp():
#     return render_template('otp.html')


# @app.route('/cfm')
# def cfm():
#     return render_template('confirm.html')


# Email Sending 
# Route to Register Page with email duplication check
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve data from the registration form
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']
        mobile_no = request.form['mobile_no']
        password = request.form['password']
        admin_type = request.form['admin']  # Added to retrieve the user type (Donor or Hospital)
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.')
            return redirect(url_for('register'))
        
        
        # Check if the email is already registered
        existing_user = RDonor.query.filter_by(d_email_id=email).first()
        existing_user_H = RHospital.query.filter_by(h_email_id=email).first()
        if existing_user or existing_user_H:
            flash('Email is already registered.')
            return redirect(url_for('register'))

        # Generate a 6-digit random OTP
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and its creation time
        otp_storage[email] = {
            'otp': otp,
            'created_at': datetime.now()
        }
        
        # Send OTP email
        server.connect('smtp.gmail.com', 587)
        server.starttls()
        msg = MIMEText(f'Your OTP for email verification: {otp}')
        msg['Subject'] = 'Mail for Email Verification'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.login(myemail, app_login_key)
        server.send_message(msg)
        server.quit()
        
        # Render the OTP verification page and pass us*-er data along with the email
        return render_template('otp.html', email=email, name=name, city=city, mobile_no=mobile_no, password=password, admin_type=admin_type)

    return render_template('register.html')

#resend email verfication OTP mail
@app.route('/resend', methods=['POST'])
def resend():
    if request.method == 'POST':
        # Retrieve data from the registration form
        name = request.form['name']
        email = request.form['email']
        city = request.form['city']
        mobile_no = request.form['mobile_no']
        password = request.form['password']
        admin_type = request.form['admin']  # Added to retrieve the user type (Donor or Hospital)
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('register'))
        
        
        # Check if the email is already registered
        existing_user = RDonor.query.filter_by(d_email_id=email).first()
        if existing_user:
            flash('Email is already registered. Please use a different email address.', 'error')
            return redirect(url_for('register'))
        
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and its creation time
        otp_storage[email] = {
            'otp': otp,
            'created_at': datetime.now()
        }

        otp_s = otp_storage[email]
        otp_ans = otp_s['otp']
        # Send OTP email
        
        server.connect('smtp.gmail.com', 587)
        server.starttls()
        server.login(myemail, app_login_key)
        msg = MIMEText(f'Your OTP for email verification: {otp_ans}')
        msg['Subject'] = 'Mail for Email Verification'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.send_message(msg)
        server.quit()
        
        # Render the OTP verification page and pass us*-er data along with the email
        # flash('OTP Sent.Valid for 4 minutes.')
        return render_template('otp.html', email=email, name=name, city=city, mobile_no=mobile_no, password=password, admin_type=admin_type)
    return render_template('register.html')

#send forget password OTP mail
@app.route('/send_forget_otp', methods=['POST'])
def submit_reset_password():
    if request.method == 'POST':
        # Retrieve data from the submitted form
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the email exists in the database
        # Replace this with your database query logic
        existing_user = RDonor.query.filter_by(d_email_id=email).first()
        existing_user_H = RHospital.query.filter_by(h_email_id=email).first()
        if not (existing_user or existing_user_H):
            flash('Email is not registered.')
            return redirect(url_for('forget'))

        # Check if the password and confirm password match
        if password != confirm_password:
            flash('Password and Confirm Password doesn\'t match.')
            return redirect(url_for('forget'))
        
        # Generate a 6-digit random OTP
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and its creation time
        otp_storage[email] = {
            'otp': otp,
            'created_at': datetime.now()
        }
        
        # Send OTP email
        server.connect('smtp.gmail.com', 587)
        server.starttls()
        server.login(myemail, app_login_key)
        msg = MIMEText(f'Your OTP for Password Reset: {otp}')
        msg['Subject'] = 'Mail for Password Reset'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.send_message(msg)
        server.quit()
        flash('OTP Sent.Valid for 4 minutes.')
        # Render the OTP verification page and pass us*-er data along with the email
        return render_template('forget_otp.html', email=email, password=password)

#Forget passowrd resend mail
@app.route('/resend_forget', methods=['POST'])
def resend_forget():
    if request.method == 'POST':
        # Retrieve data from the registration form
        email = request.form['email']
        password = request.form['password']
        
        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('register'))
        
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and its creation time
        otp_storage[email] = {
            'otp': otp,
            'created_at': datetime.now()
        }

        otp_s = otp_storage[email]
        otp_ans = otp_s['otp']
        # Send OTP email
        
        server.connect('smtp.gmail.com', 587)
        server.starttls()
        server.login(myemail, app_login_key)
        msg = MIMEText(f'Your OTP for email verification for Password Reset is: {otp_ans}')
        msg['Subject'] = 'Mail for Password Reset'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.send_message(msg)
        server.quit()
        
        # Render the OTP verification page and pass us*-er data along with the email
        flash('OTP Sent.Valid for 4 minutes.')
        return render_template('forget_otp.html', email=email,password=password)

#Database Entry
# New User Register
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    if request.method == 'POST':
        email = request.form.get('email')
        user_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])  # Concatenate OTP digits
        name = request.form.get('name')
        city = request.form.get('city')
        mobile_no = request.form.get('mobile_no')
        password = request.form.get('password')
        admin_type = request.form.get('admin')

        stored_data = otp_storage.get(email)
        print(stored_data)
        if not stored_data or user_otp != stored_data['otp']:
            flash('Wrong OTP!!!')
            return render_template('otp.html', email=email, name=name, city=city, mobile_no=mobile_no, password=password, admin_type=admin_type)
            # return redirect(url_for('register'))

        # Check if the OTP is still valid
        created_at = stored_data['created_at']

        if datetime.now() - created_at <= timedelta(seconds=OTP_TIMEOUT):
            if admin_type == 'donor':
                new_user = RDonor(d_email_id=email, name=name, city=city, contact_phone=mobile_no)
                new_user.set_password(password)
            elif admin_type == 'hospital':
                new_user = RHospital(h_email_id=email, name=name, city=city, contact_phone=mobile_no)
                new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            except Exception as e:
                print(e)
                return redirect(url_for('contact'))
        else:
            flash('OTP has expired. Please try again.')
            return render_template('otp.html')


@app.route('/verify_forget_otp', methods=['POST'])
def verify_forget_otp():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])  # Concatenate OTP digits
        admin_type = None
        donor = RDonor.query.get(email)
        if donor:
            admin_type = "donor"

        hospital = RHospital.query.get(email)
        if hospital:
            admin_type = "hospital"

        stored_data = otp_storage.get(email)

        if not stored_data or user_otp != stored_data['otp']:
            flash('Wrong OTP!!!')
            return render_template('forget_otp.html', email=email,password=password)

        created_at = stored_data['created_at']

        if datetime.now() - created_at <= timedelta(seconds=OTP_TIMEOUT):
            if admin_type == 'donor':
                new_user = RDonor.query.get(email)
                new_user.set_password(password)
            elif admin_type == 'hospital':
                new_user = RHospital.query.get(email)
                new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
            except Exception as e:
                print(e)
                return redirect(url_for('contact'))
        else:
            flash('OTP has expired. Please try again.')
            return render_template('forget_otp.html')

#Certificate
#Route to Download Certificate Page
@app.route('/gc/<appointment_id>',methods=['GET'])
@login_required
@user_required
def gc(appointment_id):
    user = current_user
    data = Donor.query.filter_by(d_email_id=user.d_email_id).first()
    results = DonationAppointment.query.filter_by(appointment_id=appointment_id,donor_id = data.donor_id).first()
    if results is None:
        return redirect(url_for('profile'))
    name = data.first_name + " " + data.middle_name + " " + data.last_name
    html_template = render_template('Donor/certificate.html', name=(name,results.appointment_date, results.place))

    return html_template

# User Features
#User Logged In
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve data from the login form
        user_id = request.form['user_id']
        password = request.form['password']
        admin_type = request.form['admin']

        # Check the user type and fetch the appropriate user from the database
        if admin_type == 'donor':
            user = RDonor.query.filter_by(d_email_id=user_id).first()
        elif admin_type == 'hospital':
            user = RHospital.query.filter_by(h_email_id=user_id).first()
        elif admin_type == 'admin':
            admin_user = AdminUser.query.filter_by(username=user_id).first()
            if admin_user is not None and admin_user.password_hash == password:
                login_user(admin_user)
                return redirect(url_for('Admin'))
            else:
                flash('Invalid username or password.')
                return redirect(url_for('login'))  # Change 'home' to the desired page
        
        if user is not None:  # Check the password using check_password method
            if  user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))  # Change 'index' to the desired page
            else:
                flash('Invalid username or password.')
                return redirect(url_for('login'))
        else:
            flash('Please first register')
            return redirect(url_for('register'))  # Change 'home' to the desired page
    
    return render_template('login.html')

# Profile Page
@app.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    if request.method == 'POST':
        Fname = request.form['Fname']
        Mname = request.form['Mname']
        Lname = request.form['Lname']
        DOB = request.form['DOB']
        DOB = datetime.strptime(DOB, '%Y-%m-%d').date()
        gender = request.form['gender']
        mob = request.form['mob']
        address = request.form['address']
        city = request.form['city']
        Btype = request.form['Btype']
        # print(gender)
        if city.lower() not in [cit.lower() for cit in cities]:
            flash("No City Found")
            return redirect(url_for('profile'))
            

        data = Donor.query.filter_by(d_email_id=current_user.d_email_id).first()
        if data:
            # Update the attributes of the existing object
            data.first_name = Fname
            data.middle_name = Mname
            data.last_name = Lname
            data.date_of_birth = DOB
            data.gender = gender
            data.contact_phone = mob
            data.contact_address = address
            data.city = city
            data.blood_type = Btype
        else:
            # Create a new Donor object if it doesn't exist
            data = Donor(
                d_email_id=current_user.d_email_id,
                first_name=Fname,
                middle_name=Mname,
                last_name=Lname,
                date_of_birth=DOB,
                gender=gender,
                contact_phone=mob,
                contact_address=address,
                city=city,
                blood_type=Btype
            )

        # Add the updated or new object to the session and commit changes
        try:
            db.session.add(data)
            db.session.commit()
            return redirect(url_for('profile'))
        except Exception as e:
            print(e)
            return redirect(url_for('contact'))

    data = Donor.query.filter_by(d_email_id=current_user.d_email_id).first()
    results = None
    # print(data.gender)
    if data is None:
        src = "../static/images/profile.png"
        fr=None
        results=None
    else:
        results = DonationAppointment.query.filter_by(donor_id=data.donor_id).order_by(
        desc(DonationAppointment.appointment_date), desc(DonationAppointment.appointment_time)
    ).all()
        
        # Fetching all appointment_ids where donor_id matches
        donor_appointment_ids = [result.appointment_id for result in results]
        
        fr = DonationAppointment.query.filter(DonationAppointment.appointment_id.in_(donor_appointment_ids),DonationAppointment.ddone == True).all()
        donor_id = data.donor_id
        allowed_extensions = ['jpg', 'jpeg', 'png']

        # Check if an image file exists for the user
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{donor_id}.{extension}"
            current_path = os.getcwd()
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                # print(filename)
                src = f"../static/images/{donor_id}.{extension}"
                break
        else:
            src = "../static/images/profile.png"
    return render_template('Donor/profile.html', email=current_user, data=data,  src = src, results = results, cities=cities,fr = fr)


@app.route('/update_img', methods=['POST'])
@login_required
@no_admin_required
def update_img():
    image = request.files['image']
    
    if image.filename == '':
        # No file selected, keep the src variable as the default profile image
        src = url_for('static', filename='images/profile.png')
        return redirect(url_for('contact'))

    if current_user.has_role('donor'):
        # Get the Donor object for the current user
        data = Donor.query.filter_by(d_email_id=current_user.d_email_id).first()
        # print(data)
        if data:
            # Delete previous images with the same name but different extensions
            allowed_extensions = ['png', 'jpg', 'jpeg']
            for extension in allowed_extensions:
                image_path = f"/app/static/images/{data.donor_id}.{extension}"
                current_path = os.getcwd()
                filename = current_path + image_path
                if os.path.isfile(filename) == True:
                    os.remove(filename)

            # Generate a secure filename based on Donor_id and the file extension
            filename = f"{data.donor_id}{os.path.splitext(image.filename)[1]}"
            image_path = os.path.join("app/static/images", filename)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            # Save the uploaded image with the Donor_id as the filename
            image.save(image_path)

            return redirect(url_for('profile'))
        else:
            error_message = str("Plz fill the form first")
            return jsonify({'error': error_message})
    elif current_user.has_role('hospital'):
        imagefile = current_user.h_email_id.split('@')[0]
        allowed_extensions = ['png', 'jpg', 'jpeg']
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{imagefile}.{extension}"
            current_path = os.getcwd()
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                os.remove(filename)
                
        # Generate a secure filename based on Donor_id and the file extension
            filename = f"{imagefile}{os.path.splitext(image.filename)[1]}"
            image_path = os.path.join("app/static/images", filename)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            # Save the uploaded image with the Donor_id as the filename
            image.save(image_path)
            
            return redirect(url_for('profile'))       

#Home Page
@app.route('/appointment')
@login_required
@user_required
def appointment():
    src = "../static/images/profile.png"
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    full_name = user.name
    name_parts = full_name.split()
    initials = "".join([name[0] for name in name_parts])
    donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
    if donor:
        allowed_extensions = ['jpg', 'jpeg', 'png']
        # Check if an image file exists for the user
        current_path = os.getcwd() 
        for extension in allowed_extensions:
            image_path = f"/app/static/images/{donor.donor_id}.{extension}"
            filename = current_path + image_path
            if os.path.isfile(filename) == True:
                src = f"../static/images/{donor.donor_id}.{extension}"
        return render_template('Donor/form.html',data=donor, src = src,cities=cities)
    else:
        flash("Fill the Donor Information")
        return redirect(url_for('profile'))
    
@app.route('/booking',methods=['POST','GET'])
@login_required
@user_required
def booking():
    if request.method == 'POST':
        dat = request.form['date']
        dat = datetime.strptime(dat, '%Y-%m-%d').date()
        tim = request.form['time']
        tim = datetime.strptime(tim, '%H:%M').time()
        place = request.form['place']
        user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
        donor = Donor.query.filter_by(d_email_id=user.d_email_id).first()
        appoint = DonationAppointment(donor_id = donor.donor_id , appointment_date = dat,appointment_time= tim,place=place,ddone=False)
        if place.lower() not in [cit.lower() for cit in cities]:
            flash("No City Found")
            return redirect(url_for('appointment'))
        try:
            db.session.add(appoint)
            db.session.commit()
            flash("Appointment Done")
            return redirect(url_for('appointment'))
        except Exception as e:
            return redirect(url_for('contact'))
    else:
        return redirect(url_for('appointment'))
    
@app.route('/aperror')
def aperror():
    flash("Login first for an Appointment")
    return redirect(url_for('login'))

@app.route('/feedback',methods=['POST'])
@no_admin_required
def feedback():
    if request.method == 'POST':
        username = request.form['uname']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        current_date = date.today()

        feed_msg = ContactUS(username=username, email=email, mob=phone,feedback= message,date= current_date)
        try:
            db.session.add(feed_msg)
            db.session.commit()
            flash("Feedback sucessfully sent!!")
            return redirect(url_for('contact'))
        except Exception as e:
            return redirect(url_for('contact'))
    else:
        return redirect(url_for('contact'))
    
# Admin Page 

# @app.route('/plot')
# def plot_real_data():
#     return render_template('admin.html')

# from collections import defaultdict

@app.route('/plot_positive_data')
@admin_required
def plot_positive_data():
    # Get a list of all unique months
    unique_months = set(record.month for record in BloodDonationRecord.query.all())

    # Sort the months chronologically
    sorted_months = sorted(unique_months, key=lambda x: datetime.strptime(x, '%b-%y'))

    # Create a dictionary to store the blood flow data
    blood_flow_dict = {'months': list(sorted_months), 'Ap': [], 'Bp': [], 'ABp': [], 'Op': []}
    
    # Query the database and populate the dictionary
    for month in sorted_months:
        for blood_type in ['A+', 'B+', 'AB+', 'O+']:
            # Sum up the quantity for the given blood type and month
            total_quantity = (
                db.session.query(func.sum(BloodDonationRecord.quantity_donated))
                .filter(BloodDonationRecord.donation_type == blood_type)
                .filter(BloodDonationRecord.month == month)
                .scalar() or 0
            )
            blood_flow_dict[blood_type.replace('+', 'p')].append(total_quantity)

    return jsonify(blood_flow_dict)

@app.route('/plot_positive_data_out')
@admin_required
def plot_positive_data_out():
    # Get a list of all unique months
    unique_months = set(record.month for record in BloodTransfusionRecord.query.filter_by(status=1).all())

    # Sort the months chronologically
    sorted_months = sorted(unique_months, key=lambda x: datetime.strptime(x, '%b-%y'))

    # Create a dictionary to store the blood flow data
    blood_flow_dict = {'months': list(sorted_months), 'Ap': [], 'Bp': [], 'ABp': [], 'Op': []}
    
    # Query the database and populate the dictionary
    for month in sorted_months:
        for blood_type in ['A+', 'B+', 'AB+', 'O+']:
            # Sum up the quantity for the given blood type and month
            total_quantity = (
                db.session.query(func.sum(BloodTransfusionRecord.quantity_transfused))
                .filter(BloodTransfusionRecord.blood_type == blood_type)
                .filter(BloodTransfusionRecord.month == month)
                .filter(BloodTransfusionRecord.status == 1)
                .scalar() or 0
            )
            blood_flow_dict[blood_type.replace('+', 'p')].append(total_quantity)

    return jsonify(blood_flow_dict)

@app.route('/plot_negative_data')
@admin_required
def plot_negative_data():
    # Get a list of all unique months
    unique_months = set(record.month for record in BloodDonationRecord.query.all())

    # Sort the months chronologically
    sorted_months = sorted(unique_months, key=lambda x: datetime.strptime(x, '%b-%y'))

    # Create a dictionary to store the negative blood flow data
    negative_blood_flow_dict = {'months': list(sorted_months), 'An': [], 'Bn': [], 'ABn': [], 'On': []}
    
    # Query the database and populate the dictionary
    for month in sorted_months:
        for blood_type in ['A-', 'B-', 'AB-', 'O-']:
            # Sum up the quantity for the given negative blood type and month
            total_quantity = (
                db.session.query(func.sum(BloodDonationRecord.quantity_donated))
                .filter(BloodDonationRecord.donation_type == blood_type)
                .filter(BloodDonationRecord.month == month)
                .scalar() or 0
            )
            negative_blood_flow_dict[blood_type.replace('-', 'n')].append(total_quantity)

    return jsonify(negative_blood_flow_dict)

@app.route('/plot_negative_data_out')
@admin_required
def plot_negative_data_out():
    # Get a list of all unique months
    unique_months = set(record.month for record in BloodTransfusionRecord.query.filter_by(status = 1).all())

    # Sort the months chronologically
    sorted_months = sorted(unique_months, key=lambda x: datetime.strptime(x, '%b-%y'))

    # Create a dictionary to store the negative blood flow data
    negative_blood_flow_dict = {'months': list(sorted_months), 'An': [], 'Bn': [], 'ABn': [], 'On': []}
    
    # Query the database and populate the dictionary
    for month in sorted_months:
        for blood_type in ['A-', 'B-', 'AB-', 'O-']:
            # Sum up the quantity for the given negative blood type and month
            total_quantity = (
                db.session.query(func.sum(BloodTransfusionRecord.quantity_transfused))
                .filter(BloodTransfusionRecord.blood_type == blood_type)
                .filter(BloodTransfusionRecord.month == month)
                .filter(BloodTransfusionRecord.status == 1)
                .scalar() or 0
            )
            negative_blood_flow_dict[blood_type.replace('-', 'n')].append(total_quantity)

    return jsonify(negative_blood_flow_dict)



@app.route('/mark_notification_as_read')
@user_required
def mark_notifications_as_read():
    if current_user.has_role('donor'):
        user = current_user
        id_noti = Donor.query.filter_by(d_email_id=user.d_email_id).first().donor_id
        notifications = Notification.query.filter_by(donor_id=id_noti, read=False).all()

        for notification in notifications:
            notification.read = True

        db.session.commit()
    elif current_user.has_role('hospital'):
        notifications = HospitalNotification.query.filter_by(h_email_id=current_user.h_email_id, read=False).all()

        for notification in notifications:
            notification.read = True

        db.session.commit()
        
    return jsonify(True)

@app.route('/DRequests')
@login_required
@admin_required
def Drequests():
    current_day = datetime.now().date()
    ua = DonationAppointment.query.filter(DonationAppointment.appointment_date <= current_day).all()
    return render_template('Admin/Admin_DRequests.html',ua = ua)

@app.route('/HRequests')
@login_required
@admin_required
def HRequests():
    ua = BloodTransfusionRecord.query.filter().all()
    return render_template('Admin/Admin_HRequests.html',ua = ua,found=False,id=-1)

@app.route('/check/<int:transfusion_id>', methods=['GET'])
def check(transfusion_id):
    # Step 1: Retrieve details from BloodTransfusionRecord
    transfusion_record = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first()
    ua = BloodTransfusionRecord.query.filter().all()
    
    if transfusion_record:
        # Extract parameters from the transfusion record
        blood_type = transfusion_record.blood_type
        quantity_transfused = transfusion_record.quantity_transfused
        city1 = transfusion_record.city1
        city2 = transfusion_record.city2
        city3 = transfusion_record.city3

        # print(blood_type, quantity_transfused, city1, city2,city3)
        # Step 2: Search for an exact match
        exact_match = BloodInventory.query.filter_by(
            blood_type=blood_type,
            quantity_donated=quantity_transfused,
            storage_location=city1
        ).first()
        
        if exact_match:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = exact_match.quantity_donated
            transfusion_record.city1 = exact_match.storage_location
            try:
                db.session.delete(exact_match)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))

            


        # Step 3: Search for quantity >= quantity_transfused
        quantity_match = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated >= quantity_transfused,
            BloodInventory.storage_location == city1
        ).first()

        if quantity_match:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_match.quantity_donated
            transfusion_record.city1 = quantity_match.storage_location
            try:
                db.session.delete(quantity_match)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))


        # Step 4: Expand the search to include city2
        city2_match = BloodInventory.query.filter_by(
            blood_type = blood_type,
            quantity_donated = quantity_transfused,
            storage_location = city2
        ).first()

        if city2_match:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = city2_match.quantity_donated
            transfusion_record.city1 = city2_match.storage_location
            try:
                db.session.delete(city2_match)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))
            
        
        quantity_match_2 = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated >= quantity_transfused,
            BloodInventory.storage_location == city2
        ).first()

        if quantity_match_2:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_match_2.quantity_donated
            transfusion_record.city1 = quantity_match_2.storage_location
            try:
                db.session.delete(quantity_match_2)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))


        # Step 5: Expand the search to include city3
        city3_match = BloodInventory.query.filter_by(
            blood_type = blood_type,
            quantity_donated = quantity_transfused,
            storage_location = city3
        ).first()

        if city3_match:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = city3_match.quantity_donated
            transfusion_record.city1 = city3_match.storage_location
            try:
                db.session.delete(city3_match)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))
            
        
        quantity_match_3 = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated >= quantity_transfused,
            BloodInventory.storage_location == city3
        ).first()

        if quantity_match_3:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_match_3.quantity_donated
            transfusion_record.city1 = quantity_match_3.storage_location
            try:
                db.session.delete(quantity_match_3)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))


        
        # Step 6: Search for quantity <= quantity_transfused in city1
        quantity_less_match_city1 = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated <= quantity_transfused,
            BloodInventory.storage_location == city1
        ).first()

        if quantity_less_match_city1:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_less_match_city1.quantity_donated
            transfusion_record.city1 = quantity_less_match_city1.storage_location
            try:
                db.session.delete(quantity_less_match_city1)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))

        # Step 7: Search for quantity <= quantity_transfused in city2
        quantity_less_match_city2 = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated <= quantity_transfused,
            BloodInventory.storage_location == city2
        ).first()

        # print(quantity_less_match_city2)
        if quantity_less_match_city2:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_less_match_city2.quantity_donated
            transfusion_record.city1 = quantity_less_match_city2.storage_location
            try:
                db.session.delete(quantity_less_match_city2)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))


        # Step 8: Search for quantity <= quantity_transfused in city3
        quantity_less_match_city3 = BloodInventory.query.filter(
            BloodInventory.blood_type == blood_type,
            BloodInventory.quantity_donated <= quantity_transfused,
            BloodInventory.storage_location == city3
        ).first()

        if quantity_less_match_city3:
            transfusion_record.status = 1
            transfusion_record.quantity_transfused = quantity_less_match_city3.quantity_donated
            transfusion_record.city1 = quantity_less_match_city3.storage_location
            try:
                db.session.delete(quantity_less_match_city3)
                db.session.commit()
                
                re_id = BloodTransfusionRecord.query.filter_by(transfusion_id=transfusion_id).first().recipient_id
                h_email = Recipient.query.filter_by(recipient_id=re_id).first().h_email_id
                
                # Step 3: Create a notification for the hospital
                message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is Dispatched."
                hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id=h_email)
                
                try:
                    db.session.add(hospital_notification)
                    db.session.commit()

                    return render_template('Admin/Admin_HRequests.html', ua=ua, found=True, id=transfusion_id)
                except Exception as e:
                    return redirect(url_for('contact'))
            except Exception as e:
                return redirect(url_for('contect'))

        
        # Step 5: Return false if no match is found
        return render_template('Admin/Admin_HRequests.html',ua = ua,found=False,id=transfusion_id)


    return render_template('Admin/Admin_HRequests.html',ua = ua,found=False,id=-1)


@app.route('/delete_request/<int:transfusion_id>', methods=['GET'])
def delete_request(transfusion_id):
    # Step 1: Retrieve the transfusion record
    transfusion_record = BloodTransfusionRecord.query.filter_by(transfusion_id = transfusion_id).first()

    if transfusion_record:
        # Step 2: Update the status column
        transfusion_record.status = -1
        db.session.commit()
        
        re_id = BloodTransfusionRecord.filter_by(transfusion_id = transfusion_id).first().recipient_id
        h_email = Recipient.filter_by(recipient_id = re_id).first().h_email_id

        # Step 3: Create a notification for the hospital
        message = f"Blood request for recipient_id {transfusion_id} of blood_type {transfusion_record.blood_type} with quantity {transfusion_record.quantity_transfused} is not available. Please gather it from elsewhere."
        hospital_notification = HospitalNotification(transfusion_id=transfusion_id, message=message, read=False, h_email_id = h_email)
        db.session.add(hospital_notification)
        db.session.commit()

        # Step 4: Redirect to the original page
        return redirect(url_for('HRequests'))  # Replace 'original_page' with the actual route

    return redirect(url_for('contact'))


@app.route('/Client/<id>',methods=['POST','GET'])
@login_required
@admin_required
def Client(id):
    if id == 'donor':
        drs = Donor.query.all()
    elif id == 'hospital':
        drs = RHospital.query.all()
    elif id == 'recipient':
        drs = Recipient.query.all()
    else:
        return redirect(url_for('Admin'))
    return render_template('Admin/Admin_Client.html',drs=drs,id=id)

@app.route('/DAccepted', methods=['POST'])
@login_required
@admin_required
def DAccepted():
    # Fetching data from the form
    appointment_id = request.form.get('AID')
    collection_date_str = request.form.get('seD')
    quantity_donated = request.form.get('QD')

    # Convert 'collection_date' to a datetime object
    collection_date = datetime.strptime(collection_date_str, '%Y-%m-%d').date()

    # Fetch donor details using the current user
    donation_appointment = DonationAppointment.query.filter_by(appointment_id=appointment_id).first()
    donation_appointment.ddone = True
    donor = Donor.query.filter_by(donor_id=donation_appointment.donor_id).first()
    donor_id = donor.donor_id
    blood_type = donor.blood_type  # Fetch blood_type from the donor

    # Fetch storage_location from DonationAppointment using appointment_id
    storage_location = donation_appointment.place  

    # Calculate expiry date as collection date + 90 days
    expiry_date = collection_date + timedelta(days=90)

    # Create a BloodDonationRecord
    donation_record = BloodDonationRecord(
        appointment_id=appointment_id,
        collection_date=collection_date,
        donation_type=blood_type,  # Replace with the actual donation type
        quantity_donated=quantity_donated,
        storage_location=storage_location  # Fetch storage_location from DonationAppointment
    )

    # Create a BloodInventory
    blood_inventory = BloodInventory(
        blood_type=blood_type,  # Fetch blood_type from the donor
        donor_id=donor_id,
        collection_date=collection_date,
        expiry_date=expiry_date,
        quantity_donated=quantity_donated,
        storage_location=storage_location  # Fetch storage_location from DonationAppointment
    )
    
        # Calculate the month based on the collection_date
    donation_record.month = f"{donation_record.collection_date.strftime('%b')}-{donation_record.collection_date.strftime('%y')}"
    blood_inventory.month = f"{blood_inventory.collection_date.strftime('%b')}-{blood_inventory.collection_date.strftime('%y')}"

    # Add the records to the database
    db.session.add(donation_record)
    db.session.add(blood_inventory)
    db.session.commit()
    
    notification_message = f'You have successfully donated Blood on { collection_date } at {storage_location}'
    new_notification = Notification(donor_id=donor_id, appointment_id=appointment_id, message=notification_message,read=False)
    db.session.add(new_notification)
    db.session.commit()

    # Redirect to the 'about' page (replace 'about' with the actual route you want to redirect to)
    return redirect(url_for('Admin'))


# Hospital Page BackEnd starts

@app.route('/HRecipients',methods=['GET', 'POST'])
@login_required
@hos_required
def HRecipients():
    src = "../static/images/profile.png"
    
    allowed_extensions = ['jpg', 'jpeg', 'png']
    # Check if an image file exists for the user
    current_path = os.getcwd()
    for extension in allowed_extensions:
        image_path = f"/app/static/images/{current_user.h_email_id.split('@')[0]}.{extension}"
        filename = current_path + image_path
        if os.path.isfile(filename) == True:
            src = f"../static/images/{current_user.h_email_id.split('@')[0]}.{extension}"
    res = Recipient.query.filter_by(h_email_id=current_user.h_email_id).all()
        
    return render_template('Hospital/Hospital_Recipent.html',ress =res,src=src,user=current_user)

@app.route('/HRadd',methods=['POST'])
@login_required
@hos_required
def Hradd():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        DOB = request.form['DOB']
        DOB = datetime.strptime(DOB, '%Y-%m-%d').date()
        gender = request.form['gender']
        mob = request.form['mob']
        emailid = request.form['emailid']
        address = request.form['address']
        mhis = request.form['mhis']
        Btype = request.form['Btype']
        
        data = Recipient(h_email_id = current_user.h_email_id,first_name = fname,last_name = lname,date_of_birth = DOB,gender = gender,contact_phone = mob,contact_email = emailid,contact_address = address,blood_type = Btype,medical_history = mhis)
        
        try:
            db.session.add(data)
            db.session.commit()
        except Exception as e:
            print(e)
            redirect(url_for('contact'))
            
    return redirect(url_for('HRecipients'))
    

@app.route('/HProfile',methods=['GET', 'POST'])
@login_required
@hos_required
def HProfile():
    user = current_user
    src = "../static/images/profile.png"
    
    allowed_extensions = ['jpg', 'jpeg', 'png']
    # Check if an image file exists for the user
    current_path = os.getcwd()
    for extension in allowed_extensions:
        image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
        filename = current_path + image_path
        if os.path.isfile(filename) == True:
            src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"
            
    results = Recipient.query.filter_by(h_email_id=current_user.h_email_id).all()
    tf_ids = [results.recipient_id for results in results]
    
    fr = BloodTransfusionRecord.query.filter(BloodTransfusionRecord.recipient_id.in_(tf_ids)).all()
    
    if request.method == 'POST':
        address = request.form['address']
        data  = RHospital.query.filter_by(h_email_id=user.h_email_id).first()
        data.address = address
        
        try:
            db.session.add(data)
            db.session.commit()
            return redirect(url_for('HProfile'))
        except Exception as e:
            print(e)
            return redirect(url_for('contact'))
    return render_template('Hospital/Hospital_Profile.html',results=fr,user=user,cities=cities,src=src)

@app.route('/HAppointment')
@login_required
@hos_required
def HAppointment():
    user = current_user
    src = "../static/images/profile.png"
    current_date = datetime.now().strftime('%d-%m-%Y')
    allowed_extensions = ['jpg', 'jpeg', 'png']
    # Check if an image file exists for the user
    current_path = os.getcwd()
    for extension in allowed_extensions:
        image_path = f"/app/static/images/{user.h_email_id.split('@')[0]}.{extension}"
        filename = current_path + image_path
        if os.path.isfile(filename) == True:
            src = f"../static/images/{user.h_email_id.split('@')[0]}.{extension}"
    return render_template('Hospital/Hospital_form.html',cities=cities,src=src,user=user,cd=current_date)

# Assume the route to add data is '/add_transfusion_record'
@app.route('/getblood', methods=['POST'])
@login_required
@hos_required
def add_transfusion_record():
     # Extract data from the form
    recipient_id = request.form.get('recipient_id')
    transfusion_date = request.form.get('transfusion_date')
    transfusion_date = datetime.strptime(transfusion_date, '%d-%m-%Y').date()
    blood_type = request.form.get('blood_type')
    quantity_transfused = request.form.get('quantity_transfused')
    city1 = request.form.get('city1')
    city2 = request.form.get('city2')
    city3 = request.form.get('city3')

    print('transfusion_date')
    # Check if the recipient_id exists for the given h_email_id
    h_email_id = current_user.h_email_id  # Assuming you have a function to get the current user's h_email_id
    recipient_exists = Recipient.query.filter_by(recipient_id=recipient_id, h_email_id=h_email_id).first()

    if not recipient_exists:
        flash('Recipient ID not found for the current hospital.')
        return redirect(url_for('HAppointment'))

    # Create a new BloodTransfusionRecord instance
    new_transfusion_record = BloodTransfusionRecord(
        recipient_id=recipient_id,
        transfusion_date=transfusion_date,
        blood_type=blood_type,
        quantity_transfused=quantity_transfused,
        city1=city1,
        city2=city2,
        city3=city3
    )
    
    new_transfusion_record.month = f"{new_transfusion_record.transfusion_date.strftime('%b')}-{new_transfusion_record.transfusion_date.strftime('%y')}"
    

    # Add the new record to the database
    db.session.add(new_transfusion_record)
    db.session.commit()

    # Redirect to the desired page (you can customize this)
    return redirect(url_for('HAppointment'))


# Hospital Page BackEnd ends