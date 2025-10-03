from django.urls import path
from . import views

urlpatterns = [
    path("", views.home),
    path('auth/login', views.login),
    path('auth/logout', views.logout),
    path('reviews', views.create_review), 
    path('reviews/bulk-import', views.reviews_bulk_import),
    path('reviews/<int:id>', views.get_review),
    path('reviews/<int:id>/submit', views.submit_review),
    path('employees/<int:id>/reviews', views.employee_reviews),
    path('employees/<int:id>/performance-trend', views.get_performance_trend), 
    path('employees/<int:id>/goals', views.employee_goals),
    path('departments/<str:dept>/summary', views.department_summary),
]
