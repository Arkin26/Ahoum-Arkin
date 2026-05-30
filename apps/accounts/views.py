from django.contrib.auth.models import User

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from ahoum.exceptions import api_error

from .otp import generate_otp, send_otp_email, store_otp, verify_otp
from .serializers import (
    LoginSerializer,
    SignupSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user (sends email OTP)",
        request=SignupSerializer,
        responses={201: {"type": "object", "properties": {"detail": {"type": "string"}}}},
        examples=[
            OpenApiExample(
                "Facilitator signup",
                value={"email": "facilitator@example.com", "password": "Test1234!", "role": "facilitator"},
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = generate_otp()
        store_otp(user.email, otp)
        send_otp_email(user.email, otp)

        return Response(
            {"detail": "Signup successful. Check server logs for OTP and verify your email."},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Verify email with OTP",
        request=VerifyEmailSerializer,
        responses={200: UserSerializer},
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].lower()
        otp = serializer.validated_data["otp"]

        ok, reason = verify_otp(email, otp)
        if not ok:
            codes = {
                "expired": "otp_expired",
                "invalid": "invalid_otp",
                "max_attempts": "max_otp_attempts",
            }
            messages = {
                "expired": "OTP has expired. Please sign up again.",
                "invalid": "Invalid OTP.",
                "max_attempts": "Maximum OTP attempts exceeded. Please sign up again.",
            }
            return api_error(messages[reason], codes[reason], status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.select_related("profile").get(email__iexact=email)
        except User.DoesNotExist:
            return api_error("User not found.", "user_not_found", status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(UserSerializer(user).data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Login with email and password",
        request=LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "access": {"type": "string"},
                    "refresh": {"type": "string"},
                },
            }
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Auth"], summary="Get current user profile", responses={200: UserSerializer})
    def get(self, request):
        user = User.objects.select_related("profile").get(pk=request.user.pk)
        return Response(UserSerializer(user).data)


class TokenRefreshViewWithSchema(TokenRefreshView):
    @extend_schema(tags=["Auth"], summary="Refresh access token")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
