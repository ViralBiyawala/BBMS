from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# from sqlalchemy import func

class RDonor(UserMixin, db.Model):
    d_email_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    roles = ['donor']
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.d_email_id  # Return a unique identifier for the user
    
    def has_role(self, role):
        return role in self.roles


class RHospital(UserMixin, db.Model):
    h_email_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(1024), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    roles = ['hospital']
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.h_email_id  # Return a unique identifier for the user
    
    def has_role(self, role):
        return role in self.roles

class Donor(UserMixin,db.Model):
    donor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    d_email_id = db.Column(db.String(120), db.ForeignKey('r_donor.d_email_id'))
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.Integer, nullable=False)
    contact_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(20), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)

    r_donor = db.relationship("RDonor", backref="donors")
    
class Recipient(UserMixin,db.Model):
    recipient_id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    h_email_id = db.Column(db.String(120), db.ForeignKey('r_hospital.h_email_id'))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.String(15))
    contact_email = db.Column(db.String(120))
    contact_address = db.Column(db.String(200))
    blood_type = db.Column(db.String(5), nullable=False)
    medical_history = db.Column(db.Text,nullable=True)

    r_hospital = db.relationship("RHospital", backref="hospitals")

class DonationAppointment(UserMixin,db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    place = db.Column(db.String(20), nullable=False)
    ddone = db.Column(db.Boolean, default=False)
    
    donor = db.relationship('Donor', backref='appointments')

class BloodDonationRecord(UserMixin,db.Model):
    blood_bag_number = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('donation_appointment.appointment_id'))
    collection_date = db.Column(db.Date, nullable=False)
    donation_type = db.Column(db.String(20), nullable=False)
    quantity_donated = db.Column(db.Float, nullable=False)
    storage_location = db.Column(db.String(100), nullable=False)
    month = db.Column(db.String(10))  
    
    donation_appointment = db.relationship('DonationAppointment', backref='donation_records')

class BloodInventory(UserMixin,db.Model):
    blood_bag_number = db.Column(db.Integer, primary_key=True, autoincrement=True)
    blood_type = db.Column(db.String(5), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'))
    collection_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity_donated = db.Column(db.Float, nullable=False)
    storage_location = db.Column(db.String(100), nullable=False)
    month = db.Column(db.String(10))  # New column for storing month-year

    donor = db.relationship('Donor', backref='inventory')

class BloodTransfusionRecord(UserMixin,db.Model):
    transfusion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.recipient_id'), nullable=False)
    transfusion_date = db.Column(db.Date, nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    quantity_transfused = db.Column(db.Float, nullable=False)
    city1 = db.Column(db.String(100), nullable=False)
    city2 = db.Column(db.String(100), nullable=False)
    city3 = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Integer, default=0)
    month = db.Column(db.String(10))  # New column for storing month-year
    
    recipient = db.relationship('Recipient', backref='transfusion_records')
    
class ContactUS(UserMixin,db.Model):
    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    mob = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.String(1000), nullable=False)
    
class AdminUser(UserMixin,db.Model):
    username = db.Column(db.String(50),primary_key=True,nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    roles = ['admin']
    
    def get_id(self):
        return self.username  
    
    def has_role(self, role):
        return role in self.roles

class Notification(db.Model):
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'), primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('donation_appointment.appointment_id'), primary_key=True)
    message = db.Column(db.String(1024), nullable=False, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    read = db.Column(db.Boolean, default=False)

    donor = db.relationship('Donor', backref='notifications')
    appointment = db.relationship('DonationAppointment', backref='notifications')

    def __init__(self, donor_id, appointment_id, message,read):
        self.donor_id = donor_id
        self.appointment_id = appointment_id
        self.message = message
        self.read = read
        
class HospitalNotification(db.Model):
    transfusion_id = db.Column(db.Integer, db.ForeignKey('blood_transfusion_record.transfusion_id'), primary_key=True)
    message = db.Column(db.String(1024), nullable=False, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    read = db.Column(db.Boolean, default=False)
    h_email_id = db.Column(db.String(120),nullable=False)

    blood_info = db.relationship('BloodTransfusionRecord', backref='hospitialnotifications')

    def __init__(self, transfusion_id, message,read,h_email_id):
        self.transfusion_id = transfusion_id
        self.message = message
        self.read = read
        self.h_email_id = h_email_id
