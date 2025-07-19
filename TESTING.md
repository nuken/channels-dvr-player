# 🧪 Testing Checklist

Use this checklist to systematically test the Live TV Player application.

## 📋 Pre-Test Setup

- [ ] **System Info Recorded**
  - [ ] Operating System: _______________
  - [ ] Browser: _______________
  - [ ] Python Version: _______________
  - [ ] Channels DVR Version: _______________
  - [ ] Network Type: WiFi / Ethernet

## 🔧 Installation Testing

- [ ] **Setup Script Works**
  - [ ] `setup_venv.sh` / `setup_venv.bat` runs without errors
  - [ ] Virtual environment created successfully
  - [ ] Dependencies installed correctly
  - [ ] Application starts with `python app.py`

- [ ] **Initial Access**
  - [ ] Can access `http://localhost:7734`
  - [ ] Page loads properly
  - [ ] No JavaScript errors in console (F12)

## 🌐 Server Discovery & Setup

- [ ] **DVR Discovery**
  - [ ] App automatically finds Channels DVR server
  - [ ] Server details display correctly
  - [ ] M3U URL is shown
  - [ ] Can access DVR web interface independently

- [ ] **Channel Sync**
  - [ ] "Sync Channels" button works
  - [ ] Channels import from DVR
  - [ ] Channel count matches DVR
  - [ ] Channel logos display (if available)

## ⚙️ Channel Management

- [ ] **Enable/Disable Channels**
  - [ ] Toggle switches work
  - [ ] "Bulk Enable/Disable" works
  - [ ] Channel search filters properly
  - [ ] Status filter works (All/Enabled/Disabled)

- [ ] **Channel Info**
  - [ ] Channel names display correctly
  - [ ] Channel numbers show (if available)
  - [ ] Channel logos load (if available)

## 📋 Playlist Management

- [ ] **Create Playlists**
  - [ ] "Create Playlist" modal opens
  - [ ] Can enter playlist name
  - [ ] Playlist saves successfully
  - [ ] New playlist appears in list

- [ ] **Edit Playlists**
  - [ ] Can edit playlist name
  - [ ] Changes save properly
  - [ ] Updated name shows everywhere

- [ ] **Delete Playlists**
  - [ ] Delete confirmation appears
  - [ ] Playlist removes from list
  - [ ] No broken references remain

- [ ] **Add/Remove Channels**
  - [ ] Can add channels to playlist
  - [ ] Can remove channels from playlist
  - [ ] Channel count updates correctly
  - [ ] Disabled channels don't add

- [ ] **Drag & Drop Reordering**
  - [ ] Can drag channels to reorder
  - [ ] Order persists after save
  - [ ] Visual feedback during drag

## 📺 Live TV Player

- [ ] **Playlist Selection**
  - [ ] Playlist dropdown populates
  - [ ] Can select different playlists
  - [ ] Channel list updates correctly
  - [ ] Playlist preference saves

- [ ] **Channel Navigation**
  - [ ] Can click channels to select
  - [ ] Selected channel highlights
  - [ ] Channel count shows correctly

- [ ] **Video Playback**
  - [ ] Video player loads
  - [ ] Stream starts playing
  - [ ] Audio works properly
  - [ ] Video quality is acceptable
  - [ ] Can use video controls (pause, volume, etc.)

- [ ] **Live Status**
  - [ ] Live indicator shows green when playing
  - [ ] Shows "READY" when not playing
  - [ ] Updates appropriately

## 📊 Program Guide

- [ ] **Program Information**
  - [ ] Current program displays below video
  - [ ] Program title shows correctly
  - [ ] Time range displays
  - [ ] Progress bar updates

- [ ] **Channel Guide**
  - [ ] Channel list shows current programs
  - [ ] Program info updates periodically
  - [ ] Time stamps are accurate

## 🔍 Search & Navigation

- [ ] **Search Functionality**
  - [ ] Can search for channels by name
  - [ ] Can search by channel number
  - [ ] Search results are accurate
  - [ ] Can select from search results

- [ ] **Navigation**
  - [ ] All menu links work
  - [ ] Can navigate between pages
  - [ ] Browser back button works
  - [ ] Bookmarks work properly

## 📱 Browser Compatibility

Test in multiple browsers:

- [ ] **Chrome/Chromium**
  - [ ] Video plays ✅/❌
  - [ ] All features work ✅/❌
  - [ ] Performance good ✅/❌

- [ ] **Firefox**
  - [ ] Video plays ✅/❌
  - [ ] All features work ✅/❌
  - [ ] Performance good ✅/❌

- [ ] **Safari** (Mac)
  - [ ] Video plays ✅/❌
  - [ ] All features work ✅/❌
  - [ ] Performance good ✅/❌

- [ ] **Edge**
  - [ ] Video plays ✅/❌
  - [ ] All features work ✅/❌
  - [ ] Performance good ✅/❌

## 🚨 Error Handling

- [ ] **Network Issues**
  - [ ] Graceful handling when DVR unavailable
  - [ ] Error messages are helpful
  - [ ] App recovers when connection restored

- [ ] **Video Errors**
  - [ ] Handles codec issues gracefully
  - [ ] Error messages are user-friendly
  - [ ] Can recover by switching channels

- [ ] **Input Validation**
  - [ ] Prevents empty playlist names
  - [ ] Handles special characters
  - [ ] Form validation works

## 🎯 User Experience

- [ ] **Interface**
  - [ ] UI is intuitive
  - [ ] Loading states are clear
  - [ ] Responsive design works
  - [ ] Dark theme is consistent

- [ ] **Performance**
  - [ ] Page loads quickly
  - [ ] Video starts promptly
  - [ ] No lag when switching channels
  - [ ] Memory usage reasonable

- [ ] **Accessibility**
  - [ ] Keyboard navigation works
  - [ ] Screen reader friendly
  - [ ] Good color contrast

## 📝 Bug Reports

For any issues found, please provide:

1. **Steps to reproduce**
2. **Expected behavior**
3. **Actual behavior**
4. **Browser console errors** (F12 → Console)
5. **Network tab info** (F12 → Network)
6. **System information** from above

## ⭐ Feature Feedback

Rate these areas (1-5 stars):

- **Ease of setup**: ⭐⭐⭐⭐⭐
- **Channel management**: ⭐⭐⭐⭐⭐
- **Playlist creation**: ⭐⭐⭐⭐⭐
- **Video player**: ⭐⭐⭐⭐⭐
- **Overall UI/UX**: ⭐⭐⭐⭐⭐

## 💡 Suggestions

Any features or improvements you'd like to see:

_____________________________________________
_____________________________________________
_____________________________________________

---

**Testing Completed By:** _______________  
**Date:** _______________  
**Overall Rating:** ⭐⭐⭐⭐⭐
