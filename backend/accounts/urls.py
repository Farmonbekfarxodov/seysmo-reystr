from django.urls import path

from .views import LoginView, RefreshView, RegisterView, ResendCodeView, VerifyEmailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("resend-code/", ResendCodeView.as_view(), name="auth-resend-code"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
]
