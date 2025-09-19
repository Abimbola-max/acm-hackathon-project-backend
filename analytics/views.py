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


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.parsers import MultiPartParser, JSONParser
# from rest_framework import status
# from django.db.models import Sum, Count, Q, F
# from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, Coalesce
# from django.utils import timezone
# from django.shortcuts import get_object_or_404
# import pandas as pd
# import hashlib
# import json
# from datetime import datetime, timedelta
# import re
# from decimal import Decimal
#
# from .models import RoyaltyStatement, Platform, Track, Album, CsvUpload
# from .serializers import (
#     DashboardSummarySerializer, StreamsOverTimeSerializer,
#     TopTracksSerializer, PlatformSerializer, AlbumSerializer,
#     TrackSerializer, RoyaltyStatementSerializer, CsvUploadSerializer,
#     CsvColumnMappingSerializer, TerritoryBreakdownSerializer
# )
#
#
# class DashboardSummaryView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         date_filter = self.get_date_filter(request)
#
#         # Get totals with date filter
#         totals = RoyaltyStatement.objects.filter(artist=user, **date_filter).aggregate(
#             total_streams=Coalesce(Sum('streams'), 0),
#             total_downloads=Coalesce(Sum('downloads'), 0),
#             total_revenue=Coalesce(Sum('revenue'), Decimal('0.0')),
#             total_usd_revenue=Coalesce(Sum('usd_revenue'), Decimal('0.0'))
#         )
#
#         # Platform breakdown
#         platform_data = []
#         platform_stats = RoyaltyStatement.objects.filter(artist=user, **date_filter).values(
#             'platform__id', 'platform__name', 'platform__display_name', 'platform__api_name'
#         ).annotate(
#             streams=Coalesce(Sum('streams'), 0),
#             revenue=Coalesce(Sum('revenue'), Decimal('0.0'))
#         ).order_by('-revenue')
#
#         for stat in platform_stats:
#             streams = stat['streams']
#             revenue = stat['revenue']
#             avg_rps = revenue / streams if streams > 0 else Decimal('0.0')
#
#             platform_data.append({
#                 'platform_id': stat['platform__id'],
#                 'platform_name': stat['platform__name'],
#                 'platform_display_name': stat['platform__display_name'] or stat['platform__name'],
#                 'platform_icon': stat['platform__api_name'],
#                 'streams': streams,
#                 'revenue': revenue,
#                 'percentage': 0,  # Will be calculated below
#                 'avg_revenue_per_stream': avg_rps
#             })
#
#         # Calculate percentages
#         total_revenue_val = totals['total_revenue'] or Decimal('0.01')
#         for platform in platform_data:
#             platform['percentage'] = round((platform['revenue'] / total_revenue_val) * 100, 2)
#
#         # Territory breakdown
#         territory_data = []
#         territory_stats = RoyaltyStatement.objects.filter(artist=user, **date_filter).values(
#             'territory'
#         ).annotate(
#             streams=Coalesce(Sum('streams'), 0),
#             revenue=Coalesce(Sum('revenue'), Decimal('0.0'))
#         ).order_by('-revenue')
#
#         for stat in territory_stats:
#             revenue = stat['revenue']
#             territory_data.append({
#                 'territory': stat['territory'],
#                 'streams': stat['streams'],
#                 'revenue': revenue,
#                 'percentage': round((revenue / total_revenue_val) * 100, 2) if total_revenue_val > 0 else 0
#             })
#
#         # Prepare response data
#         data = {
#             "total_streams": totals['total_streams'],
#             "total_downloads": totals['total_downloads'],
#             "total_revenue": totals['total_revenue'],
#             "total_usd_revenue": totals['total_usd_revenue'],
#             "currency": "USD",
#             "avg_revenue_per_stream": totals['total_revenue'] / totals['total_streams'] if totals[
#                                                                                                'total_streams'] > 0 else Decimal(
#                 '0.0'),
#             "platform_breakdown": platform_data,
#             "territory_breakdown": territory_data,
#             "total_albums": Album.objects.filter(artist=user).count(),
#             "total_tracks": Track.objects.filter(artist=user).count(),
#             "total_platforms": Platform.objects.count()
#         }
#
#         serializer = DashboardSummarySerializer(data=data)
#         serializer.is_valid(raise_exception=True)
#         return Response(serializer.data)
#
#     def get_date_filter(self, request):
#         """Get date filter parameters from request"""
#         date_filter = {}
#         start_date = request.GET.get('start_date')
#         end_date = request.GET.get('end_date')
#
#         if start_date:
#             try:
#                 date_filter['period_end__gte'] = datetime.strptime(start_date, '%Y-%m-%d').date()
#             except:
#                 pass
#
#         if end_date:
#             try:
#                 date_filter['period_end__lte'] = datetime.strptime(end_date, '%Y-%m-%d').date()
#             except:
#                 pass
#
#         return date_filter
#
#
# class CsvUploadCreateView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, JSONParser]
#
#     def post(self, request):
#         """POST /api/csv-uploads - Upload and process a CSV file with flexible column mapping"""
#         user = request.user
#         csv_file = request.FILES.get('file')
#         column_mapping = request.data.get('column_mapping', {})
#         platform_name = request.data.get('platform_name')  # Optional: specify platform if not in CSV
#
#         if not csv_file:
#             return Response({'error': 'No file provided'}, status=400)
#
#         # Validate column mapping
#         mapping_serializer = CsvColumnMappingSerializer(data=column_mapping)
#         if not mapping_serializer.is_valid():
#             return Response({'error': 'Invalid column mapping', 'details': mapping_serializer.errors}, status=400)
#
#         # Create upload record
#         upload = CsvUpload.objects.create(
#             artist=user,
#             filename=csv_file.name,
#             status='processing',
#             total_rows=0
#         )
#
#         try:
#             # Read CSV file
#             df = pd.read_csv(csv_file)
#             upload.total_rows = len(df)
#             upload.csv_headers = list(df.columns)  # Store original headers
#             upload.save()
#
#             success_count = 0
#             error_count = 0
#             error_messages = []
#             mapping = mapping_serializer.validated_data
#
#             # Get or create platform if specified
#             platform = None
#             if platform_name:
#                 platform, created = Platform.objects.get_or_create(
#                     name=platform_name,
#                     defaults={
#                         'api_name': platform_name.lower().replace(' ', '_'),
#                         'display_name': platform_name
#                     }
#                 )
#
#             for index, row in df.iterrows():
#                 try:
#                     # Extract data using column mapping with fallbacks
#                     row_data = self.extract_row_data(row, mapping, platform_name)
#
#                     if not row_data:
#                         error_count += 1
#                         error_messages.append(f"Row {index + 1}: Missing required data")
#                         continue
#
#                     # Get or create platform (if not already set)
#                     if not platform and row_data.get('platform_name'):
#                         platform, created = Platform.objects.get_or_create(
#                             name=row_data['platform_name'],
#                             defaults={
#                                 'api_name': row_data['platform_name'].lower().replace(' ', '_'),
#                                 'display_name': row_data['platform_name']
#                             }
#                         )
#                     elif not platform:
#                         error_count += 1
#                         error_messages.append(f"Row {index + 1}: Platform not specified")
#                         continue
#
#                     # Get or create album if provided
#                     album = None
#                     if row_data.get('album_title'):
#                         album, created = Album.objects.get_or_create(
#                             artist=user,
#                             title=row_data['album_title'],
#                             defaults={
#                                 'upc': row_data.get('upc'),
#                                 'release_date': row_data.get('release_date')
#                             }
#                         )
#
#                     # Get or create track
#                     track, created = Track.objects.get_or_create(
#                         artist=user,
#                         name=row_data['track_name'],
#                         defaults={
#                             'album': album,
#                             'isrc': row_data.get('isrc'),
#                             'external_id': row_data.get('track_id')
#                         }
#                     )
#
#                     # Parse dates with multiple format support
#                     period_end = self.parse_date(row_data.get('period_end'))
#                     period_start = self.parse_date(row_data.get('period_start'))
#                     report_date = self.parse_date(row_data.get('report_date'))
#
#                     if not period_end:
#                         error_count += 1
#                         error_messages.append(f"Row {index + 1}: Invalid period_end date")
#                         continue
#
#                     if not period_start:
#                         period_start = period_end.replace(day=1)  # Default to month start
#
#                     # Convert revenue to decimal
#                     revenue = self.parse_decimal(row_data.get('revenue', 0))
#                     usd_revenue = revenue  # Default to same as revenue (will need currency conversion later)
#
#                     # Generate unique hash
#                     source_string = f"{user.id}-{track.id}-{platform.id}-{period_end}-{row_data.get('territory', 'US')}-{row_data.get('streams', 0)}-{revenue}"
#                     source_row_hash = hashlib.sha256(source_string.encode()).hexdigest()
#
#                     # Check for duplicates
#                     if not RoyaltyStatement.objects.filter(source_row_hash=source_row_hash).exists():
#                         RoyaltyStatement.objects.create(
#                             artist=user,
#                             track=track,
#                             platform=platform,
#                             upload=upload,
#                             period_start=period_start,
#                             period_end=period_end,
#                             report_date=report_date,
#                             streams=int(row_data.get('streams', 0)),
#                             downloads=int(row_data.get('downloads', 0)),
#                             revenue=revenue,
#                             usd_revenue=usd_revenue,
#                             territory=row_data.get('territory', 'US'),
#                             currency=row_data.get('currency', 'USD'),
#                             quantity=int(row_data.get('quantity', 0)),
#                             unit_price=self.parse_decimal(row_data.get('unit_price', 0)),
#                             source_row_hash=source_row_hash,
#                             original_data=row.to_dict()  # Store original row data
#                         )
#                         success_count += 1
#                     else:
#                         # Skip duplicate
#                         pass
#
#                 except Exception as e:
#                     error_count += 1
#                     error_messages.append(f"Row {index + 1}: {str(e)}")
#                     continue
#
#             # Update upload status
#             upload.success_count = success_count
#             upload.error_count = error_count
#             upload.processed_rows = success_count + error_count
#
#             if error_messages:
#                 upload.error_log = "\n".join(error_messages[:20])  # Limit to first 20 errors
#
#             if upload.processed_rows >= upload.total_rows:
#                 upload.status = 'completed' if error_count == 0 else 'completed_with_errors'
#
#             upload.save()
#
#             response_data = CsvUploadSerializer(upload).data
#             response_data['processing_summary'] = {
#                 'successful_rows': success_count,
#                 'failed_rows': error_count,
#                 'duplicate_rows': upload.total_rows - (success_count + error_count)
#             }
#
#             if error_count > 0:
#                 response_data['error_samples'] = error_messages[:5]
#
#             return Response(response_data, status=201)
#
#         except Exception as e:
#             upload.status = 'failed'
#             upload.error_log = str(e)
#             upload.save()
#             return Response({
#                 'error': 'Failed to process CSV file',
#                 'details': str(e)
#             }, status=500)
#
#     def extract_row_data(self, row, mapping, default_platform=None):
#         """Extract data from row using column mapping with intelligent fallbacks"""
#         data = {}
#
#         # Helper function to get value with fallbacks
#         def get_value(field_name, default=None):
#             # Try mapped column first
#             if field_name in mapping and mapping[field_name] in row:
#                 value = row[mapping[field_name]]
#                 if pd.notna(value):
#                     return value
#
#             # Try common variations
#             variations = [
#                 field_name,
#                 field_name.replace('_', ' ').title(),
#                 field_name.replace('_', ''),
#                 field_name.upper(),
#                 field_name.lower()
#             ]
#
#             for variation in variations:
#                 if variation in row and pd.notna(row[variation]):
#                     return row[variation]
#
#             return default
#
#         # Extract all fields
#         data['track_name'] = get_value('track_name')
#         data['track_id'] = get_value('track_id')
#         data['isrc'] = get_value('isrc')
#         data['platform_name'] = get_value('platform_name', default_platform)
#         data['streams'] = get_value('streams', 0)
#         data['downloads'] = get_value('downloads', 0)
#         data['revenue'] = get_value('revenue', 0)
#         data['currency'] = get_value('currency', 'USD')
#         data['territory'] = get_value('territory', 'US')
#         data['period_start'] = get_value('period_start')
#         data['period_end'] = get_value('period_end')
#         data['report_date'] = get_value('report_date')
#         data['quantity'] = get_value('quantity', 0)
#         data['unit_price'] = get_value('unit_price', 0)
#         data['album_title'] = get_value('album_title')
#         data['album_id'] = get_value('album_id')
#         data['upc'] = get_value('upc')
#
#         return data
#
#     def parse_date(self, date_str):
#         """Parse date from various formats"""
#         if not date_str or pd.isna(date_str):
#             return None
#
#         if isinstance(date_str, (datetime, pd.Timestamp)):
#             return date_str.date()
#
#         date_formats = [
#             '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d',
#             '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d',
#             '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
#         ]
#
#         for fmt in date_formats:
#             try:
#                 return datetime.strptime(str(date_str), fmt).date()
#             except:
#                 continue
#
#         return None
#
#     def parse_decimal(self, value):
#         """Parse decimal from various formats"""
#         if pd.isna(value):
#             return Decimal('0.0')
#
#         if isinstance(value, (int, float, Decimal)):
#             return Decimal(str(value))
#
#         # Remove currency symbols and thousands separators
#         value_str = str(value).replace('$', '').replace(',', '').replace(' ', '')
#
#         try:
#             return Decimal(value_str)
#         except:
#             return Decimal('0.0')
#
#
# class TotalStreamsView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         total = RoyaltyStatement.objects.filter(artist=user).aggregate(
#             total_streams=Sum('streams'))['total_streams'] or 0
#         return Response({'total_streams': total})
#
#
# class TotalRevenueView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         total = RoyaltyStatement.objects.filter(artist=user).aggregate(
#             total_revenue=Sum('revenue'))['total_revenue'] or 0
#         return Response({'total_revenue': float(total), 'currency': 'USD'})
#
#
# class StreamsByPlatformView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         platform_stats = RoyaltyStatement.objects.filter(artist=user).values(
#             'platform__name', 'platform__api_name'
#         ).annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
#                    ).order_by('-total_streams')
#         data = []
#         for stat in platform_stats:
#             data.append({
#                 'platform_name': stat['platform__name'],
#                 'platform_icon': stat['platform__api_name'],
#                 'streams': stat['total_streams'] or 0,
#                 'revenue': float(stat['total_revenue'] or 0)
#             })
#         return Response({'platforms': data})
#
#
# class StreamsOverTimeView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         period = request.GET.get('period', '6months')
#         queryset = RoyaltyStatement.objects.filter(artist=user)
#         trunc_func = TruncWeek('period_end') if period != '1year' else TruncMonth('period_end')
#         time_series_data = queryset.annotate(period_date=trunc_func).values(
#             'period_date').annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
#                                     ).order_by('period_date')
#         formatted_data = []
#         for item in time_series_data:
#             if item['period_date']:
#                 formatted_data.append({
#                     'date': item['period_date'].isoformat(),
#                     'streams': item['total_streams'] or 0,
#                     'revenue': float(item['total_revenue'] or 0)
#                 })
#         serializer = StreamsOverTimeSerializer(formatted_data, many=True)
#         return Response(serializer.data)
#
#
# class TopTracksView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         top_tracks = RoyaltyStatement.objects.filter(artist=user).values(
#             'track__name', 'track__id', 'platform__name'
#         ).annotate(total_streams=Sum('streams'), total_revenue=Sum('revenue')
#                    ).order_by('-total_streams')[:10]
#         data = []
#         for track in top_tracks:
#             data.append({
#                 'track_name': track['track__name'],
#                 'track_id': track['track__id'],
#                 'streams': track['total_streams'] or 0,
#                 'revenue': float(track['total_revenue'] or 0),
#                 'platform': track['platform__name']
#             })
#         serializer = TopTracksSerializer(data, many=True)
#         return Response(serializer.data)
#
#
# class RevenueByPlatformView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         revenue_stats = RoyaltyStatement.objects.filter(artist=user).values(
#             'platform__name').annotate(total_revenue=Sum('revenue')
#                                        ).order_by('-total_revenue')
#         return Response({'revenue_by_platform': list(revenue_stats)})
#
#
# class PlatformListView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         platforms = Platform.objects.all()
#         serializer = PlatformSerializer(platforms, many=True)
#         return Response(serializer.data)
#
#
# class AlbumListView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         albums = Album.objects.filter(artist=user)
#         serializer = AlbumSerializer(albums, many=True)
#         return Response(serializer.data)
#
#
# class TrackListView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         user = request.user
#         tracks = Track.objects.filter(artist=user)
#         serializer = TrackSerializer(tracks, many=True)
#         return Response(serializer.data)
#
#
# class RoyaltyStatementListView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         """GET /api/royalty-statements - List all royalty statements"""
#         user = request.user
#         statements = RoyaltyStatement.objects.filter(artist=user).select_related('track', 'platform')
#         serializer = RoyaltyStatementSerializer(statements, many=True)
#         return Response(serializer.data)
#
#
# class RoyaltyStatementDetailView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, pk):
#         """GET /api/royalty-statements/{id} - Get specific royalty statement"""
#         user = request.user
#         try:
#             statement = RoyaltyStatement.objects.get(id=pk, artist=user)
#             serializer = RoyaltyStatementSerializer(statement)
#             return Response(serializer.data)
#         except RoyaltyStatement.DoesNotExist:
#             return Response({'error': 'Not found'}, status=404)
#
#
# class CsvUploadListView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         """GET /api/csv-uploads - List all CSV uploads for the user"""
#         user = request.user
#         uploads = CsvUpload.objects.filter(artist=user).order_by('-uploaded_at')
#         serializer = CsvUploadSerializer(uploads, many=True)
#         return Response(serializer.data)
#
#
# class CsvUploadDetailView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, pk):
#         """GET /api/csv-uploads/{id} - Get specific CSV upload details"""
#         user = request.user
#         try:
#             upload = CsvUpload.objects.get(id=pk, artist=user)
#             serializer = CsvUploadSerializer(upload)
#             return Response(serializer.data)
#         except CsvUpload.DoesNotExist:
#             return Response({'error': 'Not found'}, status=404)
#
#
# class CsvUploadCreateView(APIView):
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, JSONParser]
#
#     def post(self, request):
#         """POST /api/csv-uploads - Upload and process a CSV file"""
#         user = request.user
#         csv_file = request.FILES.get('file')
#
#         if not csv_file:
#             return Response({'error': 'No file provided'}, status=400)
#
#         # Create upload record
#         upload = CsvUpload.objects.create(
#             artist=user,
#             filename=csv_file.name,
#             status='processing',
#             total_rows=0
#         )
#
#         try:
#             # Process the CSV file
#             df = pd.read_csv(csv_file)
#             upload.total_rows = len(df)
#             upload.save()
#
#             success_count = 0
#             error_count = 0
#             error_messages = []
#
#             for index, row in df.iterrows():
#                 try:
#                     # Extract data from CSV row (adjust column names as needed)
#                     track_name = row.get('track_name', '')
#                     platform_name = row.get('platform', '')
#                     streams = int(row.get('streams', 0))
#                     revenue = float(row.get('revenue', 0.0))
#                     currency = row.get('currency', 'USD')
#                     period_end_str = row.get('period_end', '')
#
#                     # Parse date (handle different formats)
#                     try:
#                         period_end = datetime.strptime(period_end_str, '%Y-%m-%d').date()
#                     except:
#                         period_end = datetime.strptime(period_end_str, '%d/%m/%Y').date()
#
#                     period_start = period_end.replace(day=1)  # Assuming monthly reports
#
#                     # Get or create track
#                     track, created = Track.objects.get_or_create(
#                         artist=user,
#                         name=track_name,
#                         defaults={'name': track_name}
#                     )
#
#                     # Get platform
#                     try:
#                         platform = Platform.objects.get(name__iexact=platform_name)
#                     except Platform.DoesNotExist:
#                         platform = Platform.objects.create(
#                             name=platform_name,
#                             api_name=platform_name.lower().replace(' ', '_')
#                         )
#
#                     # Generate unique hash for this data row to prevent duplicates
#                     source_string = f"{user.id}-{track.id}-{platform.id}-{period_end}-{streams}-{revenue}-{currency}"
#                     source_row_hash = hashlib.sha256(source_string.encode()).hexdigest()
#
#                     # Check for duplicate before creating
#                     if not RoyaltyStatement.objects.filter(source_row_hash=source_row_hash).exists():
#
#                         RoyaltyStatement.objects.create(
#                             artist=user,
#                             track=track,
#                             platform=platform,
#                             upload=upload,
#                             period_start=period_start,
#                             period_end=period_end,
#                             streams=streams,
#                             revenue=revenue,
#                             currency=currency,
#                             source_row_hash=source_row_hash
#                         )
#                         success_count += 1
#                     else:
#                         pass
#
#                 except Exception as e:
#                     error_count += 1
#                     error_messages.append(f"Row {index + 1}: {str(e)}")
#                     continue
#
#             # Update upload status
#             upload.success_count = success_count
#             upload.error_count = error_count
#             upload.processed_rows = success_count + error_count
#
#             if error_messages:
#                 upload.error_log = "\n".join(error_messages[:10])
#
#             if upload.processed_rows >= upload.total_rows:
#                 upload.status = 'completed' if error_count == 0 else 'completed_with_errors'
#
#             upload.save()
#
#             response_data = {
#                 'message': f'Processed {success_count} rows successfully',
#                 'errors': error_count,
#                 'upload_id': upload.id
#             }
#
#             if error_count > 0:
#                 response_data['error_samples'] = error_messages[:3]  # Show first 3 errors
#
#             serializer = CsvUploadSerializer(upload)
#             return Response(serializer.data, status=201)
#
#         except Exception as e:
#             # Mark upload as failed
#             upload.status = 'failed'
#             upload.error_log = str(e)
#             upload.save()
#
#             return Response({
#                 'error': 'Failed to process CSV file',
#                 'details': str(e)
#             }, status=500)

# Add other view classes here (they remain mostly the same but can be enhanced)
# [Keep your existing TotalStreamsView, TotalRevenueView, etc. but add date filtering]