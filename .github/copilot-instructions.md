# Copilot Instructions for Channels DVR Web Player

## Project Overview
This is a Flask-based web application that provides a browser interface for Channels DVR live TV streaming. The app discovers DVR servers via mDNS, manages channel lists and playlists, and streams live TV using HLS.

## Architecture & Key Components

### Application Structure
- **Entry Point**: `app.py` - Simple Flask app factory pattern
- **Main Blueprint**: `app/main/` - All routes and views in single blueprint
- **Models**: `app/models/database.py` - SQLite ORM for channels/playlists
- **Services**: `app/services/` - External integrations (Channels DVR API, M3U parsing)
- **Configuration**: `config/app_config.py` - Centralized app settings and UI theme
- **Templates**: `app/templates/` - Jinja2 templates with Tailwind CSS

### Data Flow Pattern
1. **Discovery**: mDNS auto-discovery of Channels DVR servers (`ChannelsDVRClient`)
2. **Sync**: M3U parsing and channel import (`M3UParser`)
3. **Management**: Channel enable/disable and playlist creation
4. **Streaming**: Direct HLS URLs from Channels DVR to browser video elements

### State Management
- **User States**: `no_dvr` → `need_setup` → `need_playlists` → `ready_to_stream`
- **Session Data**: Selected playlist stored in session + cookies
- **Setup Flags**: Persistent state in `config/setup.flag` file
- **Database**: SQLite with channels, playlists, and playlist_channels tables

## Development Patterns

### Route Structure in `app/main/routes.py`
- **Pages**: `/`, `/setup`, `/player`, `/playlist` - render HTML templates
- **Setup Pages**: `/setup/server`, `/setup/channels`, `/setup/sync` - modular setup flow
- **API Endpoints**: `/api/*` - JSON responses for AJAX calls
- **Bulk Operations**: `/api/channels/bulk-toggle`, `/api/playlists` (POST for save)

### Template Pattern
All templates extend `base.html` and use consistent context variables:
```python
return render_template('page.html',
                     config=AppConfig,           # Always include
                     dvr_available=check_dvr_availability(),
                     channels_count=len(channels),
                     enabled_channels_count=len(enabled),
                     playlists_count=len(playlists))
```

### Error Handling Pattern
```python
try:
    # Operation
    return jsonify({'success': True, 'data': result})
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500
```

## Key Development Commands

### Environment Setup
```bash
./setup_venv.sh          # Creates venv and installs deps
./activate_venv.sh       # Activates environment
python app.py            # Starts dev server on :7734
```

### Database Operations
- Database auto-creates on first run at `config/channels.db`
- Factory reset available at `/factory-reset` endpoint
- No migrations - tables created via `Database.init_db()`

### External Dependencies
- **Channels DVR**: Auto-discovered via mDNS on `_http._tcp.local.`
- **M3U URLs**: Generated dynamically via `ChannelsDVRClient.get_m3u_url()`
- **EPG Data**: Fetched from Channels DVR EPG endpoint
- **Video Streaming**: Direct HLS URLs, no proxy/transcoding

## Important File Locations
- **Configuration**: `config/app_config.py` - UI theme, feature flags, page titles
- **Constants**: `app/constants.py` - Timeouts, cache durations, limits
- **Setup Scripts**: `setup_venv.sh` / `.bat` - Environment creation
- **Database Models**: `app/models/database.py` - Channel, Playlist, Database classes
- **DVR Integration**: `app/services/channels_dvr_services.py` - mDNS discovery + API client

## UI/UX Patterns
- **State-Driven UI**: Index page changes based on user_state
- **Modern Design**: Tailwind CSS with custom color scheme in AppConfig.UI_THEME
- **Responsive**: Mobile-friendly with backdrop blur effects
- **Search**: Real-time search via `/api/search` endpoint
- **Drag-and-Drop**: Playlist management uses HTML5 drag/drop

## Testing & Debugging
- **Logs**: Console output shows discovery, sync, and error details
- **Debug Mode**: Set `FLASK_DEBUG=True` in environment
- **Factory Reset**: `/factory-reset` clears all data and setup flags
- **DVR Status**: Check `check_dvr_availability()` function for connectivity
