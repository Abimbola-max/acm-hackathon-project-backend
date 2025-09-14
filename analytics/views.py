from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncWeek
import pandas as pd
import hashlib
from datetime import datetime
from .models import RoyaltyStatement, Platform, Track, Album, CsvUpload
from .serializers import (
    DashboardSummarySerializer, StreamsOverTimeSerializer,
    TopTracksSerializer, PlatformSerializer, AlbumSerializer,
    TrackSerializer, RoyaltyStatementSerializer, CsvUploadSerializer
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


class RoyaltyStatementListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/royalty-statements - List all royalty statements"""
        user = request.user
        statements = RoyaltyStatement.objects.filter(artist=user).select_related('track', 'platform')
        serializer = RoyaltyStatementSerializer(statements, many=True)
        return Response(serializer.data)


class RoyaltyStatementDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """GET /api/royalty-statements/{id} - Get specific royalty statement"""
        user = request.user
        try:
            statement = RoyaltyStatement.objects.get(id=pk, artist=user)
            serializer = RoyaltyStatementSerializer(statement)
            return Response(serializer.data)
        except RoyaltyStatement.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class CsvUploadListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/csv-uploads - List all CSV uploads for the user"""
        user = request.user
        uploads = CsvUpload.objects.filter(artist=user).order_by('-uploaded_at')
        serializer = CsvUploadSerializer(uploads, many=True)
        return Response(serializer.data)


class CsvUploadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """GET /api/csv-uploads/{id} - Get specific CSV upload details"""
        user = request.user
        try:
            upload = CsvUpload.objects.get(id=pk, artist=user)
            serializer = CsvUploadSerializer(upload)
            return Response(serializer.data)
        except CsvUpload.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)


class CsvUploadCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def post(self, request):
        """POST /api/csv-uploads - Upload and process a CSV file"""
        user = request.user
        csv_file = request.FILES.get('file')

        if not csv_file:
            return Response({'error': 'No file provided'}, status=400)

        # Create upload record
        upload = CsvUpload.objects.create(
            artist=user,
            filename=csv_file.name,
            status='processing',
            total_rows=0
        )

        try:
            # Process the CSV file
            df = pd.read_csv(csv_file)
            upload.total_rows = len(df)
            upload.save()

            success_count = 0
            error_count = 0
            error_messages = []

            for index, row in df.iterrows():
                try:
                    # Extract data from CSV row (adjust column names as needed)
                    track_name = row.get('track_name', '')
                    platform_name = row.get('platform', '')
                    streams = int(row.get('streams', 0))
                    revenue = float(row.get('revenue', 0.0))
                    currency = row.get('currency', 'USD')
                    period_end_str = row.get('period_end', '')

                    # Parse date (handle different formats)
                    try:
                        period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
                    except:
                        period_end = datetime.strptime(period_end_str, '%d/%m/%Y').date()

                    period_start = period_end.replace(day=1)  # Assuming monthly reports

                    # Get or create track
                    track, created = Track.objects.get_or_create(
                        artist=user,
                        name=track_name,
                        defaults={'name': track_name}
                    )

                    # Get platform
                    try:
                        platform = Platform.objects.get(name__iexact=platform_name)
                    except Platform.DoesNotExist:
                        platform = Platform.objects.create(
                            name=platform_name,
                            api_name=platform_name.lower().replace(' ', '_')
                        )

                    # Generate unique hash for this data row to prevent duplicates
                    source_string = f"{user.id}-{track.id}-{platform.id}-{period_end}-{streams}-{revenue}-{currency}"
                    source_row_hash = hashlib.sha256(source_string.encode()).hexdigest()

                    # Check for duplicate before creating
                    if not RoyaltyStatement.objects.filter(source_row_hash=source_row_hash).exists():

                        RoyaltyStatement.objects.create(
                            artist=user,
                            track=track,
                            platform=platform,
                            upload=upload,
                            period_start=period_start,
                            period_end=period_end,
                            streams=streams,
                            revenue=revenue,
                            currency=currency,
                            source_row_hash=source_row_hash
                        )
                        success_count += 1
                    else:
                        pass

                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Row {index + 1}: {str(e)}")
                    continue

            # Update upload status
            upload.success_count = success_count
            upload.error_count = error_count
            upload.processed_rows = success_count + error_count

            if error_messages:
                upload.error_log = "\n".join(error_messages[:10])

            if upload.processed_rows >= upload.total_rows:
                upload.status = 'completed' if error_count == 0 else 'completed_with_errors'

            upload.save()

            response_data = {
                'message': f'Processed {success_count} rows successfully',
                'errors': error_count,
                'upload_id': upload.id
            }

            if error_count > 0:
                response_data['error_samples'] = error_messages[:3]  # Show first 3 errors

            serializer = CsvUploadSerializer(upload)
            return Response(serializer.data, status=201)

        except Exception as e:
            # Mark upload as failed
            upload.status = 'failed'
            upload.error_log = str(e)
            upload.save()

            return Response({
                'error': 'Failed to process CSV file',
                'details': str(e)
            }, status=500)