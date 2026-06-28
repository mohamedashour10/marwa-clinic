from flask import Flask, render_template, redirect, url_for, request, flash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps

from models import db, Patient, Doctor, Appointment, User
from forms import LoginForm, UserForm, PatientForm, AppointmentForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


def parse_dt(s):
    # Expecting format: YYYY-MM-DD HH:MM
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        return None


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

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('patients_list'))
        return render_template('index.html')

    # Authentication
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                flash('تم تسجيل الدخول بنجاح')
                return redirect(request.args.get('next') or url_for('index'))
            flash('اسم المستخدم أو كلمة المرور غير صحيح')
        return render_template('auth/login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('تم تسجيل الخروج')
        return redirect(url_for('index'))

    # Admin: Users management
    @app.route('/admin/users')
    @login_required
    @role_required('admin')
    def admin_users():
        users = User.query.order_by(User.id.desc()).all()
        return render_template('admin/users.html', users=users)

    @app.route('/admin/users/new', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def admin_users_new():
        form = UserForm()
        if form.validate_on_submit():
            u = User(username=form.username.data, role=form.role.data)
            if form.password.data:
                u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
            flash('تم إضافة المستخدم')
            return redirect(url_for('admin_users'))
        return render_template('admin/user_form.html', form=form, user=None)

    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def admin_users_edit(user_id):
        user = User.query.get_or_404(user_id)
        form = UserForm(obj=user)
        if form.validate_on_submit():
            user.username = form.username.data
            user.role = form.role.data
            if form.password.data:
                user.set_password(form.password.data)
            db.session.commit()
            flash('تم تحديث المستخدم')
            return redirect(url_for('admin_users'))
        return render_template('admin/user_form.html', form=form, user=user)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @role_required('admin')
    def admin_users_delete(user_id):
        user = User.query.get_or_404(user_id)
        if user.username == 'admin':
            flash('لا يمكن حذف المستخدم الافتراضي')
            return redirect(url_for('admin_users'))
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم')
        return redirect(url_for('admin_users'))

    # Patients
    @app.route('/patients')
    @login_required
    def patients_list():
        patients = Patient.query.order_by(Patient.id.desc()).all()
        return render_template('patients/list.html', patients=patients)

    @app.route('/patients/new', methods=['GET', 'POST'])
    @login_required
    def patients_new():
        form = PatientForm()
        if form.validate_on_submit():
            dob = None
            if form.dob.data:
                try:
                    dob = datetime.strptime(form.dob.data, '%Y-%m-%d').date()
                except Exception:
                    dob = None
            p = Patient(full_name=form.full_name.data, phone=form.phone.data, dob=dob, notes=form.notes.data)
            db.session.add(p)
            db.session.commit()
            flash('تم إضافة المريض بنجاح')
            return redirect(url_for('patients_list'))
        return render_template('patients/form.html', form=form, patient=None)

    @app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
    @login_required
    def patients_edit(patient_id):
        patient = Patient.query.get_or_404(patient_id)
        form = PatientForm(obj=patient)
        if form.validate_on_submit():
            patient.full_name = form.full_name.data
            patient.phone = form.phone.data
            if form.dob.data:
                try:
                    patient.dob = datetime.strptime(form.dob.data, '%Y-%m-%d').date()
                except Exception:
                    pass
            patient.notes = form.notes.data
            db.session.commit()
            flash('تم تحديث بيانات المريض')
            return redirect(url_for('patients_list'))
        return render_template('patients/form.html', form=form, patient=patient)

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
        form = AppointmentForm()
        form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name).all()]
        form.doctor_id.choices = [(d.id, d.name) for d in Doctor.query.order_by(Doctor.name).all()]
        if form.validate_on_submit():
            start = parse_dt(form.start_datetime.data)
            end = parse_dt(form.end_datetime.data) if form.end_datetime.data else start
            if not start:
                flash('صيغة التاريخ/الوقت غير صحيحة، الرجاء استخدام YYYY-MM-DD HH:MM')
                return render_template('appointments/form.html', form=form)
            # conflict check: same doctor, overlapping times
            conflict = Appointment.query.filter(
                Appointment.doctor_id == form.doctor_id.data,
                Appointment.start_datetime < end,
                Appointment.end_datetime > start
            ).first()
            if conflict:
                flash('يوجد موعد متداخل لنفس الطبيب في هذا التوقيت')
                return render_template('appointments/form.html', form=form)
            ap = Appointment(patient_id=form.patient_id.data, doctor_id=form.doctor_id.data, start_datetime=start, end_datetime=end, reason=form.reason.data)
            db.session.add(ap)
            db.session.commit()
            flash('تم إضافة الموعد')
            return redirect(url_for('appointments_list'))
        return render_template('appointments/form.html', form=form)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
