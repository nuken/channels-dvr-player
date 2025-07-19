# 🚀 Quick Start Guide

**Get up and running with Live TV Player in 3 minutes!**

## 📋 Before You Start

✅ **Channels DVR** is running on your network  
✅ **Python 3.7+** is installed  
✅ Both devices are on the **same network**

## 🔧 Installation

### Option 1: Easy Setup (Recommended)

**Linux/Mac:**
```bash
./setup_venv.sh
./activate_venv.sh
```

**Windows:**
```cmd
setup_venv.bat
activate_venv.bat
```

### Option 2: Manual Setup

1. **Create environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start app:**
   ```bash
   python app.py
   ```

## 🌐 First Run

1. **Open browser:** `http://localhost:7734`
2. **Go to Setup:** Click "Go to Setup" button
3. **Sync channels:** Setup → Channels → "Sync Channels"
4. **Enable channels:** Toggle switches to enable desired channels
5. **Create playlist:** Go to "Playlist Builder" → "Create Playlist"
6. **Watch TV:** Go to "Live TV Player" → Select playlist → Click channel

## ⚡ Quick Actions

| What you want to do | Where to go |
|---------------------|-------------|
| **Watch TV now** | Home → "Start Watching" |
| **Add/remove channels** | Setup → Channels |
| **Create playlists** | Playlist Builder |
| **Change settings** | Setup → Server |

## 🆘 Having Issues?

**App won't start?**
- Check Python version: `python --version`
- Try: `pip install --upgrade pip`

**Can't find DVR?**
- Verify DVR web interface works: `http://DVR_IP:8089`
- Check both devices on same network

**Video won't play?**
- Try different browser (Chrome recommended)
- Check DVR server is streaming properly

## 📞 Need Help?

See the full **README.md** for detailed troubleshooting and all features.

---
*⏱️ Total setup time: ~3 minutes*
