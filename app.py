from flask import Flask, render_template, redirect, url_for, request, flash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps

from models import db, Patient, Doctor, Appointment, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///clinic.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    migrate = Migrate(app, db)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    def role_required(role):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not current_user.is_authenticated or current_user.role != role:
                    flash('غير مصرح بالوصول لهذه الصفحة')
                    return redirect(url_for('login'))
                return f(*args, **kwargs)
            return wrapped
        return decorator

    @app.route('/')
    def index():
        # إذا المستخدم مسجل دخول نوجّه لصفحة المرضى وإلا نعرض الصفحة الرئيسية
        if current_user.is_authenticated:
            return redirect(url_for('patients_list'))
        return render_template('index.html')

    # Authentication
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('تم تسجيل الدخول بنجاح')
                return redirect(request.args.get('next') or url_for('index'))
            flash('اسم المستخدم أو كلمة المرور غير صحيح')
        return render_template('auth/login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('تم تسجيل الخروج')
        return redirect(url_for('index'))

    # Patients
    @app.route('/patients')
    @login_required
    def patients_list():
        patients = Patient.query.order_by(Patient.id.desc()).all()
        return render_template('patients/list.html', patients=patients)

    @app.route('/patients/new', methods=['GET', 'POST'])
    @login_required
    def patients_new():
        if request.method == 'POST':
            name = request.form.get('full_name')
            phone = request.form.get('phone')
            dob = request.form.get('dob') or None
            notes = request.form.get('notes')
            p = Patient(full_name=name, phone=phone, dob=dob, notes=notes)
            db.session.add(p)
            db.session.commit()
            flash('تم إضافة المريض بنجاح')
            return redirect(url_for('patients_list'))
        return render_template('patients/form.html', patient=None)

    @app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
    @login_required
    def patients_edit(patient_id):
        patient = Patient.query.get_or_404(patient_id)
        if request.method == 'POST':
            patient.full_name = request.form.get('full_name')
            patient.phone = request.form.get('phone')
            patient.dob = request.form.get('dob') or None
            patient.notes = request.form.get('notes')
            db.session.commit()
            flash('تم تحديث بيانات المريض')
            return redirect(url_for('patients_list'))
        return render_template('patients/form.html', patient=patient)

    # Doctors
    @app.route('/doctors')
    @login_required
    def doctors_list():
        doctors = Doctor.query.order_by(Doctor.id.desc()).all()
        return render_template('doctors/list.html', doctors=doctors)

    # Appointments
    @app.route('/appointments')
    @login_required
    def appointments_list():
        appointments = Appointment.query.order_by(Appointment.start_datetime.desc()).all()
        return render_template('appointments/list.html', appointments=appointments)

    @app.route('/appointments/new', methods=['GET','POST'])
    @login_required
    def appointments_new():
        doctors = Doctor.query.all()
        patients = Patient.query.all()
        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            doctor_id = request.form.get('doctor_id')
            start = request.form.get('start_datetime')
            end = request.form.get('end_datetime') or start
            reason = request.form.get('reason')
            ap = Appointment(patient_id=patient_id, doctor_id=doctor_id, start_datetime=start, end_datetime=end, reason=reason)
            db.session.add(ap)
            db.session.commit()
            flash('تم إضافة الموعد')
            return redirect(url_for('appointments_list'))
        return render_template('appointments/form.html', doctors=doctors, patients=patients)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
