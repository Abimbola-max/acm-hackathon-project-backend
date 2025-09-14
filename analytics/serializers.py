from rest_framework import serializers
from .models import Platform, Album, Track, RoyaltyStatement, CsvUpload


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ['id', 'name', 'api_name', 'base_url', 'created_at']


class AlbumSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.username', read_only=True)

    class Meta:
        model = Album
        fields = ['id', 'title', 'artist', 'artist_name', 'release_date', 'external_id', 'created_at']
        extra_kwargs = {
            'artist': {'write_only': True}
        }


class TrackSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.username', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True, allow_null=True)

    class Meta:
        model = Track
        fields = ['id', 'name', 'artist', 'artist_name', 'album', 'album_title', 'external_id', 'duration_seconds',
                  'track_number', 'created_at']
        extra_kwargs = {
            'artist': {'write_only': True},
            'album': {'write_only': True}
        }


class RoyaltyStatementSerializer(serializers.ModelSerializer):
    track_name = serializers.CharField(source='track.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    artist_name = serializers.CharField(source='artist.username', read_only=True)

    class Meta:
        model = RoyaltyStatement
        fields = [
            'id', 'artist', 'artist_name', 'track', 'track_name', 'platform', 'platform_name',
            'upload', 'period_start', 'period_end', 'streams', 'revenue', 'currency',
            'source_row_hash', 'created_at'
        ]
        extra_kwargs = {
            'artist': {'write_only': True},
            'track': {'write_only': True},
            'platform': {'write_only': True},
            'upload': {'write_only': True}
        }


class CsvUploadSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.username', read_only=True)

    class Meta:
        model = CsvUpload
        fields = [
            'id', 'artist', 'artist_name', 'filename', 'uploaded_at', 'status',
            'processed_rows', 'total_rows', 'success_count', 'error_count', 'error_log'
        ]
        read_only_fields = ['uploaded_at', 'processed_rows', 'success_count', 'error_count']
        extra_kwargs = {
            'artist': {'write_only': True}
        }


# Serializers for dashboard responses
class PlatformBreakdownSerializer(serializers.Serializer):
    platform_name = serializers.CharField()
    platform_icon = serializers.CharField()
    streams = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    percentage = serializers.IntegerField()


class DashboardSummarySerializer(serializers.Serializer):
    total_streams = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    platform_breakdown = PlatformBreakdownSerializer(many=True)
    # Optional: Add more summary fields
    total_albums = serializers.IntegerField(required=False)
    total_tracks = serializers.IntegerField(required=False)


# Additional serializers for specific endpoints
class StreamsOverTimeSerializer(serializers.Serializer):
    date = serializers.DateField()
    streams = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class TopTracksSerializer(serializers.Serializer):
    track_name = serializers.CharField()
    track_id = serializers.IntegerField()
    streams = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    platform = serializers.CharField()