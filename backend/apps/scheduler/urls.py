from django.urls import path
from .views import SchedulerView

urlpatterns = [
    path("", SchedulerView.as_view(), name="scheduler"),
]
