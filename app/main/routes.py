from flask import Blueprint, render_template, request, jsonify, session, send_from_directory, make_response
from config.app_config import AppConfig
from app.services.channels_dvr_services import discover_dvr_server, ChannelsDVRClient
from app.models.database import Database, Channel, Playlist, SearchHistory
from app.services.m3u_parser import M3UParser
from app.constants import *
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import logging
import os
from . import bp

logger = logging.getLogger(__name__)

def check_dvr_availability():
    """Check if DVR server is currently available."""
    server_info = discover_dvr_server(timeout=QUICK_CHECK_TIMEOUT)  # Quick check
    return server_info is not None

def get_featured_programs(channel_ids, channels):
    """Get current program information for featured channels."""
    try:
        # Use the same logic as the API endpoint to get guide data
        db = Database()
        channel_model = Channel(db)
        
        # Get all channels to map IDs to tvg_ids
        all_channels = channel_model.get_all()
        
        # Create mapping from channel ID to tvg_id
        id_to_tvg_id = {}
        tvg_id_to_id = {}
        
        for channel in all_channels:
            if channel.get('tvg_id'):
                id_to_tvg_id[channel['id']] = channel['tvg_id']
                tvg_id_to_id[channel['tvg_id']] = channel['id']
        
        # Get the tvg_ids we need
        tvg_ids_needed = []
        for ch_id in channel_ids:
            if ch_id in id_to_tvg_id:
                tvg_ids_needed.append(id_to_tvg_id[ch_id])
        
        if not tvg_ids_needed:
            return []
        
        # Get guide data using existing function
        server_info = discover_dvr_server(timeout=DVR_DISCOVERY_TIMEOUT)
        if not server_info:
            return []
            
        try:
            with ChannelsDVRClient() as client:
                epg_url = client.get_epg_url(device="ANY")
                
            if not epg_url:
                logger.error("Could not get EPG URL")
                return []
                
            # Fetch EPG data
            response = requests.get(epg_url, timeout=HTTP_REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse the guide data - this already handles time parsing and filtering
            guide_data = parse_xmltv_data(response.text, tvg_ids_needed, tvg_id_to_id)
            
        except Exception as e:
            logger.error(f"Error fetching guide data: {e}")
            return []
        
        # Build featured programs
        featured_programs = []
        now = datetime.now()
        
        for channel in channels:
            channel_id = channel['id']
            channel_programs = guide_data.get(channel_id, [])
            
            # Find current program - use same logic as player.html
            current_program = None
            for program in channel_programs:
                try:
                    # Parse times - they come with Z suffix from parse_xmltv_data
                    # Convert to local timezone for comparison (same as frontend)
                    start_time = datetime.fromisoformat(program['start_time'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(program['end_time'].replace('Z', '+00:00'))
                    
                    # Convert UTC to local for comparison
                    start_time = start_time.replace(tzinfo=timezone.utc).astimezone()
                    end_time = end_time.replace(tzinfo=timezone.utc).astimezone()
                    
                    # Make now timezone-aware for comparison
                    local_now = now.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    
                    if start_time <= local_now < end_time:
                        current_program = program
                        break
                except Exception as e:
                    logger.error(f"Error parsing program times: {e}")
                    continue
            
            if current_program:
                # Calculate progress and remaining time using same logic as frontend
                try:
                    # Parse times - convert UTC to local (same as current_program finding logic)
                    start_time = datetime.fromisoformat(current_program['start_time'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(current_program['end_time'].replace('Z', '+00:00'))
                    
                    # Convert UTC to local for calculation
                    start_time = start_time.replace(tzinfo=timezone.utc).astimezone()
                    end_time = end_time.replace(tzinfo=timezone.utc).astimezone()
                    
                    # Make now timezone-aware
                    local_now = now.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    
                    total_duration = (end_time - start_time).total_seconds()
                    elapsed = (local_now - start_time).total_seconds()
                    progress = min(max((elapsed / total_duration) * 100, 0), 100) if total_duration > 0 else 0
                    
                    remaining_seconds = (end_time - local_now).total_seconds()
                    remaining_minutes = max(int(remaining_seconds / 60), 0)
                    
                except Exception as e:
                    logger.error(f"Error calculating progress: {e}")
                    progress = 0
                    remaining_minutes = 0
                    start_time = now
                    end_time = now
                
                featured_programs.append({
                    'channel': channel,
                    'program': current_program,
                    'progress': progress,
                    'remaining_minutes': remaining_minutes,
                    'start_time': start_time.strftime('%I:%M %p'),
                    'end_time': end_time.strftime('%I:%M %p')
                })
                
            else:
                # No current program - get next upcoming program if available
                upcoming_program = None
                if channel_programs:
                    for program in channel_programs:
                        try:
                            start_time = datetime.fromisoformat(program['start_time'].replace('Z', ''))
                            if start_time > now:
                                upcoming_program = program
                                break
                        except Exception:
                            continue
                
                if upcoming_program:
                    try:
                        start_time = datetime.fromisoformat(upcoming_program['start_time'].replace('Z', ''))
                        featured_programs.append({
                            'channel': channel,
                            'program': {
                                'title': f"Coming Up: {upcoming_program['title']}",
                                'description': upcoming_program.get('description', ''),
                                'artwork_url': upcoming_program.get('artwork_url')
                            },
                            'progress': 0,
                            'remaining_minutes': 0,
                            'start_time': start_time.strftime('%I:%M %p'),
                            'end_time': ''
                        })
                    except Exception:
                        # Fallback to basic channel info
                        featured_programs.append({
                            'channel': channel,
                            'program': {
                                'title': 'Live TV',
                                'description': f'Currently broadcasting on {channel["name"]}'
                            },
                            'progress': 0,
                            'remaining_minutes': 0,
                            'start_time': '',
                            'end_time': ''
                        })
                else:
                    # No programs available
                    featured_programs.append({
                        'channel': channel,
                        'program': {
                            'title': 'Live TV',
                            'description': f'Currently broadcasting on {channel["name"]}'
                        },
                        'progress': 0,
                        'remaining_minutes': 0,
                        'start_time': '',
                        'end_time': ''
                    })
        
        result = featured_programs[:MAX_FEATURED_PROGRAMS]
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting featured programs: {e}")
        return []

@bp.route('/')
def index():
    """Home page route."""
    # Check if DVR was previously discovered
    dvr_previously_discovered = AppConfig.get_setup_flag('dvr_discovered')
    
    # Discover DVR server
    server_info = discover_dvr_server(timeout=DVR_DISCOVERY_TIMEOUT)
    
    if server_info:
        # Server discovered
        dvr_currently_found = True
        # Mark as discovered in setup.flag for future visits
        AppConfig.set_setup_flag('dvr_discovered', True)
    else:
        # Server not discovered
        dvr_currently_found = False
    
    # Only show discovery message if server is found AND it wasn't previously discovered
    show_discovery_message = dvr_currently_found and not dvr_previously_discovered
    
    # Only show "not found" message if server is not found AND it wasn't previously discovered
    show_not_found_message = not dvr_currently_found and not dvr_previously_discovered
    
    # Determine user state for better UX flow
    user_state = "no_dvr"  # Default state
    channels_exist = False
    playlists_exist = False
    all_channels = []
    all_playlists = []
    
    if dvr_currently_found:
        try:
            # Check if channels have been imported
            db = Database()
            channel_model = Channel(db)
            playlist_model = Playlist(db)
            
            all_channels = channel_model.get_all()
            all_playlists = playlist_model.get_all()
            
            # Check for enabled channels, not just any channels
            enabled_channels = [ch for ch in all_channels if ch.get('is_enabled', False)]
            channels_exist = len(enabled_channels) > 0
            playlists_exist = len(all_playlists) > 0
            
            if not channels_exist:
                # Check if we should attempt auto-scan
                auto_scan_attempted = AppConfig.get_setup_flag('auto_scan_attempted')
                
                if not auto_scan_attempted:
                    # Attempt auto-scan on first visit
                    logger.info("Attempting automatic channel sync on first visit...")
                    try:
                        parser = M3UParser(db)
                        # Use replace_existing=True to get fresh data and disable all by default
                        sync_result = parser.sync_channels_from_dvr(replace_existing=True)
                        
                        # Mark auto-scan as attempted regardless of success
                        AppConfig.set_setup_flag('auto_scan_attempted', True)
                        
                        if sync_result.get('success'):
                            logger.info(f"Auto-scan successful: {sync_result.get('message', 'Channels imported')}")
                            
                            # Disable all channels by default after auto-scan
                            # Users should manually enable the ones they want
                            all_channels = channel_model.get_all()
                            for channel in all_channels:
                                if channel.get('is_enabled', True):  # If enabled, disable it
                                    channel_model.toggle_enabled(channel['id'])
                            logger.info(f"Disabled all {len(all_channels)} channels - user must manually enable desired channels")
                            
                            # Re-check enabled channels after successful sync
                            all_channels = channel_model.get_all()
                            enabled_channels = [ch for ch in all_channels if ch.get('is_enabled', False)]
                            channels_exist = len(enabled_channels) > 0
                            
                            # Even if channels exist after auto-scan, keep user in setup state
                            # so they can choose which channels to enable/disable
                            user_state = "need_setup"
                        else:
                            logger.warning(f"Auto-scan failed: {sync_result.get('error', 'Unknown error')}")
                            user_state = "need_setup"
                            
                    except Exception as scan_error:
                        logger.error(f"Auto-scan error: {scan_error}")
                        AppConfig.set_setup_flag('auto_scan_attempted', True)
                        user_state = "need_setup"
                else:
                    user_state = "need_setup"
                    
            elif channels_exist and not playlists_exist:
                user_state = "need_playlists"
            elif channels_exist and playlists_exist:
                user_state = "ready_to_stream"
            else:
                # No enabled channels - stay in setup
                user_state = "need_setup"
                
        except Exception as e:
            logger.error(f"Error checking user state: {e}")
            user_state = "need_setup"
    
    # Get live program data for featured cards only if ready to stream
    featured_programs = []
    if user_state == "ready_to_stream":
        try:
            db = Database()
            playlist_model = Playlist(db)
            playlists = playlist_model.get_all()
            
            if playlists:
                # Check for the last selected playlist from cookie first, then session
                selected_playlist_name = request.cookies.get('selectedPlaylist')
                selected_playlist_id = session.get('selected_playlist_id')
                featured_playlist = None
                
                # First, try to find playlist by name from cookie
                if selected_playlist_name:
                    for playlist in playlists:
                        if playlist['name'] == selected_playlist_name:
                            featured_playlist = playlist
                            # Update session to match cookie selection
                            session['selected_playlist_id'] = playlist['id']
                            break
                
                # If no playlist found via cookie, try session ID
                if not featured_playlist and selected_playlist_id:
                    for playlist in playlists:
                        if playlist['id'] == selected_playlist_id:
                            featured_playlist = playlist
                            break
                
                # If no valid playlist found, use the first available playlist
                if not featured_playlist:
                    featured_playlist = playlists[0]
                    # Store this as the selected playlist for future use
                    session['selected_playlist_id'] = featured_playlist['id']
                
                playlist_channels = playlist_model.get_channels(featured_playlist['id'])
                
                # Get up to 6 channels for featured cards
                featured_channels = playlist_channels[:MAX_FEATURED_PROGRAMS]
                
                if featured_channels:
                    # Get current program data for these channels
                    channel_ids = [ch['id'] for ch in featured_channels]
                    featured_programs = get_featured_programs(channel_ids, featured_channels)
                    
        except Exception as e:
            logger.error(f"Error getting featured programs: {e}")
            featured_programs = []
    
    # Check if auto-scan was attempted (keeping for backward compatibility)
    auto_scan_attempted = AppConfig.get_setup_flag('auto_scan_attempted')
    
    return render_template('index.html', 
                         config=AppConfig, 
                         user_state=user_state,
                         dvr_available=dvr_currently_found,
                         server_info=server_info,
                         channels_count=len(all_channels),
                         enabled_channels_count=len([ch for ch in all_channels if ch.get('is_enabled', False)]),
                         playlists_count=len(all_playlists),
                         featured_programs=featured_programs,
                         auto_scan_attempted=auto_scan_attempted)

@bp.route('/setup')
def setup():
    """Setup page route."""
    # Discover DVR server and get URLs
    server_info = discover_dvr_server(timeout=DVR_DISCOVERY_TIMEOUT)
    
    if server_info:
        # Generate M3U and EPG URLs using the service
        try:
            from app.services.channels_dvr_services import ChannelsDVRClient
            with ChannelsDVRClient() as client:
                m3u_url = client.get_m3u_url(device="ANY", format="hls", codec="copy")
                epg_url = client.get_epg_url(device="ANY")
        except Exception as e:
            logger.error(f"Error getting URLs: {e}")
            m3u_url = None
            epg_url = None
            
        dvr_status = "online"
    else:
        m3u_url = None
        epg_url = None
        dvr_status = "offline"
    
    # Get channel statistics
    db = Database()
    parser = M3UParser(db)
    channel_stats = parser.get_channel_stats()
    
    # Get all channels for the UI
    channel_model = Channel(db)
    playlist_model = Playlist(db)
    all_channels = channel_model.get_all()
    all_playlists = playlist_model.get_all()
    groups = channel_model.get_groups()
    
    return render_template('setup.html', 
                         config=AppConfig, 
                         server_info=server_info,
                         dvr_available=check_dvr_availability(),
                         m3u_url=m3u_url,
                         epg_url=epg_url,
                         dvr_status=dvr_status,
                         channel_stats=channel_stats,
                         channels=all_channels,
                         groups=groups,
                         channels_count=len(all_channels),
                         enabled_channels_count=len([ch for ch in all_channels if ch.get('is_enabled', False)]),
                         playlists_count=len(all_playlists))

@bp.route('/setup/server')
def setup_server():
    """Server configuration page."""
    # Discover DVR server and get URLs
    server_info = discover_dvr_server(timeout=DVR_DISCOVERY_TIMEOUT)
    
    if server_info:
        # Generate M3U and EPG URLs using the service
        try:
            from app.services.channels_dvr_services import ChannelsDVRClient
            with ChannelsDVRClient() as client:
                m3u_url = client.get_m3u_url(device="ANY", format="hls", codec="copy")
                epg_url = client.get_epg_url(device="ANY")
        except Exception as e:
            logger.error(f"Error getting URLs: {e}")
            m3u_url = None
            epg_url = None
            
        dvr_status = "online"
    else:
        m3u_url = None
        epg_url = None
        dvr_status = "offline"
    
    return render_template('setup_server.html', 
                         config=AppConfig, 
                         server_info=server_info,
                         dvr_available=check_dvr_availability(),
                         m3u_url=m3u_url,
                         epg_url=epg_url,
                         dvr_status=dvr_status)

@bp.route('/setup/sync')
def setup_sync():
    """Channel sync page."""
    # Discover DVR server
    server_info = discover_dvr_server(timeout=DVR_DISCOVERY_TIMEOUT)
    dvr_status = "online" if server_info else "offline"
    
    # Get channel statistics
    db = Database()
    parser = M3UParser(db)
    channel_stats = parser.get_channel_stats()
    
    return render_template('setup_sync.html', 
                         config=AppConfig, 
                         server_info=server_info,
                         dvr_available=check_dvr_availability(),
                         dvr_status=dvr_status,
                         channel_stats=channel_stats)

@bp.route('/setup/channels')
def setup_channels():
    """Channel management page."""
    # Get all channels for the UI
    db = Database()
    channel_model = Channel(db)
    all_channels = channel_model.get_all()
    groups = channel_model.get_groups()
    
    return render_template('setup_channels.html', 
                         config=AppConfig, 
                         channels=all_channels,
                         groups=groups,
                         channels_count=len(all_channels),
                         enabled_channels_count=len([ch for ch in all_channels if ch.get('is_enabled', False)]))

@bp.route('/playlist')
def playlist():
    """Playlist builder page route."""
    # Get all playlists with their channels
    db = Database()
    playlist_model = Playlist(db)
    channel_model = Channel(db)
    search_history = SearchHistory(db)
    
    # Get all playlists
    playlists = playlist_model.get_all()
    
    # Add channels to each playlist
    for playlist in playlists:
        playlist['channels'] = playlist_model.get_channels(playlist['id'])
    
    # Add search history as a special playlist (read-only)
    history_channels = search_history.get_history_channels()
    if history_channels:  # Only include if there's search history
        search_history_playlist = {
            'id': 'search-history',
            'name': '🕒 Search History',
            'description': 'Recently searched channels (read-only)',
            'channels': history_channels,
            'isSearchHistory': True,
            'isReadOnly': True,
            'created_at': '',
            'updated_at': ''
        }
        # Add at the beginning of the playlists list
        playlists.insert(0, search_history_playlist)
    
    # Get all channels for the channel browser
    all_channels = channel_model.get_all()
    
    return render_template('playlist.html',
                         config=AppConfig,
                         dvr_available=check_dvr_availability(),
                         playlists=playlists,
                         channels=all_channels,
                         channels_count=len(all_channels),
                         enabled_channels_count=len([ch for ch in all_channels if ch.get('is_enabled', False)]),
                         playlists_count=len(playlists))

@bp.route('/player')
def player():
    """Live TV player page route."""
    # Get all playlists with their channels
    db = Database()
    playlist_model = Playlist(db)
    channel_model = Channel(db)
    search_history = SearchHistory(db)
    
    # Get all playlists
    playlists = playlist_model.get_all()
    
    # Add channels to each playlist
    for playlist in playlists:
        playlist['channels'] = playlist_model.get_channels(playlist['id'])
    
    # Add search history as a special playlist
    history_channels = search_history.get_history_channels()
    if history_channels:  # Only include if there's search history
        search_history_playlist = {
            'id': 'search-history',
            'name': '🕒 Search History',
            'description': 'Recently searched channels',
            'channels': history_channels,
            'isSearchHistory': True,
            'created_at': '',
            'updated_at': ''
        }
        # Add at the beginning of the playlists list
        playlists.insert(0, search_history_playlist)
    
    # Get all channels for reference
    all_channels = channel_model.get_all()
    
    return render_template('player.html',
                         config=AppConfig,
                         dvr_available=check_dvr_availability(),
                         playlists=playlists,
                         channels=all_channels,
                         channels_count=len(all_channels),
                         enabled_channels_count=len([ch for ch in all_channels if ch.get('is_enabled', False)]),
                         playlists_count=len(playlists))

# API Routes for channel management
@bp.route('/api/channels/sync', methods=['POST'])
def sync_channels():
    """Sync channels from Channels DVR server."""
    try:
        replace_existing = request.json.get('replace_existing', False) if request.json else False
        
        db = Database()
        parser = M3UParser(db)
        result = parser.sync_channels_from_dvr(replace_existing=replace_existing)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/channels/<int:channel_id>/toggle', methods=['POST'])
def toggle_channel(channel_id):
    """Toggle channel enabled/disabled status."""
    try:
        db = Database()
        channel_model = Channel(db)
        new_status = channel_model.toggle_enabled(channel_id)
        
        return jsonify({
            'success': True,
            'channel_id': channel_id,
            'is_enabled': new_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/channels/bulk-toggle', methods=['POST'])
def bulk_toggle_channels():
    """Bulk enable or disable all channels."""
    try:
        data = request.json or {}
        enable = data.get('enable', True)
        
        db = Database()
        channel_model = Channel(db)
        
        # Get all channels
        channels = channel_model.get_all()
        
        # Update all channels to the desired state
        channels_updated = 0
        with db.get_connection() as conn:
            for channel in channels:
                current_status = channel.get('is_enabled', False)
                if current_status != enable:
                    conn.execute(
                        "UPDATE channels SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (enable, channel['id'])
                    )
                    channels_updated += 1
        
        return jsonify({
            'success': True,
            'channels_updated': channels_updated,
            'total_channels': len(channels),
            'enabled': enable
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/channels/stats')
def get_channel_stats():
    """Get channel statistics."""
    try:
        db = Database()
        parser = M3UParser(db)
        stats = parser.get_channel_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/channels/<int:channel_id>')
def get_channel_details(channel_id):
    """Get details for a specific channel."""
    try:
        db = Database()
        channel_model = Channel(db)
        
        # Get the channel by ID
        channel = channel_model.get_by_id(channel_id)
        
        if not channel:
            return jsonify({
                'success': False,
                'error': 'Channel not found'
            }), 404
        
        return jsonify({
            'success': True,
            'channel': channel
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/search')
def search():
    """Search for channels and programs."""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': True,
                'results': []
            })
        
        db = Database()
        channel_model = Channel(db)
        
        # Search channels by name, tvg_id, or channel_number
        channels = channel_model.search(query)
        
        results = []
        
        # Get current program information for channels
        current_programs = {}
        server_info = discover_dvr_server(timeout=QUICK_CHECK_TIMEOUT)
        if server_info:
            try:
                client = ChannelsDVRClient()
                guide_url = client.get_epg_url()
                
                if guide_url:
                    response = requests.get(guide_url, timeout=DVR_DISCOVERY_TIMEOUT)
                    if response.status_code == 200:
                        current_programs = get_current_programs_for_channels(response.text, channels)
            except Exception as e:
                logger.warning(f"Could not fetch current programs for search: {e}")
        
        # Add channel results
        for channel in channels:
            if channel.get('is_enabled', False):  # Only show enabled channels
                channel_result = {
                    'type': 'channel',
                    'id': channel['id'],
                    'name': channel['name'],
                    'logo_url': channel.get('logo_url'),
                    'channel_number': channel.get('channel_number'),
                    'tvg_id': channel.get('tvg_id')
                }
                
                # Add current program if available
                tvg_id = channel.get('tvg_id')
                if tvg_id and tvg_id in current_programs:
                    channel_result['current_program'] = current_programs[tvg_id]
                
                results.append(channel_result)
        
        # If we have a DVR server, also search for programs
        server_info = discover_dvr_server(timeout=QUICK_CHECK_TIMEOUT)
        if server_info and len(results) < MAX_TOTAL_SEARCH_RESULTS:  # Limit total results
            try:
                # Get guide data and search for programs
                client = ChannelsDVRClient()
                guide_url = client.get_epg_url()
                
                if guide_url:
                    response = requests.get(guide_url, timeout=DVR_DISCOVERY_TIMEOUT)
                    if response.status_code == 200:
                        programs = search_programs_in_guide(response.text, query, channels)
                        # Add programs up to the remaining space in our result limit
                        remaining_slots = MAX_TOTAL_SEARCH_RESULTS - len(results)
                        results.extend(programs[:remaining_slots])
            except Exception as e:
                logger.warning(f"Could not search programs: {e}")
        
        return jsonify({
            'success': True,
            'results': results[:MAX_TOTAL_SEARCH_RESULTS]  # Limit total results
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def search_programs_in_guide(guide_xml, query, channels):
    """Search for programs in the XML guide data."""
    results = []
    query_lower = query.lower()
    
    try:
        root = ET.fromstring(guide_xml)
        
        # Create channel mapping
        channel_map = {}
        for channel in channels:
            if channel.get('tvg_id'):
                channel_map[channel['tvg_id']] = channel
        
        # Search programmes
        current_time = datetime.now(timezone.utc)
        end_time = current_time + timedelta(hours=6)  # Search next 6 hours
        
        for programme in root.findall('.//programme'):
            try:
                # Check if programme is within time window
                start_str = programme.get('start', '')
                if not start_str:
                    continue
                    
                start_time = datetime.strptime(start_str, '%Y%m%d%H%M%S %z')
                if start_time < current_time or start_time > end_time:
                    continue
                
                # Get programme details
                title_elem = programme.find('title')
                if title_elem is None or not title_elem.text:
                    continue
                    
                title = title_elem.text
                if query_lower not in title.lower():
                    continue
                
                # Get channel info
                channel_id = programme.get('channel', '')
                if channel_id not in channel_map:
                    continue
                    
                channel = channel_map[channel_id]
                
                # Get description
                desc_elem = programme.find('desc')
                description = desc_elem.text if desc_elem is not None else ''
                
                results.append({
                    'type': 'program',
                    'title': title,
                    'description': description,
                    'channel_id': channel['id'],
                    'channel_name': channel['name'],
                    'start_time': start_time.strftime('%I:%M %p'),
                    'artwork_url': None  # Could be enhanced later
                })
                
                if len(results) >= MAX_PROGRAM_RESULTS:  # Limit program results
                    break
                    
            except Exception as e:
                logger.debug(f"Error parsing programme: {e}")
                continue
                
    except Exception as e:
        logger.warning(f"Error parsing guide XML for search: {e}")
    
    return results

def get_current_programs_for_channels(guide_xml, channels):
    """Get current programs for a list of channels."""
    current_programs = {}
    
    try:
        root = ET.fromstring(guide_xml)
        
        # Create channel mapping
        channel_map = {}
        for channel in channels:
            if channel.get('tvg_id'):
                channel_map[channel['tvg_id']] = channel
        
        # Find current programmes
        current_time = datetime.now(timezone.utc)
        
        for programme in root.findall('.//programme'):
            try:
                # Check if programme is currently airing
                start_str = programme.get('start', '')
                stop_str = programme.get('stop', '')
                if not start_str or not stop_str:
                    continue
                    
                start_time = datetime.strptime(start_str, '%Y%m%d%H%M%S %z')
                stop_time = datetime.strptime(stop_str, '%Y%m%d%H%M%S %z')
                
                if start_time <= current_time <= stop_time:
                    # This is a current program
                    channel_id = programme.get('channel', '')
                    if channel_id in channel_map:
                        title_elem = programme.find('title')
                        if title_elem is not None and title_elem.text:
                            current_programs[channel_id] = title_elem.text
                    
            except Exception as e:
                logger.debug(f"Error parsing programme for current programs: {e}")
                continue
                
    except Exception as e:
        logger.warning(f"Error parsing guide XML for current programs: {e}")
    
    return current_programs

# API Routes for playlist management
@bp.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all playlists with their channels."""
    try:
        db = Database()
        playlist_model = Playlist(db)
        search_history = SearchHistory(db)
        
        playlists = playlist_model.get_all()
        
        # Add channels to each playlist
        for playlist in playlists:
            playlist['channels'] = playlist_model.get_channels(playlist['id'])
        
        # Add search history as a special playlist
        history_channels = search_history.get_history_channels()
        if history_channels:  # Only include if there's search history
            search_history_playlist = {
                'id': 'search-history',
                'name': '🕒 Search History',
                'description': 'Recently searched channels',
                'channels': history_channels,
                'isSearchHistory': True,
                'created_at': '',
                'updated_at': ''
            }
            # Add at the beginning of the playlists list
            playlists.insert(0, search_history_playlist)
        
        return jsonify({
            'success': True,
            'playlists': playlists
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/playlists', methods=['POST'])
def save_playlists():
    """Save playlists (create, update, delete)."""
    try:
        data = request.json or {}
        playlists = data.get('playlists', [])
        
        db = Database()
        playlist_model = Playlist(db)
        
        # Get existing playlists to determine what to delete
        existing_playlists = {p['id']: p for p in playlist_model.get_all()}
        current_playlist_ids = {p['id'] for p in playlists if 'id' in p}
        
        # Delete playlists that are no longer in the list
        for playlist_id in existing_playlists.keys():
            if playlist_id not in current_playlist_ids:
                playlist_model.delete(playlist_id)
        
        # Process each playlist
        for playlist_data in playlists:
            if 'id' not in playlist_data or playlist_data['id'] > 1000000000:  # New playlist (timestamp ID)
                # Create new playlist
                playlist_id = playlist_model.create(
                    name=playlist_data['name'],
                    description=playlist_data.get('description', '')
                )
            else:
                # Update existing playlist
                playlist_id = playlist_data['id']
                playlist_model.update(
                    playlist_id=playlist_id,
                    name=playlist_data['name'],
                    description=playlist_data.get('description', '')
                )
            
            # Clear existing channels for this playlist
            with db.get_connection() as conn:
                conn.execute("DELETE FROM playlist_channels WHERE playlist_id = ?", (playlist_id,))
            
            # Add channels with their order
            for order, channel in enumerate(playlist_data.get('channels', []), 1):
                playlist_model.add_channel(playlist_id, channel['id'], order)
        
        return jsonify({
            'success': True,
            'message': 'Playlists saved successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Search History API endpoints
@bp.route('/api/search-history/add', methods=['POST'])
def add_to_search_history():
    """Add a channel to search history."""
    try:
        data = request.json or {}
        channel_id = data.get('channel_id')
        
        if not channel_id:
            return jsonify({
                'success': False,
                'error': 'Channel ID is required'
            }), 400
        
        db = Database()
        search_history = SearchHistory(db)
        search_history.add_channel(channel_id)
        
        return jsonify({
            'success': True,
            'message': 'Channel added to search history'
        })
        
    except Exception as e:
        logger.error(f"Error adding to search history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/search-history')
def get_search_history():
    """Get search history as a playlist."""
    try:
        db = Database()
        search_history = SearchHistory(db)
        channels = search_history.get_history_channels()
        
        return jsonify({
            'success': True,
            'playlist': {
                'id': 'search-history',
                'name': '🕒 Search History',
                'description': 'Recently searched channels',
                'channels': channels,
                'isSearchHistory': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/search-history/clear', methods=['POST'])
def clear_search_history():
    """Clear all search history."""
    try:
        db = Database()
        search_history = SearchHistory(db)
        search_history.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'Search history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing search history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/guide/data', methods=['POST'])
def get_guide_data():
    """Get guide data for specified channels."""
    try:
        data = request.json or {}
        requested_channel_ids = data.get('channels', [])
        
        if not requested_channel_ids:
            logger.warning("No channels requested for guide data")
            return jsonify({})
        
        # Get the actual channel records to get their tvg_id mappings
        db = Database()
        channel_model = Channel(db)
        
        # Get channels from the database to map IDs
        all_channels = channel_model.get_all()
        
        # Create mapping from channel ID to tvg_id
        id_to_tvg_id = {}
        tvg_id_to_id = {}
        
        for channel in all_channels:
            if channel.get('tvg_id'):
                id_to_tvg_id[channel['id']] = channel['tvg_id']
                tvg_id_to_id[channel['tvg_id']] = channel['id']
        
        # Get the tvg_ids we need to look for
        tvg_ids_needed = []
        for ch_id in requested_channel_ids:
            if ch_id in id_to_tvg_id:
                tvg_id = id_to_tvg_id[ch_id]
                tvg_ids_needed.append(tvg_id)
        
        if not tvg_ids_needed:
            logger.warning("No valid tvg_ids found for requested channels")
            return jsonify({})
        
        # Get EPG data from Channels DVR
        with ChannelsDVRClient() as client:
            epg_url = client.get_epg_url()
            if not epg_url:
                logger.warning("No EPG URL available")
                return jsonify({})
            
            # Fetch EPG data
            response = requests.get(epg_url, timeout=HTTP_REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Parse XMLTV data
            guide_data = parse_xmltv_data(response.text, tvg_ids_needed, tvg_id_to_id)
            
            # Create response with appropriate caching headers
            from flask import make_response
            json_response = make_response(jsonify(guide_data))
            json_response.headers['Cache-Control'] = 'max-age=900'  # Cache for 15 minutes
            json_response.headers['Expires'] = (datetime.now() + timedelta(minutes=15)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            return json_response
            
    except Exception as e:
        logger.error(f"Error fetching guide data: {e}")
        return jsonify({})

def parse_xmltv_data(xmltv_content, tvg_ids_needed, tvg_id_to_channel_id):
    """Parse XMLTV data and extract program information for specified channels."""
    try:
        root = ET.fromstring(xmltv_content)
        guide_data = {}
        
        # Get current time and extend the window to include current programs
        now = datetime.now()
        # Look back 3 hours and forward 8 hours to catch current programs and provide better coverage
        start_time = now - timedelta(hours=3)
        end_time = now + timedelta(hours=8)
        
        # Make sure end_time is timezone-aware for comparison with converted program times
        end_time = end_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
        
        logger.info(f"Parsing guide data from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')} for {len(tvg_ids_needed)} channels")
        
        # First, build a dictionary of all channel definitions in the guide
        xmltv_channels = {}
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            if channel_id:
                channel_info = {
                    'id': channel_id,
                    'display_name': ''
                }
                
                # Get display name
                display_name = channel.find('display-name')
                if display_name is not None:
                    channel_info['display_name'] = display_name.text or ''
                
                xmltv_channels[channel_id] = channel_info
        
        programs_found = 0
        
        # Process programs
        for programme in root.findall('programme'):
            xmltv_channel_id = programme.get('channel')
            
            # Only process channels we're interested in
            if xmltv_channel_id not in tvg_ids_needed:
                continue
            
            # Parse program times
            start_str = programme.get('start')
            stop_str = programme.get('stop')
            
            if not start_str or not stop_str:
                continue
                
            try:
                # Parse XMLTV datetime format (e.g., "20231215120000 +0000")
                # XMLTV times are in UTC, so parse them as UTC
                start_time_str = start_str[:14]
                stop_time_str = stop_str[:14]
                
                start_time = datetime.strptime(start_time_str, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
                stop_time = datetime.strptime(stop_time_str, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
                
                # Convert to local timezone for comparison with our window
                start_time_local = start_time.astimezone()
                stop_time_local = stop_time.astimezone()
                
                # Only include programs within our expanded time window (compare local times)
                if stop_time_local < start_time_local or start_time_local > end_time:
                    continue
                    
            except ValueError as e:
                logger.warning(f"Error parsing time {start_str}/{stop_str}: {e}")
                continue
            
            # Extract program details
            title_elem = programme.find('title')
            title = title_elem.text if title_elem is not None else 'Unknown Program'
            
            desc_elem = programme.find('desc')
            description = desc_elem.text if desc_elem is not None else ''
            
            # Extract program artwork/images
            artwork_url = None
            icon_elem = programme.find('icon')
            if icon_elem is not None:
                artwork_url = icon_elem.get('src')
            
            # Also check for image elements
            if not artwork_url:
                image_elem = programme.find('image')
                if image_elem is not None:
                    artwork_url = image_elem.text or image_elem.get('src')
            
            # Extract episode info
            episode_info = []
            
            # Try episode-num element
            episode_num_elem = programme.find('episode-num')
            if episode_num_elem is not None and episode_num_elem.text:
                episode_info.append(episode_num_elem.text)
            
            # Try sub-title element  
            sub_title_elem = programme.find('sub-title')
            if sub_title_elem is not None and sub_title_elem.text:
                episode_info.append(sub_title_elem.text)
            
            episode_str = ' • '.join(episode_info) if episode_info else None
            
            # Map back to our internal channel ID
            internal_channel_id = tvg_id_to_channel_id.get(xmltv_channel_id)
            if not internal_channel_id:
                continue
            
            # Add to guide data using our internal channel ID
            if internal_channel_id not in guide_data:
                guide_data[internal_channel_id] = []
            
            guide_data[internal_channel_id].append({
                'title': title,
                'description': description,
                'episode': episode_str,
                'artwork_url': artwork_url,
                'start_time': start_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'end_time': stop_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'channel_display_name': xmltv_channels.get(xmltv_channel_id, {}).get('display_name', '')
            })
            
            programs_found += 1
        
        # Sort programs by start time for each channel
        for channel_id in guide_data:
            guide_data[channel_id].sort(key=lambda x: x['start_time'])
        
        return guide_data
        
    except ET.ParseError as e:
        logger.error(f"Error parsing XMLTV data: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error processing guide data: {e}")
        return {}

@bp.route('/proxy/stream/<int:channel_id>')
def proxy_stream(channel_id):
    """Proxy HLS video streams to bypass CORS restrictions."""
    try:
        import requests
        from flask import Response, request as flask_request
        
        # Get channel from database
        db = Database()
        channel_model = Channel(db)
        channel = channel_model.get_by_id(channel_id)
        
        if not channel:
            return jsonify({'error': 'Channel not found'}), 404
        
        # Get the original stream URL
        stream_url = channel['stream_url']
        
        # Always use HLS format for web playback
        format_param = 'hls'
        
        # Modify URL to use HLS format and handle codec appropriately
        if '?' in stream_url:
            base_url = stream_url.split('?')[0]
            # Parse existing parameters
            from urllib.parse import urlparse, parse_qs, urlencode
            parsed = urlparse(stream_url)
            params = parse_qs(parsed.query)
            # Update format to HLS
            params['format'] = [format_param]
            
            # For HDHomeRun comptat streams, try h264 codec instead of copy for better browser compatibility
            # This helps with AAC audio streams that don't work well with codec=copy
            if 'hdhomerun' in stream_url.lower() or str(CHANNELS_DVR_DEFAULT_PORT) in stream_url:
                params['codec'] = ['h264']
                logger.info(f"Stream detected, using h264 codec for better browser compatibility")
            else:
                params['codec'] = ['copy']
                
            # Rebuild URL
            new_query = urlencode(params, doseq=True)
            proxied_url = f"{base_url}?{new_query}"
        else:
            # For HDHomeRun  compat streams, try h264 codec instead of copy
            if 'hdhomerun' in stream_url.lower() or str(CHANNELS_DVR_DEFAULT_PORT) in stream_url:
                proxied_url = f"{stream_url}?format={format_param}&codec=h264"
                logger.info(f"Stream detected, using h264 codec for better browser compatibility")
            else:
                proxied_url = f"{stream_url}?format={format_param}&codec=copy"
        
        logger.info(f"Proxying HLS stream: {proxied_url}")
        
        # Stream the content from Channels DVR
        def generate():
            try:
                with requests.get(proxied_url, stream=True, timeout=HTTP_REQUEST_TIMEOUT) as r:
                    r.raise_for_status()
                    logger.info(f"Channels DVR response: {r.status_code}, Content-Type: {r.headers.get('content-type')}")
                    
                    for chunk in r.iter_content(chunk_size=8192):
                        yield chunk
                            
            except Exception as e:
                logger.error(f"Proxy streaming error: {e}")
                yield b''
        
        # Set content type for HLS streams
        content_type = 'application/vnd.apple.mpegurl'
        
        logger.info(f"Setting response content-type: {content_type}")
        
        return Response(
            generate(),
            content_type=content_type,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
    except Exception as e:
        logger.error(f"Proxy stream error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/playlists')
def api_playlists():
    """API endpoint to get all playlists."""
    try:
        db = Database()
        playlist_model = Playlist(db)
        playlists = playlist_model.get_all()
        
        return jsonify({
            'success': True,
            'playlists': playlists
        })
        
    except Exception as e:
        logger.error(f"Error fetching playlists: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/playlists/<int:playlist_id>/channels')
def api_playlist_channels(playlist_id):
    """API endpoint to get channels for a specific playlist."""
    try:
        db = Database()
        channel_model = Channel(db)
        channels = channel_model.get_by_playlist(playlist_id)
        
        return jsonify({
            'success': True,
            'channels': channels
        })
        
    except Exception as e:
        logger.error(f"Error fetching playlist channels: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/factory-reset', methods=['GET'])
def factory_reset():
    """Factory reset - delete all data and return to initial state."""
    try:
        import os
        import shutil
        from config.app_config import AppConfig
        
        # Delete the database file
        db_path = DEFAULT_DB_PATH
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Database file deleted")
        
        # Delete setup flags
        setup_flag_path = "config/setup.flag"
        if os.path.exists(setup_flag_path):
            os.remove(setup_flag_path)
            logger.info("Setup flags deleted")
        
        # Clear any cached data
        cache_dirs = ["__pycache__", "app/__pycache__", "app/main/__pycache__", 
                      "app/models/__pycache__", "app/services/__pycache__", "config/__pycache__"]
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    shutil.rmtree(cache_dir)
                    logger.info(f"Cleared cache directory: {cache_dir}")
                except Exception as e:
                    logger.warning(f"Could not clear cache directory {cache_dir}: {e}")
        
        logger.info("Factory reset completed successfully")
        
        return jsonify({
            'success': True,
            'message': 'Factory reset completed successfully',
            'redirect': '/'
        })
        
    except Exception as e:
        logger.error(f"Factory reset error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
