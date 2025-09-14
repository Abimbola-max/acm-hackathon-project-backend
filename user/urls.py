from django.urls import path
from .views import RegisterView, LoginView, LogoutView, MeView, ArtistProfileView, DashboardSummaryView, ChangePasswordView, ChangeUsernameView

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/me', MeView.as_view(), name='me'),
    path('artist/profile', ArtistProfileView.as_view(), name='artist_profile'),
    path('artist/dashboard-summary', DashboardSummaryView.as_view(), name='dashboard_summary'),
    # Add these if separate endpoints needed; otherwise, integrate into profile update
    path('auth/change-password', ChangePasswordView.as_view(), name='change_password'),
    path('auth/change-username', ChangeUsernameView.as_view(), name='change_username'),
]
