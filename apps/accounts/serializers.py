from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("role", "created_at")
        read_only_fields = ("created_at",)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "profile")
        read_only_fields = ("id", "email")


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)

    def to_internal_value(self, data):
        if "username" in data:
            raise serializers.ValidationError(
                {"username": "This field is not allowed. Email is used as the username."}
            )
        return super().to_internal_value(data)

    def validate_email(self, value):
        email = value.lower()
        existing = User.objects.filter(email__iexact=email).first()
        if existing and existing.is_active:
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        role = validated_data["role"]

        user = User.objects.filter(email__iexact=email).first()
        if user:
            user.set_password(password)
            user.is_active = False
            user.save()
            Profile.objects.update_or_create(user=user, defaults={"role": role})
        else:
            user = User(username=email, email=email, is_active=False)
            user.set_password(password)
            user.save()
            Profile.objects.create(user=user, role=role)

        return user


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        try:
            user = User.objects.select_related("profile").get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError(
                "Email not verified. Please verify your email before logging in."
            )

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        attrs["user"] = user
        return attrs
