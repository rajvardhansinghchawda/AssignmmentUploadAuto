from rest_framework import serializers
from .models import AssignmentRun, GeneratedDoc


class GeneratedDocSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDoc
        fields = [
            "id", "run", "subject_name", "assignment_no",
            "drive_url", "uploaded_to_portal", "created_at",
        ]


class AssignmentRunListSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.IntegerField(read_only=True)
    docs_count = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentRun
        fields = [
            "id", "status", "triggered_by",
            "started_at", "finished_at", "duration_seconds",
            "total_uploaded", "docs_count", "created_at",
        ]

    def get_docs_count(self, obj) -> int:
        return obj.docs.count()


class AssignmentRunDetailSerializer(serializers.ModelSerializer):
    docs = GeneratedDocSerializer(many=True, read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = AssignmentRun
        fields = [
            "id", "status", "triggered_by",
            "started_at", "finished_at", "duration_seconds",
            "log_output", "total_uploaded", "docs", "created_at",
        ]
