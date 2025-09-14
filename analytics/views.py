from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncWeek
from .models import RoyaltyStatement, Platform, Track, Album
from .serializers import (
    DashboardSummarySerializer, StreamsOverTimeSerializer,
    TopTracksSerializer, PlatformSerializer, AlbumSerializer,
    TrackSerializer
)


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        totals = RoyaltyStatement.objects.filter(artist=user).aggregate(
            total_streams=Sum('streams'), total_revenue=Sum('revenue')
        )
        platform_data = []
        platforms = Platform.objects.all()
        for platform in platforms:
            platform_stats = RoyaltyStatement.objects.filter(
                artist=user, platform=platform
            ).aggregate(streams=Sum('streams'), revenue=Sum('revenue'))
            if platform_stats['streams']:
                platform_data.append({
                    'platform_name': platform.name,
                    'platform_icon': platform.api_name,
                    'streams': platform_stats['streams'],
                    'revenue': platform_stats['revenue'] or 0,
                    'percentage': 0
                })
        total_streams_val = totals['total_streams'] or 1
        for platform in platform_data:
            platform['percentage'] = round((platform['streams'] / total_streams_val) * 100)
        data = {
            "total_streams": totals['total_streams'] or 0,
            "total_revenue": totals['total_revenue'] or 0,
            "currency": "USD", "platform_breakdown": platform_data,
            "total_albums": Album.objects.filter(artist=user).count(),
            "total_tracks": Track.objects.filter(artist=user).count()
        }
        serializer = DashboardSummarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class TotalStreamsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total = RoyaltyStatement.objects.filter(artist=user).aggregate(
            total_streams=Sum('streams'))['total_streams'] or 0
        return Response({'total_streams': total})


class TotalRevenueView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total = RoyaltyStatement.objects.filter(artist=user).aggregate(
            total_revenue=Sum('revenue'))['total_revenue'] or 0
        return Response({'total_revenue': float(total), 'currency': 'USD'})


class StreamsByPlatformView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        platform_stats = RoyaltyStatement.objects.filter(artist=user).values(
            'platform__name', 'platform__api_name'
        ).annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
                   ).order_by('-total_streams')
        data = []
        for stat in platform_stats:
            data.append({
                'platform_name': stat['platform__name'],
                'platform_icon': stat['platform__api_name'],
                'streams': stat['total_streams'] or 0,
                'revenue': float(stat['total_revenue'] or 0)
            })
        return Response({'platforms': data})


class StreamsOverTimeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        period = request.GET.get('period', '6months')
        queryset = RoyaltyStatement.objects.filter(artist=user)
        trunc_func = TruncWeek('period_end') if period != '1year' else TruncMonth('period_end')
        time_series_data = queryset.annotate(period_date=trunc_func).values(
            'period_date').annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
                                    ).order_by('period_date')
        formatted_data = []
        for item in time_series_data:
            if item['period_date']:
                formatted_data.append({
                    'date': item['period_date'].isoformat(),
                    'streams': item['total_streams'] or 0,
                    'revenue': float(item['total_revenue'] or 0)
                })
        serializer = StreamsOverTimeSerializer(formatted_data, many=True)
        return Response(serializer.data)


class TopTracksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        top_tracks = RoyaltyStatement.objects.filter(artist=user).values(
            'track__name', 'track__id', 'platform__name'
        ).annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
                   ).order_by('-total_streams')[:10]
        data = []
        for track in top_tracks:
            data.append({
                'track_name': track['track__name'],
                'track_id': track['track__id'],
                'streams': track['total_streams'] or 0,
                'revenue': float(track['total_revenue'] or 0),
                'platform': track['platform__name']
            })
        serializer = TopTracksSerializer(data, many=True)
        return Response(serializer.data)


class RevenueByPlatformView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        revenue_stats = RoyaltyStatement.objects.filter(artist=user).values(
            'platform__name').annotate(total_revenue=Sum('revenue')
                                       ).order_by('-total_revenue')
        return Response({'revenue_by_platform': list(revenue_stats)})


class PlatformListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platforms = Platform.objects.all()
        serializer = PlatformSerializer(platforms, many=True)
        return Response(serializer.data)


class AlbumListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        albums = Album.objects.filter(artist=user)
        serializer = AlbumSerializer(albums, many=True)
        return Response(serializer.data)


class TrackListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tracks = Track.objects.filter(artist=user)
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)