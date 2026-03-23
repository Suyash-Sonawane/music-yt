# Music Recommendation System

A full-stack music recommendation application built with Flask backend and Spotify Web API integration.

## Architecture

```
Frontend (HTML/CSS/JS)  →  Backend (Python Flask)  →  Spotify API (Spotipy)  →  Spotify Web API
```

## Features

- 🔍 **Search**: Search for songs, artists, and albums on Spotify
- 🎯 **Recommendations**: Get personalized track recommendations based on selected songs
- 🎵 **Audio Features**: View detailed audio analysis (danceability, energy, valence, etc.)
- 🔥 **Featured Playlists**: Browse Spotify's featured playlists
- 🆕 **New Releases**: Discover the latest album releases
- ▶️ **Preview Playback**: Play 30-second track previews directly in the browser
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Project Structure

```
.
├── app.py                  # Flask backend application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
├── static/
│   ├── style.css          # Frontend styles
│   └── script.js          # Frontend JavaScript
└── templates/
    └── index.html         # Main HTML template
```

## Setup Instructions

### 1. Clone/Create the Project

Ensure all project files are in your workspace directory.

### 2. Create Spotify Developer Account

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in the app details:
   - App name: Music Recommendation System
   - App description: Personal music recommendation app
   - Redirect URI: http://localhost:5000/callback (not used but required)
5. Check the Developer Terms of Service checkbox
6. Click "Create"
7. Note down your `Client ID` and `Client Secret`

### 3. Set Up Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Spotify credentials:
   ```
   SPOTIFY_CLIENT_ID=your_actual_client_id
   SPOTIFY_CLIENT_SECRET=your_actual_client_secret
   ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at: **http://localhost:5000**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application page |
| `/api/search` | GET | Search for tracks |
| `/api/recommendations` | GET | Get track recommendations |
| `/api/track/<id>` | GET | Get track details with audio features |
| `/api/artist/<id>` | GET | Get artist details |
| `/api/genres` | GET | Get available genre seeds |
| `/api/featured-playlists` | GET | Get featured playlists |
| `/api/new-releases` | GET | Get new album releases |

### Query Parameters

**Search:**
- `q` (required): Search query
- `limit`: Number of results (default: 10)

**Recommendations:**
- `seed_tracks`: Comma-separated track IDs
- `seed_artists`: Comma-separated artist IDs
- `seed_genres`: Comma-separated genre names
- `limit`: Number of recommendations (default: 20)
- `target_danceability`: Target danceability (0-1)
- `target_energy`: Target energy (0-1)
- `target_popularity`: Target popularity (0-100)

## Usage Guide

### Getting Recommendations

1. Go to the "Search Results" tab
2. Enter a song or artist name in the search box
3. Click "Search"
4. Click "Select" on tracks you like (up to 5 tracks)
5. Go to the "Recommendations" tab
6. Click "Get Recommendations"
7. Browse and click on tracks for more details

### Viewing Track Details

Click on any track card to see:
- Full track information
- Album details
- Audio features analysis
- Direct link to Spotify
- 30-second preview (if available)

## Technologies Used

### Backend
- **Flask**: Python web framework
- **Spotipy**: Spotify Web API Python wrapper
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS variables
- **Vanilla JavaScript**: No framework dependencies

### External APIs
- **Spotify Web API**: Music data and recommendations

## Troubleshooting

### Common Issues

**"No module named 'spotipy'"**
```bash
pip install spotipy
```

**"Authentication error"**
- Check that your `.env` file exists and contains valid credentials
- Ensure there are no extra spaces in your Client ID/Secret

**"No search results"**
- Check your internet connection
- Verify your Spotify API credentials are valid
- Try different search terms

**"Recommendations not loading"**
- Make sure you've selected at least one track
- Select up to 5 tracks for best results

## Development

### Running in Debug Mode

The application runs in debug mode by default. For production:

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Adding New Features

The modular structure makes it easy to add:
- User authentication for personalized recommendations
- Playlist creation/editing
- More audio feature visualizations
- Export recommendations to Spotify

## License

This project is for educational purposes. Please respect Spotify's [Terms of Service](https://developer.spotify.com/terms).

## Credits

- Music data provided by [Spotify](https://spotify.com)
- Icons and design inspired by Spotify's interface