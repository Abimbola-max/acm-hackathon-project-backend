from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = CustomUser.USERNAME_FIELD

    def validate(self, attrs):
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }
        if credentials['email'] and credentials['password']:
            user = CustomUser.objects.filter(email=credentials['email']).first()
            if user and user.check_password(credentials['password']):
                data = super().validate({
                    self.username_field: credentials['email'],
                    'password': credentials['password']
                })
                return data
            raise serializers.ValidationError('Invalid credentials')
        raise serializers.ValidationError('Email and password are required')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'created_at')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data.get('username', ''),
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.is_active = True
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'created_at')
        extra_kwargs = {
            'id': {'read_only': True}
        }

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
        return {
            'total_tracks': 15,
            'total_streams': 1245893,
            'total_platforms': obj.total_platforms
        }

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class ChangeUsernameSerializer(serializers.Serializer):
    new_username = serializers.CharField(required=True)