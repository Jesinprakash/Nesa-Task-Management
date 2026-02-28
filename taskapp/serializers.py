from rest_framework import serializers
from taskapp.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class CreateTaskSerializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "assigned_to",
            "due_date",
        ]

    def validate_assigned_to(self, value):
        request = self.context.get("request")

        # Admin can assign only to their users
        if request.user.role == "ADMIN":
            if value.assigned_admin != request.user:
                raise serializers.ValidationError(
                    "You can assign tasks only to your users."
                )

        # Users cannot create tasks
        if request.user.role == "USER":
            raise serializers.ValidationError(
                "Users cannot create tasks."
            )

        return value









