"""
Music Recommendation System using Flask and Spotify API
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv
import random

# Custom recommendation engine
def get_custom_recommendations(seed_tracks, seed_artists, limit=10):
    """
    Custom recommendation algorithm based on audio features analysis.
    Analyzes selected tracks and finds similar songs based on:
    - Danceability
    - Energy
    - Valence (positivity)
    - Acousticness
    - Genre/Artist similarity
    """
    try:
        # Get audio features for seed tracks
        seed_features = []
        seed_track_objects = []
        
        if seed_tracks:
            # Get full track objects
            for track_id in seed_tracks[:5]:
                try:
                    track = sp.track(track_id)
                    seed_track_objects.append(track)
                except:
                    continue
            
            # Get audio features
            try:
                features = sp.audio_features(seed_tracks[:5])
                seed_features = [f for f in features if f]
            except:
                pass
        
        if not seed_track_objects:
            return []
        
        # Calculate average preferences from seed tracks
        avg_preferences = {}
        if seed_features:
            for feature in ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']:
                values = [f.get(feature, 0) for f in seed_features if f.get(feature) is not None]
                avg_preferences[feature] = sum(values) / len(values) if values else 0.5
        
        # Get artists and genres from seed tracks
        seed_artists_names = set()
        seed_genres = set()
        
        for track in seed_track_objects:
            for artist in track.get('artists', []):
                artist_name = artist.get('name', '')
                seed_artists_names.add(artist_name)
                
                # Try to get artist genres
                try:
                    artist_info = sp.artist(artist.get('id'))
                    for genre in artist_info.get('genres', []):
                        seed_genres.add(genre)
                except:
                    pass
        
        # Search strategy: Build queries based on detected preferences
        search_queries = []
        
        # Add artist-based searches
        for artist in list(seed_artists_names)[:3]:
            search_queries.append(f'artist:"{artist}"')
        
        # Add genre-based searches if we have genres
        if seed_genres:
            for genre in list(seed_genres)[:2]:
                search_queries.append(f'genre:"{genre}"')
        
        # Add feature-based search terms
        if avg_preferences.get('energy', 0.5) > 0.7:
            search_queries.append('workout OR party OR upbeat')
        elif avg_preferences.get('energy', 0.5) < 0.3:
            search_queries.append('chill OR relax OR acoustic')
        
        if avg_preferences.get('danceability', 0.5) > 0.7:
            search_queries.append('dance OR edm')
        
        if avg_preferences.get('acousticness', 0.5) > 0.5:
            search_queries.append('acoustic OR unplugged')
        
        # Collect tracks from various searches
        all_tracks = []
        seen_ids = set(t['id'] for t in seed_track_objects)
        
        for query in search_queries[:5]:  # Limit to 5 searches
            try:
                results = sp.search(q=query, type='track', limit=10)
                for track in results.get('tracks', {}).get('items', []):
                    track_id = track.get('id')
                    if track_id and track_id not in seen_ids:
                        # Calculate similarity score
                        similarity = 0
                        
                        # Artist match bonus
                        track_artists = [a.get('name', '') for a in track.get('artists', [])]
                        if any(a in seed_artists_names for a in track_artists):
                            similarity += 0.3
                        
                        # Popularity consideration (prefer similar popularity)
                        seed_popularity = sum(t.get('popularity', 50) for t in seed_track_objects) / len(seed_track_objects)
                        track_pop = track.get('popularity', 50)
                        popularity_diff = abs(seed_popularity - track_pop) / 100
                        similarity += (1 - popularity_diff) * 0.2
                        
                        all_tracks.append({
                            'track': track,
                            'similarity': similarity,
                            'source': 'custom'
                        })
                        seen_ids.add(track_id)
            except:
                continue
        
        # Sort by similarity score
        all_tracks.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top tracks
        result_tracks = []
        for item in all_tracks[:limit]:
            track = item['track']
            result_tracks.append({
                'id': track.get('id'),
                'name': track.get('name'),
                'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
                'album': track.get('album', {}).get('name'),
                'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                'preview_url': track.get('preview_url'),
                'spotify_url': track.get('external_urls', {}).get('spotify'),
                'popularity': track.get('popularity'),
                'duration_ms': track.get('duration_ms'),
                'similarity_score': round(item['similarity'] * 100, 1)
            })
        
        return result_tracks
    
    except Exception as e:
        print(f"Custom recommendation error: {e}")
        return []

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

# Initialize Spotipy client
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager,
    retries=3,
    status_forcelist=[429, 500, 502, 503, 504]
)


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/search')
def search_tracks():
    """Search for tracks on Spotify"""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    market = request.args.get('market', 'US')  # Default to US, allow other markets
    
    # Spotify API limit constraints (must be between 1 and 50)
    limit = int(limit)
    if limit < 1:
        limit = 10
    elif limit > 50:
        limit = 50
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    try:
        results = sp.search(q=query, type='track', limit=limit, market=market)
        tracks = []
        
        for track in results['tracks']['items']:
            tracks.append({
                'id': track.get('id'),
                'name': track.get('name'),
                'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
                'album': track.get('album', {}).get('name'),
                'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                'preview_url': track.get('preview_url'),
                'spotify_url': track.get('external_urls', {}).get('spotify'),
                'popularity': track.get('popularity'),
                'duration_ms': track.get('duration_ms')
            })
        
        return jsonify({'tracks': tracks})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations')
def get_recommendations():
    """Get track recommendations based on seed tracks"""
    seed_tracks = request.args.get('seed_tracks', '')
    seed_artists = request.args.get('seed_artists', '')
    seed_genres = request.args.get('seed_genres', '')
    limit = request.args.get('limit', 10, type=int)
    
    # Spotify allows max 5 seeds total across all types
    try:
        kwargs = {'limit': limit}
        
        # Build seeds - limit to max 5 total
        all_seeds = []
        
        if seed_tracks:
            track_ids = seed_tracks.split(',')[:5]  # Max 5 tracks
            kwargs['seed_tracks'] = track_ids
            all_seeds.extend(track_ids)
        
        # Only add artists if we have room for more seeds
        if seed_artists and len(all_seeds) < 5:
            artist_ids = seed_artists.split(',')[:5-len(all_seeds)]
            kwargs['seed_artists'] = artist_ids
            all_seeds.extend(artist_ids)
        
        # Only add genres if we have room for more seeds
        if seed_genres and len(all_seeds) < 5:
            genre_list = seed_genres.split(',')[:5-len(all_seeds)]
            kwargs['seed_genres'] = genre_list
        
        # Try recommendations API
        try:
            results = sp.recommendations(**kwargs)
            
            tracks = []
            for track in results.get('tracks', []):
                tracks.append({
                    'id': track.get('id'),
                    'name': track.get('name'),
                    'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
                    'album': track.get('album', {}).get('name'),
                    'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                    'preview_url': track.get('preview_url'),
                    'spotify_url': track.get('external_urls', {}).get('spotify'),
                    'popularity': track.get('popularity'),
                    'duration_ms': track.get('duration_ms')
                })
            
            if tracks:
                return jsonify({'tracks': tracks})
        except Exception as api_error:
            print(f"Recommendations API error: {api_error}")
        
        # Use custom recommendation engine
        custom_tracks = []
        if seed_tracks:
            track_ids = seed_tracks.split(',')[:5]
            artist_ids = seed_artists.split(',')[:5] if seed_artists else []
            custom_tracks = get_custom_recommendations(track_ids, artist_ids, limit)
        
        if custom_tracks:
            return jsonify({'tracks': custom_tracks, 'custom': True})
        
        # Last resort fallback
        return jsonify({'tracks': [], 'error': 'No recommendations available'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<track_id>')
def get_track_details(track_id):
    """Get detailed information about a specific track"""
    try:
        track = sp.track(track_id)
        
        # Get audio features (may fail with 403 for some tracks)
        try:
            audio_features = sp.audio_features([track_id])[0]
        except:
            audio_features = None
        
        track_data = {
            'id': track.get('id'),
            'name': track.get('name'),
            'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
            'artists_details': [{'id': a.get('id'), 'name': a.get('name')} for a in track.get('artists', [])],
            'album': track.get('album', {}).get('name'),
            'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
            'preview_url': track.get('preview_url'),
            'spotify_url': track.get('external_urls', {}).get('spotify'),
            'popularity': track.get('popularity'),
            'duration_ms': track.get('duration_ms'),
            'explicit': track.get('explicit'),
            'release_date': track.get('album', {}).get('release_date'),
            'audio_features': {
                'danceability': audio_features.get('danceability'),
                'energy': audio_features.get('energy'),
                'key': audio_features.get('key'),
                'loudness': audio_features.get('loudness'),
                'mode': audio_features.get('mode'),
                'speechiness': audio_features.get('speechiness'),
                'acousticness': audio_features.get('acousticness'),
                'instrumentalness': audio_features.get('instrumentalness'),
                'liveness': audio_features.get('liveness'),
                'valence': audio_features.get('valence'),
                'tempo': audio_features.get('tempo')
            } if audio_features else None
        }
        
        return jsonify(track_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/artist/<artist_id>')
def get_artist_details(artist_id):
    """Get detailed information about an artist"""
    try:
        artist = sp.artist(artist_id)
        top_tracks = sp.artist_top_tracks(artist_id)
        
        artist_data = {
            'id': artist.get('id'),
            'name': artist.get('name'),
            'genres': artist.get('genres', []),
            'popularity': artist.get('popularity'),
            'followers': artist.get('followers', {}).get('total'),
            'image': artist.get('images', [{}])[0].get('url') if artist.get('images') else None,
            'spotify_url': artist.get('external_urls', {}).get('spotify'),
            'top_tracks': [{
                'id': track.get('id'),
                'name': track.get('name'),
                'album': track.get('album', {}).get('name'),
                'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                'preview_url': track.get('preview_url'),
                'spotify_url': track.get('external_urls', {}).get('spotify')
            } for track in top_tracks.get('tracks', [])[:5]]
        }
        
        return jsonify(artist_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/genres')
def get_available_genres():
    """Get list of available genre seeds for recommendations"""
    try:
        genres = sp.recommendation_genre_seeds()
        return jsonify({'genres': genres['genres']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/featured-playlists')
def get_featured_playlists():
    """Get Spotify's featured playlists"""
    try:
        # Try the featured_playlists endpoint first
        try:
            results = sp.featured_playlists(limit=10)
            playlists = []
            
            for playlist in results.get('playlists', {}).get('items', []):
                playlists.append({
                    'id': playlist.get('id'),
                    'name': playlist.get('name'),
                    'description': playlist.get('description'),
                    'image': playlist.get('images', [{}])[0].get('url') if playlist.get('images') else None,
                    'spotify_url': playlist.get('external_urls', {}).get('spotify'),
                    'tracks_total': playlist.get('tracks', {}).get('total')
                })
            
            if playlists:
                return jsonify({'playlists': playlists})
        except:
            pass
        
        # Fallback: Search for popular playlists
        search_queries = ['pop', 'rock', 'hip hop', 'workout', 'party']
        all_playlists = []
        
        for query in search_queries:
            try:
                results = sp.search(q=query, type='playlist', limit=2)
                for playlist in results.get('playlists', {}).get('items', []):
                    all_playlists.append({
                        'id': playlist.get('id'),
                        'name': playlist.get('name'),
                        'description': playlist.get('description', ''),
                        'image': playlist.get('images', [{}])[0].get('url') if playlist.get('images') else None,
                        'spotify_url': playlist.get('external_urls', {}).get('spotify'),
                        'tracks_total': playlist.get('tracks', {}).get('total', 0)
                    })
            except:
                continue
        
        return jsonify({'playlists': all_playlists[:10]})
    
    except Exception as e:
        return jsonify({'playlists': [], 'error': str(e)}), 200


@app.route('/api/new-releases')
def get_new_releases():
    """Get new releases - uses search for popular recent tracks as fallback"""
    try:
        # Try the new_releases endpoint first
        try:
            results = sp.new_releases(limit=10)
            albums = []
            
            for album in results.get('albums', {}).get('items', []):
                albums.append({
                    'id': album.get('id'),
                    'name': album.get('name'),
                    'artist': ', '.join([artist.get('name', '') for artist in album.get('artists', [])]),
                    'image': album.get('images', [{}])[0].get('url') if album.get('images') else None,
                    'spotify_url': album.get('external_urls', {}).get('spotify'),
                    'release_date': album.get('release_date'),
                    'total_tracks': album.get('total_tracks')
                })
            
            if albums:
                return jsonify({'albums': albums})
        except:
            pass
        
        # Fallback: Search for popular tracks from 2024-2025
        search_queries = ['year:2024', 'year:2025', 'tag:new']
        all_tracks = []
        
        for query in search_queries:
            try:
                results = sp.search(q=query, type='track', limit=5)
                for track in results.get('tracks', {}).get('items', []):
                    all_tracks.append({
                        'id': track.get('album', {}).get('id'),
                        'name': track.get('album', {}).get('name'),
                        'artist': ', '.join([artist.get('name', '') for artist in track.get('artists', [])]),
                        'image': track.get('album', {}).get('images', [{}])[0].get('url') if track.get('album', {}).get('images') else None,
                        'spotify_url': track.get('album', {}).get('external_urls', {}).get('spotify') or track.get('external_urls', {}).get('spotify'),
                        'release_date': track.get('album', {}).get('release_date', '2024'),
                        'total_tracks': track.get('album', {}).get('total_tracks', 1)
                    })
            except:
                continue
        
        # Remove duplicates by ID
        seen = set()
        unique_tracks = []
        for track in all_tracks:
            if track['id'] and track['id'] not in seen:
                seen.add(track['id'])
                unique_tracks.append(track)
        
        return jsonify({'albums': unique_tracks[:10]})
    
    except Exception as e:
        return jsonify({'albums': [], 'error': str(e)}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)