from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    make_response,
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
from datetime import datetime, timedelta
from app import app,myemail,server,app_login_key
import pdfkit, shutil, re, random
from email.mime.text import MIMEText
# ids = 1

#initialization
# Store OTPs for email verification with their creation time
otp_storage = {}

# Define the OTP timeout duration in seconds (100 seconds in this case)
OTP_TIMEOUT = 240

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


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
def contact():
    return render_template('contact.html')

#By default Page
@app.route('/')
def index():
    user = current_user if current_user.is_authenticated else None
    if user == None:
        initials = None
    else:
        full_name = user.name
        name_parts = full_name.split()
        initials = "".join([name[0] for name in name_parts])
    return render_template('index.html',user=user, name=initials)

#Home Page
@app.route('/index')
def base():
    user = current_user if current_user.is_authenticated else None
    if user == None:
        initials = None
    else:
        full_name = user.name
        name_parts = full_name.split()
        initials = "".join([name[0] for name in name_parts])
    return render_template('index.html',user=user, name=initials)

# generating basic template for certficate
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
        # flash('OTP Sent.Valid for 4 minutes.')
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
    # flash("")
    if request.method == 'POST':
        email = request.form.get('email')
        user_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])  # Concatenate OTP digits
        name = request.form.get('name')
        city = request.form.get('city')
        mobile_no = request.form.get('mobile_no')
        password = request.form.get('password')
        admin_type = request.form.get('admin')

        # if user_otp == None:
        #     return render_template('otp.html')
        print(user_otp)   
        stored_data = otp_storage.get(email)
        # print(stored_data)
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
        else:
            flash('Wrong OTP!!!')                
            return render_template('otp.html')
        # flash('Wrong OTP!!!')                
        return render_template('otp.html')

# Paasword update in Database
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

        # Check if the user_id is for an RHospital
        hospital = RHospital.query.get(email)
        if hospital:
            admin_type = "hospital"

        stored_data = otp_storage.get(email)
        # print(stored_data)
        if stored_data and user_otp == stored_data['otp']:
            # Check if the OTP is still valid
            created_at = stored_data['created_at']
            if datetime.now() - created_at <= timedelta(seconds=OTP_TIMEOUT):
                # Check the user type and create the appropriate object
                if admin_type == 'donor':
                    # Create an RDonor object and populate it
                    new_user = RDonor.query.get(email)
                    new_user.set_password(password)  # Set the password using set_password method
                elif admin_type == 'hospital':
                    # Create an RHospital object and populate it
                    new_user = RHospital.query.get(email)
                    new_user.set_password(password)  # Set the password using set_password method
                
                # Add the new user to the appropriate table in the database
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect(url_for('login'))
                except Exception as e:
                    print(e)
                    return redirect(url_for('contact'))
                        
        return render_template('forget_otp.html')

#Certificate
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
        
        if user is not None and user.check_password(password):  # Check the password using check_password method
            # Log in the user using Flask-Login
            login_user(user)
            return redirect(url_for('index'))  # Change 'index' to the desired page
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))  # Change 'home' to the desired page
    
    return render_template('login.html')

# Profile Page
@app.route('/profile', methods=['GET', 'POST'])
@login_required
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
    if data is None:
        return render_template('profile.html', email=current_user, data=None)
    else:
        return render_template('profile.html', email=current_user, data=data)
