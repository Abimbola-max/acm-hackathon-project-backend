from django.contrib import admin
from .models import Platform, Album, Track, RoyaltyStatement, CsvUpload


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'api_name')

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'created_at')
    list_filter = ('release_date', 'created_at')
    search_fields = ('title', 'artist__username')
    raw_id_fields = ('artist',)

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'artist', 'album', 'track_number', 'created_at')
    list_filter = ('created_at', 'album')
    search_fields = ('name', 'artist__username', 'album__title')
    raw_id_fields = ('artist', 'album')

@admin.register(RoyaltyStatement)
class RoyaltyStatementAdmin(admin.ModelAdmin):
    list_display = ('track', 'platform', 'period_end', 'streams', 'revenue', 'currency')
    list_filter = ('platform', 'period_end', 'currency')
    search_fields = ('track__name', 'platform__name')
    raw_id_fields = ('artist', 'track', 'platform')

@admin.register(CsvUpload)
class CsvUploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'artist', 'status', 'uploaded_at', 'success_count', 'error_count')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('filename', 'artist__username')
    readonly_fields = ('uploaded_at',)