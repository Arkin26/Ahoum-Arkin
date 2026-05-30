from django.urls import path

from .views import (
    LoginView,
    MeView,
    SignupView,
    TokenRefreshViewWithSchema,
    VerifyEmailView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="auth-signup"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshViewWithSchema.as_view(), name="auth-refresh"),
    path("token/refresh/", TokenRefreshViewWithSchema.as_view(), name="auth-token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
