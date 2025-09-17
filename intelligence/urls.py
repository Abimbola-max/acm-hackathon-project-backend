from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.AnalyzeArtistView.as_view(), name='analyze-artist'),
    path('insights/', views.ArtistInsightsView.as_view(), name='artist-insights'),
    path('report/', views.ArtistReportView.as_view(), name='artist-report'),
    path('comparison/', views.PlatformComparisonView.as_view(), name='platform-comparison'),
]