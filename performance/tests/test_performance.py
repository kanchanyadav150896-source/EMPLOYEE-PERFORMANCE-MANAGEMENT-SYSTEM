from performance.models import Employee, User

# Create employee
emp = Employee.objects.create(
    name="Kanchan Yadav",
    email="kanchan@example.com",
    department="Development",
    role="employee"
)

# Create user linked to employee
user = User.objects.create_user(
    username="kanchan",
    password="Test@123",
    employee=emp,
    role="employee"
)