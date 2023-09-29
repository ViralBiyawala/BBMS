from flask import Flask, render_template, send_file
from app import app, db
from app.models import *
import pdfkit, shutil

#Route to Register Page
@app.route('/register')
def register():
    return render_template('register.html')

# @app.route('/home')
# def home():
#     return render_template('home.html')

#Route to Contact Page
@app.route('/contact')
def home():
    return render_template('contact.html')

#Route to Login Page
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/confirm')
def confirm():
    return render_template('confirm.html')

# @app.route('/')
# def base():
#     return render_template('base.html')

# generating basic template for certficate
@app.route('/certificate', methods=['GET'])
def verify():
    return render_template('certificate.html',name=('Life Saver Blood Donor',"DD-MM-YYYY","City"))


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