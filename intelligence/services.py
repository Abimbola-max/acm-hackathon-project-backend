import requests
import base64
import pandas as pd
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import PlatformInsight


class APIConfig:
    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_BASE = "https://api.spotify.com/v1"
    DEEZER_API_BASE = "https://api.deezer.com"
    APPLE_MUSIC_API_BASE = "https://itunes.apple.com/search"
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def get_spotify_access_token():
    """
    Requests an access token from the Spotify API using client credentials.
    """
    auth_string = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(APIConfig.SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting Spotify token: {e}")
        return None



def fetch_spotify_artist_data(access_token, artist_id):
    """
    Fetches top tracks and artist data from Spotify API.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get artist info first to get name and popularity
    artist_url = f"{APIConfig.SPOTIFY_API_BASE}/artists/{artist_id}"
    try:
        artist_response = requests.get(artist_url, headers=headers, timeout=10)
        artist_response.raise_for_status()
        artist_data = artist_response.json()
        artist_name = artist_data.get('name', 'Unknown Artist')
        artist_popularity = artist_data.get('popularity', 0)
    except requests.exceptions.RequestException:
        artist_name = 'Unknown Artist'
        artist_popularity = 0

    # Get top tracks
    top_tracks_url = f"{APIConfig.SPOTIFY_API_BASE}/artists/{artist_id}/top-tracks?market=US"
    try:
        tracks_response = requests.get(top_tracks_url, headers=headers, timeout=10)
        tracks_response.raise_for_status()
        tracks_data = tracks_response.json()

        tracks = []
        for track in tracks_data.get('tracks', []):
            tracks.append({
                'track_name': track.get('name'),
                'spotify_popularity': track.get('popularity', 0),
                'duration_ms': track.get('duration_ms', 0),
                'album_name': track.get('album', {}).get('name'),
                'explicit': track.get('explicit', False),
                'track_id': track.get('id')
            })

        return {
            'artist_name': artist_name,
            'artist_popularity': artist_popularity,
            'tracks': tracks
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Spotify tracks: {e}")
        return {'artist_name': artist_name, 'tracks': []}


def fetch_deezer_artist_data(artist_name):
    """
    Fetches artist data and top tracks from Deezer API.
    """
    # Search for artist
    search_url = f"{APIConfig.DEEZER_API_BASE}/search/artist?q={artist_name}"
    try:
        search_response = requests.get(search_url, timeout=10)
        search_response.raise_for_status()
        search_data = search_response.json()

        if not search_data.get('data'):
            return {'tracks': []}

        artist_id = search_data['data'][0]['id']
        artist_name = search_data['data'][0]['name']

    except requests.exceptions.RequestException:
        return {'tracks': []}

    # Get top tracks
    top_tracks_url = f"{APIConfig.DEEZER_API_BASE}/artist/{artist_id}/top?limit=50"
    try:
        tracks_response = requests.get(top_tracks_url, timeout=10)
        tracks_response.raise_for_status()
        tracks_data = tracks_response.json()

        tracks = []
        for track in tracks_data.get('data', []):
            tracks.append({
                'track_name': track.get('title'),
                'deezer_rank': track.get('rank', 0),
                'duration': track.get('duration', 0),
                'album_title': track.get('album', {}).get('title'),
                'track_id': track.get('id')
            })

        return {
            'artist_name': artist_name,
            'tracks': tracks
        }
    except requests.exceptions.RequestException:
        return {'artist_name': artist_name, 'tracks': []}


def fetch_apple_music_data(artist_name):
    """
    Fetches artist data from iTunes Search API (Apple Music).
    """
    params = {
        'term': artist_name,
        'country': 'us',
        'media': 'music',
        'entity': 'song',
        'limit': 50
    }

    try:
        response = requests.get(APIConfig.APPLE_MUSIC_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        tracks = []
        for track in data.get('results', []):
            if artist_name.lower() in track.get('artistName', '').lower():
                tracks.append({
                    'track_name': track.get('trackName'),
                    'collection_name': track.get('collectionName'),
                    'duration_ms': track.get('trackTimeMillis', 0),
                    'genre': track.get('primaryGenreName'),
                    'release_date': track.get('releaseDate'),
                    'track_id': track.get('trackId')
                })

        return {'tracks': tracks}
    except requests.exceptions.RequestException:
        return {'tracks': []}


def fetch_youtube_data(api_key, artist_name):
    """
    Fetches artist channel data and video statistics from YouTube API.
    """
    # This is a simplified version. Full implementation would require
    # channel discovery, playlist scanning, and video statistics collection.
    # For now, we'll return a placeholder.
    print(f"YouTube API implementation would go here for {artist_name}")
    return {'tracks': []}



def analyze_and_store_artist_data(artist_user, artist_name, spotify_artist_id=None):
    """
    Main function to orchestrate data fetching, analysis, and storage for an artist.
    """
    # Fetch data from all platforms
    spotify_access_token = get_spotify_access_token()

    platform_data = {}

    if spotify_access_token and spotify_artist_id:
        platform_data['spotify'] = fetch_spotify_artist_data(spotify_access_token, spotify_artist_id)

    platform_data['deezer'] = fetch_deezer_artist_data(artist_name)
    platform_data['apple_music'] = fetch_apple_music_data(artist_name)

    if hasattr(settings, 'YOUTUBE_API_KEY') and settings.YOUTUBE_API_KEY:
        platform_data['youtube'] = fetch_youtube_data(settings.YOUTUBE_API_KEY, artist_name)

    # Process and store insights
    for platform, data in platform_data.items():
        if platform == 'spotify' and data['tracks']:
            process_spotify_data(artist_user, data)
        elif platform == 'deezer' and data['tracks']:
            process_deezer_data(artist_user, data)
        elif platform == 'apple_music' and data['tracks']:
            process_apple_music_data(artist_user, data)

    return True


def process_spotify_data(artist_user, data):
    """Process and store Spotify insights."""
    for track in data['tracks']:
        # Store popularity score
        PlatformInsight.objects.create(
            artist=artist_user,
            platform='spotify',
            track_name=track['track_name'],
            insight_type='popularity',
            value=track['spotify_popularity']
        )

        # You could add more Spotify-specific insights here
        # For example: duration, explicitness, etc.


def process_deezer_data(artist_user, data):
    """Process and store Deezer insights."""
    for track in data['tracks']:
        PlatformInsight.objects.create(
            artist=artist_user,
            platform='deezer',
            track_name=track['track_name'],
            insight_type='rank',
            value=track['deezer_rank']
        )


def process_apple_music_data(artist_user, data):
    """Process and store Apple Music insights."""
    for track in data['tracks']:
        # Store release date information for recency analysis
        if track.get('release_date'):
            try:
                release_date = datetime.fromisoformat(track['release_date'].replace('Z', '+00:00'))
                days_since_release = (timezone.now() - release_date).days
                if days_since_release > 0:
                    PlatformInsight.objects.create(
                        artist=artist_user,
                        platform='apple_music',
                        track_name=track['track_name'],
                        insight_type='days_since_release',
                        value=days_since_release
                    )
            except (ValueError, TypeError):
                pass


def generate_artist_report(artist_user):
    """
    Generates a comprehensive report of the artist's performance across platforms.
    """
    insights = PlatformInsight.objects.filter(artist=artist_user)

    report = {
        'summary': {
            'total_tracks_tracked': insights.values('track_name').distinct().count(),
            'platforms_available': list(insights.values_list('platform', flat=True).distinct()),
            'latest_update': insights.latest('timestamp').timestamp if insights.exists() else None
        },
        'by_platform': {},
        'top_performers': {}
    }

    # Group insights by platform
    for platform in report['summary']['platforms_available']:
        platform_insights = insights.filter(platform=platform)
        report['by_platform'][platform] = {
            'tracks_tracked': platform_insights.values('track_name').distinct().count(),
            'latest_data': platform_insights.latest('timestamp').timestamp if platform_insights.exists() else None
        }

    return report