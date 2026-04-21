from rest_framework import serializers
from django.contrib.auth.models import User
from .models import StudentProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id", "user", "name", "full_name", "enrollment_no",
            "is_setup_complete", "has_piemr_credentials",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at", "has_piemr_credentials"]

    def get_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.user.email


class ConfigSerializer(serializers.Serializer):
    """For POST /api/config/ — saving PIEMR credentials."""
    full_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    enrollment_no = serializers.CharField(max_length=30)
    piemr_password = serializers.CharField(write_only=True)
