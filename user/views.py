from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, ProfileSerializer, ChangePasswordSerializer, ChangeUsernameSerializer, UserSerializer
from .models import CustomUser

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User registered successfully",
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        }, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response({
            "message": "Login successful",
            "tokens": response.data
        })

class LogoutView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logout(request)
        request.user.is_active = False  # Note: is_active in Django typically for account activation, but per req, set to False on logout
        request.user.save()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

class MeView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

# Artist Profile Views (assuming user is artist; extend permissions as needed)

class ArtistProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

class DashboardSummaryView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer  # Reuse, or create specific for stats

    def get(self, request, *args, **kwargs):
        user = request.user
        stats = {
            "total_tracks": 15,  # Calculate properly in production
            "total_streams": 1245893,
            "total_platforms": user.total_platforms
        }
        return Response(stats)

# Additional views for change password and username

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not user.check_password(serializer.data['old_password']):
            return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.data['new_password'])
        user.save()
        return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

class ChangeUsernameView(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeUsernameSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.username = serializer.data['new_username']
        user.save()
        return Response({"message": "Username updated successfully"}, status=status.HTTP_200_OK)

