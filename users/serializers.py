from rest_framework import serializers
from .models import User, Profile

class SignupSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES, write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')

        # Create the user
        user = User.objects.create_user(password=password, **validated_data)

        # ✅ Update the existing profile created by signals
        if hasattr(user, "profile"):
            user.profile.role = role
            user.profile.save()

        return user





class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class PasswordLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    address = serializers.CharField(source='profile.address', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'role', 'address', 'phone']
        read_only_fields = ['id', 'date_joined']
