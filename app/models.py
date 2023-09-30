from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class RDonor(UserMixin, db.Model):
    d_email_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.d_email_id  # Return a unique identifier for the user

class RHospital(UserMixin, db.Model):
    h_email_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    contact_phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return self.h_email_id  # Return a unique identifier for the user

class Donor(UserMixin,db.Model):
    donor_id = db.Column(db.Integer, primary_key=True)
    d_email_id = db.Column(db.String(120), db.ForeignKey('r_donor.d_email_id'))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.String(15))
    contact_email = db.Column(db.String(120))
    contact_address = db.Column(db.String(200))
    blood_type = db.Column(db.String(5), nullable=False)
    donor_status = db.Column(db.String(20), nullable=False)

    r_donor = db.relationship("RDonor", backref="donors")
    
class Recipient(UserMixin,db.Model):
    recipient_id = db.Column(db.Integer, primary_key=True)
    h_email_id = db.Column(db.String(120), db.ForeignKey('r_hospital.h_email_id'))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.String(15))
    contact_email = db.Column(db.String(120))
    contact_address = db.Column(db.String(200))
    blood_type = db.Column(db.String(5), nullable=False)
    medical_history = db.Column(db.Text)
    doctor_prescription = db.Column(db.Text)

    r_hospital = db.relationship("RHospital", backref="hospitals")

class DonationAppointment(UserMixin,db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False)

    donor = db.relationship('Donor', backref='appointments')

class BloodDonationRecord(UserMixin,db.Model):
    donation_id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'), nullable=False)
    collection_date = db.Column(db.Date, nullable=False)
    donation_type = db.Column(db.String(20), nullable=False)
    quantity_donated = db.Column(db.Float, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))

    donor = db.relationship('Donor', backref='donation_records')
    staff = db.relationship('Staff', backref='donation_records')

class BloodInventory(UserMixin,db.Model):
    blood_id = db.Column(db.Integer, primary_key=True)
    blood_type = db.Column(db.String(5), nullable=False)
    blood_component = db.Column(db.String(20), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.donor_id'))
    collection_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    blood_bag_number = db.Column(db.String(20))
    storage_location = db.Column(db.String(100), nullable=False)

class BloodTransfusionRecord(UserMixin,db.Model):
    transfusion_id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.recipient_id'), nullable=False)
    transfusion_date = db.Column(db.Date, nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    blood_component = db.Column(db.String(20))
    quantity_transfused = db.Column(db.Float, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))

    recipient = db.relationship('Recipient', backref='transfusion_records')
    staff = db.relationship('Staff', backref='transfusion_records')

class Staff(UserMixin,db.Model):
    staff_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    contact_phone = db.Column(db.String(15))
    contact_email = db.Column(db.String(120))
    contact_address = db.Column(db.String(200))
    position = db.Column(db.String(20), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)