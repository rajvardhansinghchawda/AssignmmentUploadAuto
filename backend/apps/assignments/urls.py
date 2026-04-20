from django.urls import path
from .views import (
    TriggerRunView,
    RunListView,
    RunDetailView,
    RunLogStreamView,
    DocListView,
    StopRunView,
)

urlpatterns = [
    path("run/", TriggerRunView.as_view(), name="trigger-run"),
    path("runs/", RunListView.as_view(), name="run-list"),
    path("runs/<int:pk>/", RunDetailView.as_view(), name="run-detail"),
    path("runs/<int:pk>/stop/", StopRunView.as_view(), name="run-stop"),
    path("runs/<int:pk>/stream/", RunLogStreamView.as_view(), name="run-stream"),
    path("docs/", DocListView.as_view(), name="doc-list"),
]
