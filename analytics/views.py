from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import RoyaltyStatement, Platform
from .serializers import DashboardSummarySerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """GET /api/artist/dashboard-summary"""
    user = request.user

    totals = RoyaltyStatement.objects.filter(artist=user).aggregate(
        total_streams=Sum('streams'),
        total_revenue=Sum('revenue')
    )


    platform_data = []
    platforms = Platform.objects.all()

    for platform in platforms:
        platform_stats = RoyaltyStatement.objects.filter(
            artist=user,
            platform=platform
        ).aggregate(streams=Sum('streams'), revenue=Sum('revenue'))


        if platform_stats['streams']:
            platform_data.append({
                'platform_name': platform.name,
                'platform_icon': platform.api_name,
                'streams': platform_stats['streams'],
                'revenue': platform_stats['revenue'] or 0,
                'percentage': 0  # We'll calculate this next
            })


    total_streams_val = totals['total_streams'] or 1
    for platform in platform_data:
        platform['percentage'] = round((platform['streams'] / total_streams_val) * 100)

    # 4. Build the response
    data = {
        "total_streams": totals['total_streams'] or 0,
        "total_revenue": totals['total_revenue'] or 0,
        "currency": "USD",  # For now
        "platform_breakdown": platform_data
    }


    serializer = DashboardSummarySerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_streams(request):
    """GET /api/streams/total"""
    user = request.user
    total = RoyaltyStatement.objects.filter(artist=user).aggregate(
        total_streams=Sum('streams')
    )['total_streams'] or 0
    return Response({'total_streams': total})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_revenue(request):
    """GET /api/revenue/total"""
    user = request.user
    total = RoyaltyStatement.objects.filter(artist=user).aggregate(
        total_revenue=Sum('revenue')
    )['total_revenue'] or 0
    return Response({'total_revenue': float(total), 'currency': 'USD'})