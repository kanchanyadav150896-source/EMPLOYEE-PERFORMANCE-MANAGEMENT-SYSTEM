from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Employee, Review, Score, Goal, ReviewCycle, User
from .serializers import ReviewSerializer, EmployeeSerializer, GoalSerializer
from .auth_models import AuthToken
from django.utils import timezone
import uuid
from .services import *
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Welcome to TechCorp Performance Management API"})


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = get_object_or_404(User, username=username)
    # verify password - if using Django's hasher:
    from django.contrib.auth.hashers import check_password
    if not check_password(password, user.password_hash):
        return Response({'detail':'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    token = str(uuid.uuid4())
    AuthToken.objects.create(user=user, token=token)
    return Response({'token': token, 'role': user.role})

@api_view(['POST'])
def logout(request):
    token = request.headers.get('Authorization')
    if not token:
        return Response({'detail':'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
    AuthToken.objects.filter(token=token).delete()
    return Response({'detail':'logged out'})


# Create new review
@api_view(['POST'])
def create_review(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        # verify duplicate: no duplicate for same employee/cycle/reviewer/review_type
        employee = serializer.validated_data['employee']
        reviewer = serializer.validated_data['reviewer']
        cycle = serializer.validated_data['cycle']
        review_type = serializer.validated_data['review_type']
        exists = Review.objects.filter(employee=employee, reviewer=reviewer, cycle=cycle, review_type=review_type, is_deleted=False).exists()
        if exists:
            return Response({'detail':'Duplicate review exists'}, status=status.HTTP_400_BAD_REQUEST)
        review = serializer.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Submit completed review
@api_view(['PUT'])
def submit_review(request, id):
    review = get_object_or_404(Review, id=id, is_deleted=False)
    if review.status == 'submitted':
        return Response({'detail':'Already submitted'}, status=status.HTTP_400_BAD_REQUEST)
    # Validate scores exist and have all four criteria
    scores = list(review.scores.all())
    criteria_present = {s.criteria for s in scores}
    required = {'technical','communication','leadership','goals'}
    if criteria_present != required:
        return Response({'detail':'All four criteria scores required before submission', 'missing': list(required - criteria_present)}, status=status.HTTP_400_BAD_REQUEST)
    review.status = 'submitted'
    review.submitted_date = timezone.now()
    review.save()
    # log audit (could be implemented via signal)
    return Response({'detail':'submitted'})

# Get review details
@api_view(['GET'])
def get_review(request, id):
    review = get_object_or_404(Review, id=id, is_deleted=False)
    return Response(ReviewSerializer(review).data)

# Get employee's review history
@api_view(['GET'])
def employee_reviews(request, id):
    employee = get_object_or_404(Employee, id=id, is_deleted=False)
    reviews = Review.objects.filter(employee=employee, is_deleted=False).order_by('-cycle__start_date')
    return Response(ReviewSerializer(reviews, many=True).data)

# Employee goals
@api_view(['GET'])
def employee_goals(request, id):
    employee = get_object_or_404(Employee, id=id, is_deleted=False)
    goals = Goal.objects.filter(employee=employee, is_deleted=False).order_by('-created_at')
    return Response(GoalSerializer(goals, many=True).data)

# Department summary (simple)
@api_view(['GET'])
def department_summary(request, dept):
    from django.db.models import Avg
    employees = Employee.objects.filter(department=dept, is_deleted=False)
    total = employees.count()
    return Response({'department': dept, 'total_employees': total})

# Bulk import reviews (JSON)
@api_view(['POST'])
def reviews_bulk_import(request):
    data = request.data
    reviews = data.get('reviews', [])
    created = []
    errors = []
    for r in reviews:
        serializer = ReviewSerializer(data=r)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    employee = serializer.validated_data['employee']
                    reviewer = serializer.validated_data['reviewer']
                    cycle = serializer.validated_data['cycle']
                    review_type = serializer.validated_data['review_type']
                    if Review.objects.filter(employee=employee, reviewer=reviewer, cycle=cycle, review_type=review_type, is_deleted=False).exists():
                        errors.append({'item': r, 'error':'duplicate'})
                        continue
                    review = serializer.save()
                    created.append(review.id)
            except Exception as e:
                errors.append({'item': r, 'error':str(e)})
        else:
            errors.append({'item': r, 'error': serializer.errors})
    return Response({'created': created, 'errors': errors})
