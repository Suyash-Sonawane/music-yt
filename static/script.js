/**
 * Music Recommendation System - Frontend JavaScript
 */

// State management
const state = {
    searchResults: [],
    selectedSeeds: [],
    recommendations: [],
    featuredPlaylists: [],
    newReleases: [],
    currentTrack: null
};

// DOM Elements
const elements = {
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    marketSelect: document.getElementById('marketSelect'),
    searchResultsGrid: document.getElementById('searchResultsGrid'),
    selectedSeeds: document.getElementById('selectedSeeds'),
    getRecommendationsBtn: document.getElementById('getRecommendationsBtn'),
    recommendationsGrid: document.getElementById('recommendationsGrid'),
    featuredGrid: document.getElementById('featuredGrid'),
    newReleasesGrid: document.getElementById('newReleasesGrid'),
    trackModal: document.getElementById('trackModal'),
    modalContent: document.getElementById('modalContent'),
    audioPlayer: document.getElementById('audioPlayer'),
    audioElement: document.getElementById('audioElement'),
    nowPlaying: document.getElementById('nowPlaying'),
    closePlayer: document.getElementById('closePlayer'),
    loading: document.getElementById('loading'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadFeaturedPlaylists();
    loadNewReleases();
});

// Event Listeners
function initializeEventListeners() {
    // Search
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // Tabs
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Recommendations
    elements.getRecommendationsBtn.addEventListener('click', getRecommendations);

    // Modal
    document.querySelector('.close-btn').addEventListener('click', closeModal);
    elements.trackModal.addEventListener('click', (e) => {
        if (e.target === elements.trackModal) closeModal();
    });

    // Audio Player
    elements.closePlayer.addEventListener('click', closeAudioPlayer);

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeAudioPlayer();
        }
    });
}

// Search functionality
async function handleSearch() {
    const query = elements.searchInput.value.trim();
    if (!query) return;

    const market = elements.marketSelect.value;
    showLoading();
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10&market=${market}`);
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }

        state.searchResults = data.tracks;
        renderSearchResults();
        switchTab('search-results');
    } catch (error) {
        showError('Failed to search tracks');
        console.error('Search error:', error);
    } finally {
        hideLoading();
    }
}

// Render search results
function renderSearchResults() {
    if (state.searchResults.length === 0) {
        elements.searchResultsGrid.innerHTML = '<p class="empty-state">No results found</p>';
        return;
    }

    elements.searchResultsGrid.innerHTML = state.searchResults.map(track => `
        <div class="track-card" data-track-id="${track.id}">
            ${track.image 
                ? `<img src="${track.image}" alt="${track.name}" class="track-image">`
                : `<div class="track-image-placeholder">No Image</div>`
            }
            <div class="track-info">
                <h3>${escapeHtml(track.name)}</h3>
                <p>${escapeHtml(track.artist)}</p>
                ${track.preview_url 
                    ? `<small style="color: var(--primary-color);">♪ Preview available</small>`
                    : `<small style="color: var(--text-secondary);">No preview</small>`
                }
            </div>
            <div class="track-actions">
                <button class="select-btn ${isSelected(track.id) ? 'selected' : ''}" 
                        onclick="toggleSeed('${track.id}', event)">
                    ${isSelected(track.id) ? 'Selected' : 'Select'}
                </button>
            </div>
        </div>
    `).join('');

    // Add click listeners for track details
    document.querySelectorAll('.track-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.classList.contains('select-btn')) {
                const trackId = card.dataset.trackId;
                showTrackDetail(trackId);
            }
        });
    });
}

// Toggle seed track selection
function toggleSeed(trackId, event) {
    event.stopPropagation();
    
    const track = state.searchResults.find(t => t.id === trackId);
    if (!track) return;

    const index = state.selectedSeeds.findIndex(s => s.id === trackId);
    
    if (index > -1) {
        state.selectedSeeds.splice(index, 1);
    } else {
        if (state.selectedSeeds.length >= 5) {
            showError('You can select up to 5 tracks for recommendations');
            return;
        }
        state.selectedSeeds.push(track);
    }

    updateSelectedSeedsUI();
    renderSearchResults();
}

// Check if track is selected
function isSelected(trackId) {
    return state.selectedSeeds.some(s => s.id === trackId);
}

// Update selected seeds UI
function updateSelectedSeedsUI() {
    if (state.selectedSeeds.length === 0) {
        elements.selectedSeeds.innerHTML = '<p class="empty-state-small">Select tracks from search to get recommendations</p>';
        elements.getRecommendationsBtn.disabled = true;
    } else {
        elements.selectedSeeds.innerHTML = state.selectedSeeds.map(track => `
            <span class="seed-pill">
                ${escapeHtml(track.name)}
                <button onclick="removeSeed('${track.id}')">&times;</button>
            </span>
        `).join('');
        elements.getRecommendationsBtn.disabled = false;
    }
}

// Remove seed
function removeSeed(trackId) {
    const index = state.selectedSeeds.findIndex(s => s.id === trackId);
    if (index > -1) {
        state.selectedSeeds.splice(index, 1);
        updateSelectedSeedsUI();
        renderSearchResults();
    }
}

// Get recommendations
async function getRecommendations() {
    if (state.selectedSeeds.length === 0) return;

    showLoading();
    try {
        const seedTracks = state.selectedSeeds.map(s => s.id).join(',');
        const response = await fetch(`/api/recommendations?seed_tracks=${seedTracks}&limit=10`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        state.recommendations = data.tracks;
        state.recommendationsFallback = data.fallback || false;
        state.recommendationsCustom = data.custom || false;
        renderRecommendations();
        switchTab('recommendations');
    } catch (error) {
        showError('Failed to get recommendations');
        console.error('Recommendations error:', error);
    } finally {
        hideLoading();
    }
}

// Render recommendations
function renderRecommendations() {
    let message = '';
    if (state.recommendationsCustom) {
        message = '<p style="color: var(--primary-color); margin-bottom: 20px; font-size: 0.9rem;">✨ Personalized recommendations based on your selected preferences!</p>';
    } else if (state.recommendationsFallback) {
        message = '<p style="color: var(--text-secondary); margin-bottom: 20px; font-size: 0.9rem;">ℹ️ Showing similar songs by the same artist (recommendations API not available)</p>';
    }
    
    if (state.recommendations.length === 0) {
        elements.recommendationsGrid.innerHTML = '<p class="empty-state">No recommendations found</p>';
        return;
    }

    elements.recommendationsGrid.innerHTML = message + state.recommendations.map(track => `
        <div class="track-card" data-track-id="${track.id}">
            ${track.image 
                ? `<img src="${track.image}" alt="${track.name}" class="track-image">`
                : `<div class="track-image-placeholder">No Image</div>`
            }
            <div class="track-info">
                <h3>${escapeHtml(track.name)}</h3>
                <p>${escapeHtml(track.artist)}</p>
                ${track.similarity_score 
                    ? `<small style="color: var(--primary-color);">★ Match: ${track.similarity_score}%</small>`
                    : (track.preview_url 
                        ? `<small style="color: var(--primary-color);">♪ Preview available</small>`
                        : `<small style="color: var(--text-secondary);">No preview</small>`)
                }
            </div>
        </div>
    `).join('');

    // Add click listeners
    document.querySelectorAll('#recommendationsGrid .track-card').forEach(card => {
        card.addEventListener('click', () => {
            showTrackDetail(card.dataset.trackId);
        });
    });
}

// Load featured playlists
async function loadFeaturedPlaylists() {
    try {
        const response = await fetch('/api/featured-playlists');
        const data = await response.json();

        if (data.error) {
            console.error('Featured playlists error:', data.error);
            return;
        }

        state.featuredPlaylists = data.playlists;
        renderFeaturedPlaylists();
    } catch (error) {
        console.error('Failed to load featured playlists:', error);
    }
}

// Render featured playlists
function renderFeaturedPlaylists() {
    if (state.featuredPlaylists.length === 0) {
        elements.featuredGrid.innerHTML = '<p class="empty-state">No featured playlists available</p>';
        return;
    }

    elements.featuredGrid.innerHTML = state.featuredPlaylists.map(playlist => `
        <div class="playlist-card" onclick="window.open('${playlist.spotify_url}', '_blank')">
            ${playlist.image 
                ? `<img src="${playlist.image}" alt="${playlist.name}">`
                : `<div class="track-image-placeholder">No Image</div>`
            }
            <h3>${escapeHtml(playlist.name)}</h3>
            <p>${escapeHtml(playlist.description || '')}</p>
            <p>${playlist.tracks_total} tracks</p>
        </div>
    `).join('');
}

// Load new releases
async function loadNewReleases() {
    try {
        const response = await fetch('/api/new-releases');
        const data = await response.json();

        if (data.error) {
            console.error('New releases error:', data.error);
            return;
        }

        state.newReleases = data.albums;
        renderNewReleases();
    } catch (error) {
        console.error('Failed to load new releases:', error);
    }
}

// Render new releases
function renderNewReleases() {
    if (state.newReleases.length === 0) {
        elements.newReleasesGrid.innerHTML = '<p class="empty-state">No new releases available</p>';
        return;
    }

    elements.newReleasesGrid.innerHTML = state.newReleases.map(album => `
        <div class="album-card" onclick="window.open('${album.spotify_url}', '_blank')">
            ${album.image 
                ? `<img src="${album.image}" alt="${album.name}">`
                : `<div class="track-image-placeholder">No Image</div>`
            }
            <h3>${escapeHtml(album.name)}</h3>
            <p>${escapeHtml(album.artist)}</p>
            <p>${album.release_date} • ${album.total_tracks} tracks</p>
        </div>
    `).join('');
}

// Show track detail
async function showTrackDetail(trackId) {
    showLoading();
    try {
        const response = await fetch(`/api/track/${trackId}`);
        const track = await response.json();

        if (track.error && !track.id) {
            showError(track.error);
            return;
        }

        renderTrackModal(track);
        elements.trackModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    } catch (error) {
        showError('Failed to load track details');
        console.error('Track detail error:', error);
    } finally {
        hideLoading();
    }
}

// Render track modal
function renderTrackModal(track) {
    const duration = formatDuration(track.duration_ms);
    const features = track.audio_features || {};

    elements.modalContent.innerHTML = `
        <div class="track-detail">
            ${track.image 
                ? `<img src="${track.image}" alt="${track.name}" class="track-detail-image">`
                : `<div class="track-detail-image track-image-placeholder">No Image</div>`
            }
            <div class="track-detail-info">
                <h2>${escapeHtml(track.name)}</h2>
                <p class="artist">${escapeHtml(track.artist)}</p>
                
                <div class="track-meta">
                    <div class="meta-item">
                        <span class="meta-label">Album</span>
                        <span class="meta-value">${escapeHtml(track.album)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Duration</span>
                        <span class="meta-value">${duration}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Popularity</span>
                        <span class="meta-value">${track.popularity}/100</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Release Date</span>
                        <span class="meta-value">${track.release_date}</span>
                    </div>
                </div>

                ${features && features.danceability !== undefined && features.danceability !== null ? `
                    <div class="audio-features">
                        <h3>Audio Features</h3>
                        ${renderFeatureBar('Danceability', features.danceability)}
                        ${renderFeatureBar('Energy', features.energy)}
                        ${renderFeatureBar('Valence (Positivity)', features.valence)}
                        ${renderFeatureBar('Acousticness', features.acousticness)}
                        ${renderFeatureBar('Instrumentalness', features.instrumentalness)}
                    </div>
                ` : '<p style="color: var(--text-secondary); margin-top: 16px;">Audio features not available for this track</p>'}

                <div class="track-links">
                    <a href="${track.spotify_url}" target="_blank">
                        Open in Spotify
                    </a>
                    ${track.preview_url ? `
                        <button class="btn btn-secondary" onclick="playPreview('${track.preview_url}', '${escapeHtml(track.name)}')">
                            ▶ Play Preview
                        </button>
                    ` : `<span style="color: var(--text-secondary); font-size: 0.875rem;">Preview not available</span>`}
                </div>
            </div>
        </div>
    `;
}

// Render feature bar
function renderFeatureBar(label, value) {
    const percentage = Math.round((value || 0) * 100);
    return `
        <div class="feature-bar">
            <div class="feature-label">
                <span>${label}</span>
                <span>${percentage}%</span>
            </div>
            <div class="feature-progress">
                <div class="feature-progress-fill" style="width: ${percentage}%"></div>
            </div>
        </div>
    `;
}

// Play preview
function playPreview(url, trackName) {
    if (!url) {
        alert('Preview not available for this track');
        return;
    }
    
    elements.audioElement.src = url;
    elements.audioElement.play().catch(error => {
        console.error('Audio playback error:', error);
        alert('Failed to play preview. The audio may not be available.');
    });
    elements.nowPlaying.textContent = `Now playing: ${trackName}`;
    elements.audioPlayer.classList.remove('hidden');
    
    // Add error handler for when audio fails to load
    elements.audioElement.onerror = () => {
        alert('Failed to load audio preview');
        closeAudioPlayer();
    };
}

// Close audio player
function closeAudioPlayer() {
    elements.audioElement.pause();
    elements.audioElement.src = '';
    elements.audioPlayer.classList.add('hidden');
}

// Close modal
function closeModal() {
    elements.trackModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Switch tab
function switchTab(tabId) {
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabId);
    });
}

// Show loading
function showLoading() {
    elements.loading.classList.remove('hidden');
}

// Hide loading
function hideLoading() {
    elements.loading.classList.add('hidden');
}

// Show error
function showError(message) {
    alert(`Error: ${message}`);
}

// Format duration
function formatDuration(ms) {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}