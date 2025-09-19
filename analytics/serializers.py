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


# from rest_framework import serializers
# from .models import Platform, Album, Track, RoyaltyStatement, CsvUpload
#
#
# class PlatformSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Platform
#         fields = ['id', 'name', 'api_name', 'display_name', 'base_url', 'created_at']
#
#
# class AlbumSerializer(serializers.ModelSerializer):
#     artist_name = serializers.CharField(source='artist.username', read_only=True)
#     total_revenue = serializers.DecimalField(max_digits=14, decimal_places=6, read_only=True)
#     total_streams = serializers.IntegerField(read_only=True)
#
#     class Meta:
#         model = Album
#         fields = ['id', 'title', 'artist', 'artist_name', 'release_date', 'external_id',
#                  'upc', 'total_revenue', 'total_streams', 'created_at']
#         extra_kwargs = {'artist': {'write_only': True}}
#
#
# class TrackSerializer(serializers.ModelSerializer):
#     artist_name = serializers.CharField(source='artist.username', read_only=True)
#     album_title = serializers.CharField(source='album.title', read_only=True, allow_null=True)
#     total_revenue = serializers.DecimalField(max_digits=14, decimal_places=6, read_only=True)
#     total_streams = serializers.IntegerField(read_only=True)
#
#     class Meta:
#         model = Track
#         fields = ['id', 'name', 'artist', 'artist_name', 'album', 'album_title',
#                  'external_id', 'isrc', 'duration_seconds', 'track_number',
#                  'total_revenue', 'total_streams', 'created_at']
#         extra_kwargs = {
#             'artist': {'write_only': True},
#             'album': {'write_only': True, 'required': False}
#         }
#
#
# class RoyaltyStatementSerializer(serializers.ModelSerializer):
#     track_name = serializers.CharField(source='track.name', read_only=True)
#     platform_name = serializers.CharField(source='platform.name', read_only=True)
#     platform_display_name = serializers.CharField(source='platform.display_name', read_only=True)
#     artist_name = serializers.CharField(source='artist.username', read_only=True)
#     album_name = serializers.CharField(source='track.album.title', read_only=True, allow_null=True)
#     revenue_per_stream = serializers.DecimalField(max_digits=10, decimal_places=8, read_only=True)
#
#     class Meta:
#         model = RoyaltyStatement
#         fields = [
#             'id', 'artist', 'artist_name', 'track', 'track_name', 'platform',
#             'platform_name', 'platform_display_name', 'upload', 'period_start',
#             'period_end', 'report_date', 'streams', 'downloads', 'revenue',
#             'usd_revenue', 'territory', 'currency', 'quantity', 'unit_price',
#             'album_name', 'revenue_per_stream', 'source_row_hash', 'original_data',
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ['usd_revenue', 'source_row_hash', 'original_data', 'created_at', 'updated_at']
#         extra_kwargs = {
#             'artist': {'write_only': True},
#             'track': {'write_only': True},
#             'platform': {'write_only': True},
#             'upload': {'write_only': True}
#         }
#
#
# class CsvUploadSerializer(serializers.ModelSerializer):
#     artist_name = serializers.CharField(source='artist.username', read_only=True)
#     csv_headers = serializers.JSONField(read_only=True)
#
#     class Meta:
#         model = CsvUpload
#         fields = [
#             'id', 'artist', 'artist_name', 'filename', 'uploaded_at', 'status',
#             'processed_rows', 'total_rows', 'success_count', 'error_count',
#             'error_log', 'csv_headers'
#         ]
#         read_only_fields = ['uploaded_at', 'processed_rows', 'success_count',
#                            'error_count', 'error_log', 'csv_headers']
#
#
# # Dashboard serializers
# class PlatformBreakdownSerializer(serializers.Serializer):
#     platform_id = serializers.UUIDField()
#     platform_name = serializers.CharField()
#     platform_display_name = serializers.CharField()
#     platform_icon = serializers.CharField()
#     streams = serializers.IntegerField()
#     revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
#     avg_revenue_per_stream = serializers.DecimalField(max_digits=10, decimal_places=8)
#
#
# class TerritoryBreakdownSerializer(serializers.Serializer):
#     territory = serializers.CharField()
#     territory_name = serializers.CharField(source='get_territory_display', read_only=True)
#     streams = serializers.IntegerField()
#     revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
#
#
# class DashboardSummarySerializer(serializers.Serializer):
#     total_streams = serializers.IntegerField()
#     total_downloads = serializers.IntegerField()
#     total_revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     total_usd_revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     currency = serializers.CharField()
#     avg_revenue_per_stream = serializers.DecimalField(max_digits=10, decimal_places=8)
#     platform_breakdown = PlatformBreakdownSerializer(many=True)
#     territory_breakdown = TerritoryBreakdownSerializer(many=True, required=False)
#     total_albums = serializers.IntegerField()
#     total_tracks = serializers.IntegerField()
#     total_platforms = serializers.IntegerField()
#
#
# class StreamsOverTimeSerializer(serializers.Serializer):
#     date = serializers.DateField()
#     period = serializers.CharField()  # 'day', 'week', 'month'
#     streams = serializers.IntegerField()
#     revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     usd_revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#
#
# class TopTracksSerializer(serializers.Serializer):
#     track_id = serializers.UUIDField()
#     track_name = serializers.CharField()
#     artist_name = serializers.CharField()
#     album_name = serializers.CharField(allow_null=True)
#     streams = serializers.IntegerField()
#     revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     usd_revenue = serializers.DecimalField(max_digits=14, decimal_places=6)
#     avg_revenue_per_stream = serializers.DecimalField(max_digits=10, decimal_places=8)
#     platform_count = serializers.IntegerField()
#
#
# class CsvColumnMappingSerializer(serializers.Serializer):
#     """Serializer for CSV column mapping configuration"""
#     track_name = serializers.CharField(required=False)
#     track_id = serializers.CharField(required=False)
#     isrc = serializers.CharField(required=False)
#     platform = serializers.CharField(required=False)
#     platform_id = serializers.CharField(required=False)
#     streams = serializers.CharField(required=False)
#     downloads = serializers.CharField(required=False)
#     revenue = serializers.CharField(required=False)
#     currency = serializers.CharField(required=False)
#     territory = serializers.CharField(required=False)
#     period_start = serializers.CharField(required=False)
#     period_end = serializers.CharField(required=False)
#     report_date = serializers.CharField(required=False)
#     quantity = serializers.CharField(required=False)
#     unit_price = serializers.CharField(required=False)
#     album_title = serializers.CharField(required=False)
#     album_id = serializers.CharField(required=False)
#     upc = serializers.CharField(required=False)