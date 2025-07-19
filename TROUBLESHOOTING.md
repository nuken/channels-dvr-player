# 🔧 Troubleshooting Guide

Common issues and solutions for Live TV Player.

## 🚀 Installation Issues

### ❌ "Python not found" or "python: command not found"

**Problem:** Python is not installed or not in PATH

**Solutions:**
```bash
# Check if Python is installed
python --version
python3 --version

# Install Python (if missing)
# Ubuntu/Debian:
sudo apt update && sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL:
sudo yum install python3 python3-pip

# macOS (with Homebrew):
brew install python

# Windows: Download from https://python.org
```

### ❌ "Permission denied" when running setup script

**Problem:** Script doesn't have execute permissions

**Solution:**
```bash
chmod +x setup_venv.sh
chmod +x activate_venv.sh
```

### ❌ "pip: command not found"

**Problem:** pip is not installed

**Solution:**
```bash
# Install pip
python -m ensurepip --upgrade
# OR
python3 -m ensurepip --upgrade
```

### ❌ Package installation fails

**Problem:** Missing build dependencies or old pip

**Solutions:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install build dependencies (Linux)
sudo apt install build-essential python3-dev

# Use system packages (if available)
pip install --prefer-binary -r requirements.txt
```

## 🌐 Network & DVR Issues

### ❌ "DVR Server Not Found"

**Problem:** Can't discover Channels DVR server

**Diagnosis:**
```bash
# Test DVR connectivity
ping DVR_IP_ADDRESS

# Test DVR web interface
curl http://DVR_IP:8089/status
```

**Solutions:**
1. **Check same network:** Ensure both devices on same subnet
2. **Manual IP entry:** Try accessing `http://DVR_IP:8089` directly
3. **Firewall:** Check firewall blocking port 8089
4. **DVR status:** Verify Channels DVR is running and accessible

### ❌ "Cannot connect to DVR"

**Problem:** Network connectivity issues

**Solutions:**
```bash
# Check DVR is running
# Access DVR web interface at http://DVR_IP:8089

# Check network connectivity
ping DVR_IP

# Check port accessibility
telnet DVR_IP 8089
# OR
nc -zv DVR_IP 8089
```

### ❌ "Address already in use" (Port 7734)

**Problem:** Port 7734 is already occupied

**Solutions:**
```bash
# Find process using port 7734
lsof -i :7734           # Linux/Mac
netstat -ano | find "7734"  # Windows

# Kill the process or use different port
# Edit app.py to change port:
app.run(host='0.0.0.0', port=7735, debug=True)
```

## 📺 Video Playback Issues

### ❌ "Video won't play" or black screen

**Problem:** HLS streaming or codec issues

**Solutions:**
1. **Try different browser** (Chrome recommended)
2. **Check browser console** (F12 → Console)
3. **Verify DVR stream** directly: `http://DVR_IP:8089/devices/ANY/channels/CHANNEL_ID.m3u8`
4. **Update browser** to latest version
5. **Enable hardware acceleration** in browser settings

### ❌ "Stream loading failed"

**Problem:** Codec compatibility or stream issues

**Solutions:**
1. **Check DVR transcoding settings**
2. **Try different channel** to isolate issue
3. **Browser compatibility:**
   - Chrome/Edge: Full HLS support
   - Firefox: Good support
   - Safari: Native HLS support
4. **Check DVR logs** for streaming errors

### ❌ Audio works but no video

**Problem:** Video codec not supported

**Solutions:**
1. **Try different browser**
2. **Check DVR transcoding settings**
3. **Enable hardware decoding** in browser
4. **Update graphics drivers**

### ❌ Video stutters or buffers frequently

**Problem:** Network or performance issues

**Solutions:**
1. **Check network speed:** Ensure sufficient bandwidth
2. **Use wired connection** instead of WiFi
3. **Close other streaming apps**
4. **Lower DVR quality settings**
5. **Check CPU usage** on both DVR and client

## 🎬 Channel & Playlist Issues

### ❌ "No channels found"

**Problem:** Channels not synced or enabled

**Solutions:**
1. **Sync channels:** Setup → Channels → "Sync Channels"
2. **Enable channels:** Use toggle switches
3. **Check DVR setup:** Verify channels in DVR interface
4. **Refresh page** after syncing

### ❌ "Playlist won't save"

**Problem:** Database or permission issues

**Solutions:**
```bash
# Check config directory permissions
ls -la config/
chmod 755 config/
chmod 644 config/channels.db

# Clear browser cache
# Hard refresh: Ctrl+F5 (Windows) / Cmd+Shift+R (Mac)
```

### ❌ "Channels missing from playlist"

**Problem:** Channel sync or filter issues

**Solutions:**
1. **Check channel status:** Ensure channels are enabled
2. **Re-sync channels:** Setup → Channels → "Sync Channels"
3. **Check filter settings:** "Show All" vs "Show Available"
4. **Refresh browser** and try again

## 🖥️ Browser-Specific Issues

### Chrome/Edge Issues
```javascript
// Check console for errors
// Common fixes:
// 1. Clear cache: Settings → Privacy → Clear browsing data
// 2. Disable extensions temporarily
// 3. Try incognito mode
```

### Firefox Issues
```javascript
// Enable HLS if needed:
// about:config → media.mediasource.enabled → true
// Clear cache: Settings → Privacy & Security → Clear Data
```

### Safari Issues
```javascript
// Enable develop menu: Safari → Preferences → Advanced
// Check console: Develop → Show Web Inspector
// Clear cache: Safari → Clear History
```

## 📊 Performance Issues

### ❌ High CPU usage

**Problem:** Browser or transcoding overload

**Solutions:**
1. **Close unused tabs**
2. **Lower video quality** in DVR settings
3. **Use hardware acceleration**
4. **Check DVR server resources**

### ❌ Slow page loading

**Problem:** Network or server issues

**Solutions:**
```bash
# Check server resources
top
htop

# Restart application
Ctrl+C  # Stop server
python app.py  # Restart

# Check network latency
ping localhost
ping DVR_IP
```

## 🐛 Debug Mode

Enable debug mode for more information:

```bash
# Enable Flask debug mode (already enabled in app.py)
export FLASK_DEBUG=1
python app.py

# Browser debugging
# 1. Open Developer Tools (F12)
# 2. Check Console tab for JavaScript errors
# 3. Check Network tab for failed requests
# 4. Check Application tab for storage issues
```

## 📋 Log Collection

For bug reports, collect these logs:

```bash
# 1. Application logs (terminal output)
python app.py > app.log 2>&1

# 2. Browser console logs (F12 → Console → Copy all)

# 3. Network requests (F12 → Network → Export HAR)

# 4. System information
python --version
pip list
lsb_release -a  # Linux
system_profiler SPSoftwareDataType  # Mac
systeminfo  # Windows
```

## 🆘 Getting More Help

### Before asking for help:

1. **Check browser console** (F12) for errors
2. **Try different browser** 
3. **Verify DVR accessibility** independently
4. **Clear browser cache** and try again
5. **Restart the application**

### Include this information:

```
Operating System: 
Browser & Version: 
Python Version: 
Error Message: 
Steps to Reproduce: 
Console Errors: 
```

### Useful commands for diagnosis:

```bash
# Check Python environment
python --version
pip list

# Check network connectivity
ping DVR_IP
curl -I http://DVR_IP:8089

# Check application logs
python app.py  # Watch for errors

# Check browser network tools
# F12 → Network → Look for failed requests
```

---

**Still stuck?** Include the information above when reporting issues!
