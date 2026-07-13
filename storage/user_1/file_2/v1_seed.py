"""
Quick seed script for demo data.
Run with: python seed.py
"""
from datetime import date, timedelta

from app.database import SessionLocal, Base, engine
from app.models.user import User, RoleName
from app.models.vehicle import Vehicle, VehicleStatus, VehicleType
from app.models.driver import Driver, DriverStatus
from app.auth.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

DEMO_USERS = [
    {"full_name": "Admin User", "email": "admin@trackteq.com", "password": "admin123", "role": RoleName.ADMIN},
    {"full_name": "Fleet Manager", "email": "fleet@trackteq.com", "password": "fleet123", "role": RoleName.FLEET_MANAGER},
    {"full_name": "Driver Dan", "email": "driver@trackteq.com", "password": "driver123", "role": RoleName.DRIVER},
    {"full_name": "Safety Officer", "email": "safety@trackteq.com", "password": "safety123", "role": RoleName.SAFETY_OFFICER},
    {"full_name": "Finance Analyst", "email": "finance@trackteq.com", "password": "finance123", "role": RoleName.FINANCIAL_ANALYST},
]

DEMO_VEHICLES = [
    {"registration_number": "GJ-01-VAN-05", "name_model": "Tata Ace Van-05", "type": VehicleType.VAN,
     "max_load_capacity": 500, "odometer": 12000, "acquisition_cost": 800000, "region": "Ahmedabad"},
    {"registration_number": "GJ-01-TRK-11", "name_model": "Ashok Leyland Truck-11", "type": VehicleType.TRUCK,
     "max_load_capacity": 5000, "odometer": 45000, "acquisition_cost": 2500000, "region": "Ahmedabad"},
    {"registration_number": "GJ-05-MTR-02", "name_model": "Mahindra Bolero Mini-02", "type": VehicleType.MINI_TRUCK,
     "max_load_capacity": 1200, "odometer": 30000, "acquisition_cost": 1000000, "region": "Surat"},
]

DEMO_DRIVERS = [
    {"name": "Alex", "license_number": "GJ0120230001", "license_category": "LMV",
     "license_expiry_date": date.today() + timedelta(days=365), "contact_number": "9999900001"},
    {"name": "Rahul", "license_number": "GJ0120230002", "license_category": "HMV",
     "license_expiry_date": date.today() + timedelta(days=200), "contact_number": "9999900002"},
    {"name": "Priya", "license_number": "GJ0120230003", "license_category": "LMV",
     "license_expiry_date": date.today() - timedelta(days=10), "contact_number": "9999900003"},  # expired, for testing
]


def seed():
    for u in DEMO_USERS:
        if not db.query(User).filter(User.email == u["email"]).first():
            db.add(User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
            ))

    for v in DEMO_VEHICLES:
        if not db.query(Vehicle).filter(Vehicle.registration_number == v["registration_number"]).first():
            db.add(Vehicle(**v, status=VehicleStatus.AVAILABLE))

    for d in DEMO_DRIVERS:
        if not db.query(Driver).filter(Driver.license_number == d["license_number"]).first():
            db.add(Driver(**d, status=DriverStatus.AVAILABLE))

    db.commit()
    print("Seed complete.")
    print("\nDemo logins (email / password):")
    for u in DEMO_USERS:
        print(f"  {u['email']} / {u['password']}  ({u['role'].value})")


if __name__ == "__main__":
    seed()
    db.close()
