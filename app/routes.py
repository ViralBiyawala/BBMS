from flask import render_template, request, flash, redirect, url_for, send_file, make_response
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_mail import Message
from app.models import *
import random  # Import the random module
from datetime import datetime, timedelta  # Import datetime and timedelta
from app import app
import pdfkit, os, smtplib
import shutil
from email.mime.text import MIMEText

import re


myemail = 'svspbs567@gmail.com'
smtp_server = 'smtp.gmail.com'
smtp_port = 587

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()


# Store OTPs for email verification with their creation time
otp_storage = {}

# Define the OTP timeout duration in seconds (100 seconds in this case)
OTP_TIMEOUT = 180

def is_valid_email(email):
    # Regular expression for basic email validation
    email_regex = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
    return re.match(email_regex, email)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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

    # If the user_id doesn't match either type, return None
    return None

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
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('register'))
        
        
        # Check if the email is already registered
        existing_user = RDonor.query.filter_by(d_email_id=email).first()
        existing_user_H = RHospital.query.filter_by(d_email_id=email).first()
        if existing_user or existing_user_H:
            flash('Email is already registered. Please use a different email address.', 'error')
            return redirect(url_for('register'))

        # Generate a 6-digit random OTP
        otp = str(random.randint(100000, 999999))
        
        # Store OTP and its creation time
        otp_storage[email] = {
            'otp': otp,
            'created_at': datetime.now()
        }
        
        # old_otp = otp_storage.get(email)
        # if old_otp:
        #     del otp_storage[email]
        # print(stored_data)
        
        # Send OTP email
        msg = MIMEText(f'Your OTP for email verification: {otp}')
        msg['Subject'] = 'Mail for Email Verification'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.login(myemail, 'edfouebuiwfvwdrr')
        server.send_message(msg)
        # server.quit()
        
        # Render the OTP verification page and pass us*-er data along with the email
        return render_template('otp.html', email=email, name=name, city=city, mobile_no=mobile_no, password=password, admin_type=admin_type)

    
    return render_template('register.html')

# New route for OTP verification
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
        if stored_data and user_otp == stored_data['otp']:
            # Check if the OTP is still valid
            created_at = stored_data['created_at']
            print(email,user_otp,name,city,mobile_no,password,admin_type)
            if datetime.now() - created_at <= timedelta(seconds=OTP_TIMEOUT):
                # Check the user type and create the appropriate object
                if admin_type == 'donor':
                    # Create an RDonor object and populate it
                    new_user = RDonor(d_email_id=email, name=name, city=city, contact_phone=mobile_no)
                    new_user.set_password(password)  # Set the password using set_password method
                elif admin_type == 'hospital':
                    # Create an RHospital object and populate it
                    new_user = RHospital(h_email_id=email, name=name, city=city, contact_phone=mobile_no)
                    new_user.set_password(password)  # Set the password using set_password method
                
                # Add the new user to the appropriate table in the database
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect(url_for('login'))
                except Exception as e:
                    print(e)
                    return redirect(url_for('contact'))
                        
        return "Invalid OTP. Please try again."


#Route to Login Page
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
        
        if user is not None and user.check_password(password):  # Check the password using check_password method
            # Log in the user using Flask-Login
            login_user(user)
            # Redirect to a protected page or perform other actions
            # For example, you can redirect to a dashboard or home page
            return redirect(url_for('contact'))  # Change 'home' to the desired page
        else:
            # flash('Invalid username or password. Please try again.')
            return redirect(url_for('register'))  # Change 'home' to the desired page
    
    return render_template('login.html')


# @app.route('/otp')
# def otp():
#     return render_template('otp.html')

#Route to Contact Page
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/otp')
def otp():
    return render_template('otp.html')


# generating basic template for certficate
@app.route('/certificate', methods=['GET'])
def verify():
    return render_template('certificate.html',name=('Life Saver Blood Donor',"DD-MM-YYYY","City"))

# @app.route('/hello')
# def tp():
#     return render_template('certificate.html',name=('Life Saver Blood Donor',"DD-MM-YYYY","City"))


#Route to Download Certificate Page
@app.route('/gc/<name>')
def generate_certificate(name):
    # html_template = render_template('certificate.html', name=name)
    html_template = render_template('certificate.html', name=(name,"10-1-2021", "Surat"))

    # Save the HTML content to a file with a specific name
    # html_file_name = f"app/templates/certificate{name}.html"
    with open("app/templates/certificate.html", 'w') as html_file:
        html_file.write(html_template)

    pdfkit.from_url("http://127.0.0.1:5000/certificate","app/templates/output.pdf")
    # os.remove(html_file_name)
    temp = str(name) + ".pdf"
    source_file = 'app/templates/certificate.html'

    # Destination file path (where you want to copy the HTML file)
    destination_file = 'app/templates/temp.html'

    # Copy the source HTML file to the destination
    shutil.copyfile(destination_file,source_file)
    return send_file("templates\\output.pdf",download_name=temp,as_attachment=False)


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

        otp = otp_storage[email]
        
        # Send OTP email
        msg = MIMEText(f'Your OTP for email verification: {otp}')
        msg['Subject'] = 'Mail for Email Verification'
        msg['From'] = " Life Saver Blood"
        msg['To'] = email
        server.login(myemail, 'edfouebuiwfvwdrr')
        server.send_message(msg)
        # server.quit()
        
        # Render the OTP verification page and pass us*-er data along with the email
        return render_template('otp.html', email=email, name=name, city=city, mobile_no=mobile_no, password=password, admin_type=admin_type)

    
    return render_template('register.html')