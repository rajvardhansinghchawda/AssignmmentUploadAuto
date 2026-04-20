from django.urls import path
from .views import GoogleLoginView, GoogleCallbackView, LogoutView, MeView

urlpatterns = [
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
