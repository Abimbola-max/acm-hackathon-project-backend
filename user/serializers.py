from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'created_at')  # created_at is auto from AbstractUser's date_joined

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = True
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        user.is_active = True
        user.save()
        return token

class ProfileSerializer(serializers.ModelSerializer):
    genres = serializers.ListField(child=serializers.CharField(), required=False)
    social_links = serializers.DictField(child=serializers.CharField(), required=False)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('user_id', 'display_name', 'avatar_url', 'bio', 'country', 'city', 'genres', 'social_links', 'total_platforms', 'stats')
        extra_kwargs = {
            'user_id': {'source': 'id', 'read_only': True},
        }

    def get_stats(self, obj):
        # Placeholder for calculated stats; in real app, query related models
        return {
            'total_tracks': 15,  # Calculate from admin or related models
            'total_streams': 1245893,  # Calculate from admin or related models
            'total_platforms': obj.total_platforms
        }

    def update(self, instance, validated_data):
        # Handle avatar upload to Cloudinary automatically via CloudinaryField
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email')