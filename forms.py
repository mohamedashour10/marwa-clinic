from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=3)])

class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('كلمة المرور', validators=[Optional()])
    role = SelectField('الدور', choices=[('admin','مدير (admin)'), ('doctor','طبيب (doctor)')])

class PatientForm(FlaskForm):
    full_name = StringField('الاسم الكامل', validators=[DataRequired()])
    phone = StringField('الهاتف', validators=[Optional()])
    dob = StringField('تاريخ الميلاد', validators=[Optional()])
    notes = StringField('ملاحظات', validators=[Optional()])

class AppointmentForm(FlaskForm):
    patient_id = SelectField('المريض', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('الطبيب', coerce=int, validators=[DataRequired()])
    start_datetime = StringField('تاريخ ووقت البداية', validators=[DataRequired()])
    end_datetime = StringField('تاريخ ووقت النهاية', validators=[Optional()])
    reason = StringField('السبب', validators=[Optional()])
