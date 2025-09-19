from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('artist/dashboard-summary', views.DashboardSummaryView.as_view(), name='dashboard-summary'),

    # Stream endpoints
    path('streams/total', views.TotalStreamsView.as_view(), name='total-streams'),
    path('streams/by-platform', views.StreamsByPlatformView.as_view(), name='streams-by-platform'),
    path('streams/over-time', views.StreamsOverTimeView.as_view(), name='streams-over-time'),
    path('streams/top-tracks', views.TopTracksView.as_view(), name='top-tracks'),

    # Revenue endpoints
    path('revenue/total', views.TotalRevenueView.as_view(), name='total-revenue'),
    path('revenue/by-platform', views.RevenueByPlatformView.as_view(), name='revenue-by-platform'),

    # Platform endpoints
    path('platforms', views.PlatformListView.as_view(), name='platform-list'),

    # Content endpoints
    path('albums', views.AlbumListView.as_view(), name='album-list'),
    path('tracks', views.TrackListView.as_view(), name='track-list'),

    # Royalty Statements
    path('royalty-statements', views.RoyaltyStatementListView.as_view(), name='royalty-statement-list'),
    path('royalty-statements/<int:pk>', views.RoyaltyStatementDetailView.as_view(), name='royalty-statement-detail'),

    # CSV Uploads
    path('csv-uploads', views.CsvUploadListView.as_view(), name='csv-upload-list'),
    path('csv-uploads/<int:pk>', views.CsvUploadDetailView.as_view(), name='csv-upload-detail'),
    path('csv-uploads/upload', views.CsvUploadCreateView.as_view(), name='csv-upload-create'),
]

# from django.urls import path
# from . import views
#
# urlpatterns = [
#     # Dashboard
#     path('artist/dashboard-summary', views.DashboardSummaryView.as_view(), name='dashboard-summary'),
#
#     # Stream endpoints
#     path('streams/total', views.TotalStreamsView.as_view(), name='total-streams'),
#     path('streams/by-platform', views.StreamsByPlatformView.as_view(), name='streams-by-platform'),
#     path('streams/over-time', views.StreamsOverTimeView.as_view(), name='streams-over-time'),
#     path('streams/top-tracks', views.TopTracksView.as_view(), name='top-tracks'),
#
#     # Revenue endpoints
#     path('revenue/total', views.TotalRevenueView.as_view(), name='total-revenue'),
#     path('revenue/by-platform', views.RevenueByPlatformView.as_view(), name='revenue-by-platform'),
#
#     # Platform endpoints
#     path('platforms', views.PlatformListView.as_view(), name='platform-list'),
#
#     # Content endpoints
#     path('albums', views.AlbumListView.as_view(), name='album-list'),
#     path('tracks', views.TrackListView.as_view(), name='track-list'),
#
#     # Royalty Statements
#     path('royalty-statements', views.RoyaltyStatementListView.as_view(), name='royalty-statement-list'),
#     path('royalty-statements/<uuid:pk>', views.RoyaltyStatementDetailView.as_view(), name='royalty-statement-detail'),
#
#     # CSV Uploads
#     path('csv-uploads', views.CsvUploadListView.as_view(), name='csv-upload-list'),
#     path('csv-uploads/<uuid:pk>', views.CsvUploadDetailView.as_view(), name='csv-upload-detail'),
#     path('csv-uploads/upload', views.CsvUploadCreateView.as_view(), name='csv-upload-create'),
#
#     # Data management
#     path('data/clear', views.ClearDataView.as_view(), name='clear-data'),
#     path('data/export', views.ExportDataView.as_view(), name='export-data'),
# ]