from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import analyze_and_store_artist_data, generate_artist_report
from .models import PlatformInsight


class AnalyzeArtistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Triggers data collection from all music platforms for the authenticated artist.
        Expects 'artist_name' and optionally 'spotify_artist_id' in request data.
        """
        artist_user = request.user
        artist_name = request.data.get('artist_name', artist_user.username)  # Default to username
        spotify_artist_id = request.data.get('spotify_artist_id')

        if not artist_name:
            return Response(
                {'error': 'artist_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            success = analyze_and_store_artist_data(artist_user, artist_name, spotify_artist_id)
            if success:
                return Response({
                    'message': f'Successfully analyzed data for {artist_name}',
                    'artist_name': artist_name
                })
            else:
                return Response(
                    {'error': 'Failed to analyze artist data'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ArtistInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns all stored insights for the authenticated artist.
        """
        artist_user = request.user
        insights = PlatformInsight.objects.filter(artist=artist_user).order_by('-timestamp')

        # Format the response
        insights_data = []
        for insight in insights:
            insights_data.append({
                'platform': insight.platform,
                'track_name': insight.track_name,
                'insight_type': insight.insight_type,
                'value': insight.value,
                'timestamp': insight.timestamp
            })

        return Response({
            'artist': artist_user.username,
            'insights': insights_data,
            'total_insights': len(insights_data)
        })


class ArtistReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generates and returns a comprehensive performance report for the artist.
        """
        artist_user = request.user
        report = generate_artist_report(artist_user)

        return Response(report)


class PlatformComparisonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Compares the artist's performance across different platforms.
        """
        artist_user = request.user
        insights = PlatformInsight.objects.filter(artist=artist_user)

        # This would implement more sophisticated comparison logic
        # For now, return a simple platform comparison
        platform_stats = {}
        for platform in insights.values_list('platform', flat=True).distinct():
            platform_insights = insights.filter(platform=platform)
            platform_stats[platform] = {
                'track_count': platform_insights.values('track_name').distinct().count(),
                'average_value': platform_insights.aggregate(avg=models.Avg('value'))['avg'] or 0
            }

        return Response({
            'artist': artist_user.username,
            'platform_comparison': platform_stats
        })