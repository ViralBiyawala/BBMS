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
from flask_mail import Message
from app.models import *
from datetime import datetime, timedelta, date
import os
from app import app,myemail,server,app_login_key,mypass
import re, random
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from sqlalchemy import desc,func
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
        if current_user.is_authenticated and current_user.has_role('admin'):
            return f(*args, **kwargs)
        else:
            flash('Admin only have permission for this Page.')
            return redirect(url_for('index'))
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if not current_user.has_role('admin'):
                return f(*args, **kwargs)
            else:
                flash('Donor only permission for this Page.')
                return redirect(url_for('Admin'))
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route('/Admin',methods=['POST','GET'])
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
        
        # Create a list to store the summarized data
    sd_city = {}
    
    # Query the database to find appointment IDs where city == selected_city
    appointment_ids = (
        DonationAppointment.query
        .filter(DonationAppointment.place == selected_city)
        .with_entities(DonationAppointment.appointment_id)
        .all()
    )
    if sb == 'ALL' :
        # Query the database to group by blood type and sum up quantities
        for blood_type in blood_types:
                total_quantity = 0

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

                sd_city[blood_type] = total_quantity
    
    else :
        total_quantity = 0
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
        sd_city[sb] = total_quantity
    

    return render_template('Admin_Home.html',cities=cities,in_qu=summarized_data,sd_city=sd_city,sc=selected_city,sb=sb)

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
@user_required
@app.route('/contact')
def contact():
    src = "../static/images/profile.png"
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin') else None
    if user != None:
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
    return render_template('contact.html',src=src,user=user)

# @app.route('/form')
# def donor_form():
#     return render_template('form.html',cities=cities)

@app.route('/about')
def about():
    src = "../static/images/profile.png"
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    if user != None:
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
    return render_template('AboutUs.html',src=src,user=user)

#By default Page
@app.route('/')
@user_required
def base():
    src = "../static/images/profile.png"
    notifications = None
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    if user == None:
        initials = None
    else:
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
        
        notifications = Notification.query.filter_by(donor_id=id_noti).all()
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
        else :
            flash("Fill Donor Information First")
            return redirect(url_for('profile'))
    return render_template('index.html',user=user, name=initials, src = src, notifications = notifications)

#Home Page
@app.route('/index')
@user_required
def index():
    src = "../static/images/profile.png"
    notifications = None
    user = current_user if current_user.is_authenticated and not current_user.has_role('admin')  else None
    if user == None:
        initials = None
    else:
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
        
        notifications = Notification.query.filter_by(donor_id=id_noti).all()
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
        else :
            flash("Fill Donor Information First")
            return redirect(url_for('profile'))
    return render_template('index.html',user=user, name=initials, src = src, notifications = notifications)

# generating basic template for certficate
@login_required
@user_required
@app.route('/certificate', methods=['GET'])
def verify():
    return render_template('certificate.html',name=('Life Saver Blood Donor',"DD-MM-YYYY","City"))

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
@app.route('/gc/<appointment_id>')
def gc(appointment_id):
    user = current_user
    # html_template = render_template('certificate.html', name=name)
    results = DonationAppointment.query.filter_by(appointment_id=appointment_id).first()
    data = Donor.query.filter_by(d_email_id=user.d_email_id).first()
    name = data.first_name + " " + data.middle_name + " " + data.last_name
    html_template = render_template('certificate.html', name=(name,results.appointment_date, results.place))

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
        
        if user is not None and user.check_password(password):  # Check the password using check_password method
            login_user(user)
            return redirect(url_for('index'))  # Change 'index' to the desired page
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))  # Change 'home' to the desired page
    
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
            print(data.gender)
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
            print(data.gender)
            return redirect(url_for('profile'))
        except Exception as e:
            print(e)
            return redirect(url_for('contact'))

    data = Donor.query.filter_by(d_email_id=current_user.d_email_id).first()
    results = None
    # print(data.gender)
    if data is None:
        src = "../static/images/profile.png"
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
    return render_template('profile.html', email=current_user, data=data,  src = src, results = results, cities=cities,fr = fr)


@app.route('/update_img', methods=['POST'])
@login_required
def update_img():
    image = request.files['image']
    
    if image.filename == '':
        # No file selected, keep the src variable as the default profile image
        src = url_for('static', filename='images/profile.png')
        return redirect(url_for('contact'))

    # Get the Donor object for the current user
    data = Donor.query.filter_by(d_email_id=current_user.d_email_id).first()
    print(data)
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
        
        # Update the src variable to the new image path
        src = image_path

        return redirect(url_for('profile'))
    else:
        error_message = str("Plz fill the form first")
        # flash(error_message, 'error')
        return jsonify({'error': error_message})

#Home Page
@app.route('/appointment')
@login_required
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
        return render_template('form.html',data=donor, src = src,cities=cities)
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
            # print(data.gender)
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
def plot_positive_data():
    # Get a list of all unique dates
    unique_dates = set(record.collection_date.strftime('%Y-%m-%d') for record in BloodDonationRecord.query.all())

    # Create a dictionary to store the positive blood data
    positive_data_dict = {'dates': list(unique_dates), 'Ap': [], 'Bp': [], 'ABp': [], 'Op': []}
    
    # Query the database and populate the dictionary
    for date in unique_dates:
        for blood_type in ['A+', 'B+', 'AB+', 'O+']:
            # Find the corresponding record or set quantity to 0
            record = (
                BloodDonationRecord.query
                .filter(BloodDonationRecord.donation_type == blood_type)
                .filter(BloodDonationRecord.collection_date == date)
                .first()
            )
            quantity = record.quantity_donated if record else 0
            positive_data_dict[blood_type.replace('+', 'p')].append(quantity)

    # Sort the data by 'dates'
    sorted_data = {'dates': sorted(positive_data_dict['dates']), 'Ap': [], 'Bp': [], 'ABp': [], 'Op': []}
    for blood_type in ['A+', 'B+', 'AB+', 'O+']:
        sorted_data[blood_type.replace('+', 'p')] = [positive_data_dict[blood_type.replace('+', 'p')][positive_data_dict['dates'].index(date)] for date in sorted_data['dates']]

    return jsonify(sorted_data)


@app.route('/plot_negative_data')
def plot_negative_data():
    # Get a list of all unique dates
    unique_dates = set(record.collection_date.strftime('%Y-%m-%d') for record in BloodDonationRecord.query.all())

    # Create a dictionary to store the negative blood data
    negative_data_dict = {'dates': list(unique_dates), 'An': [], 'Bn': [], 'ABn': [], 'On': []}

    # Query the database and populate the dictionary
    for date in unique_dates:
        for blood_type in ['A-', 'B-', 'AB-', 'O-']:
            # Find the corresponding record or set quantity to 0
            record = (
                BloodDonationRecord.query
                .filter(BloodDonationRecord.donation_type == blood_type)
                .filter(BloodDonationRecord.collection_date == date)
                .first()
            )
            quantity = record.quantity_donated if record else 0
            negative_data_dict[blood_type.replace('-', 'n')].append(quantity)

    # Sort the data by 'dates'
    sorted_data = {'dates': sorted(negative_data_dict['dates']), 'An': [], 'Bn': [], 'ABn': [], 'On': []}
    for blood_type in ['A-', 'B-', 'AB-', 'O-']:
        sorted_data[blood_type.replace('-', 'n')] = [negative_data_dict[blood_type.replace('-', 'n')][negative_data_dict['dates'].index(date)] for date in sorted_data['dates']]

    return jsonify(sorted_data)


@app.route('/mark_notification_as_read')
def mark_notifications_as_read():
    user = current_user
    id_noti = Donor.query.filter_by(d_email_id=user.d_email_id).first().donor_id
    notifications = Notification.query.filter_by(donor_id=id_noti, read=False).all()

    for notification in notifications:
        notification.read = True

    db.session.commit()

    return jsonify(True)

@login_required
@admin_required
@app.route('/DRequests')
def Drequests():
    current_day = datetime.now().date()
    ua = DonationAppointment.query.filter(DonationAppointment.appointment_date <= current_day).all()
    return render_template('Admin_DRequests.html',ua = ua)


@app.route('/Client')
def Client():
    return render_template('Admin_Client.html')

@login_required
@admin_required
@app.route('/DAccepted', methods=['POST'])
def DAccepted():
    # Fetching data from the form
    appointment_id = request.form.get('AID')
    collection_date_str = request.form.get('seD')
    quantity_donated = request.form.get('QD')
    blood_bag_number = request.form.get('BBN')

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
        blood_bag_number=blood_bag_number,
        storage_location=storage_location  # Fetch storage_location from DonationAppointment
    )

    # Create a BloodInventory
    blood_inventory = BloodInventory(
        blood_type=blood_type,  # Fetch blood_type from the donor
        donor_id=donor_id,
        collection_date=collection_date,
        expiry_date=expiry_date,
        quantity_donated=quantity_donated,
        blood_bag_number=blood_bag_number,
        storage_location=storage_location  # Fetch storage_location from DonationAppointment
    )

    # Add the records to the database
    db.session.add(donation_record)
    db.session.add(blood_inventory)
    db.session.commit()

    # Redirect to the 'about' page (replace 'about' with the actual route you want to redirect to)
    return redirect(url_for('Admin'))