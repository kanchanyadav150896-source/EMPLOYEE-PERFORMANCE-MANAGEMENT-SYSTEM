from django.core.management.base import BaseCommand
from performance.models import Employee, User
from django.contrib.auth.hashers import make_password
from datetime import date
import random

class Command(BaseCommand):
    help = "Create 20 sample employees with login credentials"

    def handle(self, *args, **kwargs):
        departments = ["Engineering", "Marketing", "HR", "Finance", "Sales"]
        roles = ["employee", "manager"]

        for i in range(1, 21):
            emp_name = f"Employee{i}"
            email = f"employee{i}@example.com"
            department = random.choice(departments)
            role = random.choice(roles)

            # Create employee
            emp = Employee.objects.create(
                name=emp_name,
                email=email,
                department=department,
                hire_date=date(2023, random.randint(1, 12), random.randint(1, 28)),
                role="employee",
                manager_id=None  # Optionally assign manager later
            )

            # Create login user
            username = f"user{i}"
            password = f"Pass@{i}123"
            User.objects.create(
                employee=emp,
                username=username,
                password_hash=make_password(password),
                role="employee"
            )

            self.stdout.write(self.style.SUCCESS(f"Created {username} / {password}"))
