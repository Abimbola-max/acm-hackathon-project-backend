from django.contrib import admin
from .models import PlatformInsight

@admin.register(PlatformInsight)
class PlatformInsightAdmin(admin.ModelAdmin):
    list_display = ('artist', 'platform', 'track_name', 'insight_type', 'value', 'timestamp')
    list_filter = ('platform', 'insight_type', 'timestamp')
    search_fields = ('artist__username', 'track_name')