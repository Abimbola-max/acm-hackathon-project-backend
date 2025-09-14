from django.shortcuts import render

# Create your views here.
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import logout
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, ProfileSerializer, ChangePasswordSerializer, ChangeUsernameSerializer, UserSerializer
from .models import CustomUser

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response({
                'message': 'You have registered successfully',
                'user': user_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = CustomUser.objects.filter(email=request.data.get('email')).first()
        return Response({
            'message': 'Login Successful.',
            'refresh': serializer.validated_data['refresh'],
            'access': serializer.validated_data['access'],
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class LogoutView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logout(request)
        request.user.is_active = False
        request.user.save()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

class MeView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ArtistProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

class DashboardSummaryView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        stats = {
            "total_tracks": 15,
            "total_streams": 1245893,
            "total_platforms": user.total_platforms
        }
        return Response(stats)

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

