from rest_framework import serializers
from .models import Employee, Review, Score, Goal, ReviewCycle, User

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = ['id','criteria','score','comments']

class ReviewSerializer(serializers.ModelSerializer):
    scores = ScoreSerializer(many=True, required=False)
    class Meta:
        model = Review
        fields = ['id','employee','reviewer','cycle','review_type','status','submitted_date','scores']

    def create(self, validated_data):
        scores_data = validated_data.pop('scores', [])
        review = Review.objects.create(**validated_data)
        for s in scores_data:
            Score.objects.create(review=review, **s)
        return review

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id','name','email','department','manager','hire_date','role']

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['id','employee','cycle','description','target_date','status','progress']
