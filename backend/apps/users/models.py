from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    enrollment_no = models.CharField(max_length=30, blank=True)
    piemr_password = models.TextField(blank=True)          # Fernet-encrypted
    google_access_token = models.TextField(blank=True)     # Fernet-encrypted
    google_refresh_token = models.TextField(blank=True)    # Fernet-encrypted
    token_expiry = models.DateTimeField(null=True, blank=True)
    is_setup_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.enrollment_no})"

    @property
    def has_piemr_credentials(self) -> bool:
        return bool(self.enrollment_no and self.piemr_password)
