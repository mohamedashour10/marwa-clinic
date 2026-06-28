from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Patient, Doctor, Appointment, User
from datetime import datetime
from dateutil import parser as dateparser

# Edit these URLs if your setup differs
SQLITE_URL = 'sqlite:///clinic.db'
PG_URL = 'postgresql://postgres:postgres@db:5432/clinic_db'

sqlite_engine = create_engine(SQLITE_URL)
pg_engine = create_engine(PG_URL)

SQLiteSession = sessionmaker(bind=sqlite_engine)
PgSession = sessionmaker(bind=pg_engine)

src = SQLiteSession()
dst = PgSession()


def parse_datetime_like(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return dateparser.parse(s)
    except Exception:
        return None

# Patients
for p in src.query(Patient).all():
    new_p = Patient(
        id=p.id,
        full_name=p.full_name,
        dob=p.dob,
        phone=p.phone,
        email=getattr(p, 'email', None),
        address=getattr(p, 'address', None),
        notes=p.notes,
        created_at=p.created_at
    )
    dst.merge(new_p)
dst.commit()
print("Patients migrated")

# Doctors
for d in src.query(Doctor).all():
    new_d = Doctor(
        id=d.id,
        name=d.name,
        specialty=d.specialty,
        phone=d.phone,
        email=getattr(d, 'email', None),
        notes=d.notes,
        created_at=d.created_at
    )
    dst.merge(new_d)
dst.commit()
print("Doctors migrated")

# Appointments
for a in src.query(Appointment).all():
    start = parse_datetime_like(getattr(a, 'start_datetime', None))
    end = parse_datetime_like(getattr(a, 'end_datetime', None)) if getattr(a, 'end_datetime', None) else None
    new_a = Appointment(
        id=a.id,
        patient_id=a.patient_id,
        doctor_id=a.doctor_id,
        start_datetime=start,
        end_datetime=end,
        reason=getattr(a, 'reason', None),
        status=getattr(a, 'status', None) or 'scheduled',
        created_at=getattr(a, 'created_at', None)
    )
    dst.merge(new_a)
dst.commit()
print("Appointments migrated")
