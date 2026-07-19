from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    LoginTokenObtainPairSerializer,
    MeSerializer,
    RegisterSerializer,
    ResendCodeSerializer,
    VerifyEmailSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Creates the inactive employee account + profile + photo + documents
    in one multipart request, and emails a 6-digit verification code."""

    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_scope = "auth-register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "detail": "Hisob yaratildi. Emailingizga yuborilgan kodni tasdiqlang.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth-verify"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Email tasdiqlandi. Endi tizimga kirishingiz mumkin."}
        )


class ResendCodeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth-resend-code"

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Agar hisob mavjud bo'lsa, yangi kod yuborildi."})


class LoginView(TokenObtainPairView):
    serializer_class = LoginTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth-login"


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
