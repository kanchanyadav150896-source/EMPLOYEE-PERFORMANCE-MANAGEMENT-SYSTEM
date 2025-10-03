from django.db import models
import uuid
from django.utils import timezone

class AuthToken(models.Model):
    user = models.ForeignKey('performance.User', on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True) 