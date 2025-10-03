from django.db import models, transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=1, updated_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=0)

    def dead(self):
        return self.filter(is_deleted=1)

class Employee(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, db_index=True)
    manager = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='direct_reports', db_index=True)
    hire_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True,)

    objects = SoftDeleteQuerySet.as_manager()

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted','updated_at'])

    def __str__(self):
        return f"{self.name} ({self.department})"

class ReviewCycle(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=(('active','active'),('closed','closed')), default='active')

class Review(models.Model):
    REVIEW_TYPE_CHOICES = (('self','self'),('manager','manager'),('peer','peer'))
    STATUS_CHOICES = (('draft','draft'),('submitted','submitted'))

    employee = models.ForeignKey(Employee, related_name='reviews', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(Employee, related_name='reviews_given', on_delete=models.SET_NULL, null=True)
    cycle = models.ForeignKey(ReviewCycle, related_name='reviews', on_delete=models.CASCADE)
    review_type = models.CharField(max_length=10, choices=REVIEW_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    submitted_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True,)

    class Meta:
        unique_together = ('employee','reviewer','cycle','review_type')
        indexes = [
            models.Index(fields=['employee','cycle']),
            models.Index(fields=['cycle']),
        ]

class Score(models.Model):
    CRITERIA_CHOICES = (('technical','technical'),('communication','communication'),('leadership','leadership'),('goals','goals'))
    review = models.ForeignKey(Review, related_name='scores', on_delete=models.CASCADE)
    criteria = models.CharField(max_length=20, choices=CRITERIA_CHOICES)
    score = models.IntegerField()
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True,)

    class Meta:
        indexes = [models.Index(fields=['review'])]

class Goal(models.Model):
    STATUS_CHOICES = (('not_started','not_started'),('in_progress','in_progress'),('completed','completed'))
    employee = models.ForeignKey(Employee, related_name='goals', on_delete=models.CASCADE)
    cycle = models.ForeignKey(ReviewCycle, related_name='goals', on_delete=models.CASCADE)
    description = models.TextField()
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True,)

class User(models.Model):
    employee = models.ForeignKey(Employee, null=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=512)
    role = models.CharField(max_length=10, choices=(('employee','employee'),('manager','manager'),('hr','hr')))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

class AuditLog(models.Model):
    actor_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    target_table = models.CharField(max_length=100, null=True, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True,)
