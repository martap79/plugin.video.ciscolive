# Implementation Checklist

Use this checklist to track implementation of the UX improvements.

## Phase 1: Visual Assets & Quick Wins ✅

- [x] Create icon.png (256x256)
- [x] Create fanart.jpg (1920x1080)
- [x] Generate assets with create_assets.py
- [x] Review UX_REVIEW.md for detailed recommendations
- [ ] Apply improved session label format (remove code prefix)
- [ ] Add color-coded difficulty indicators
- [ ] Improve pagination text
- [ ] Hide sessions without video by default
- [ ] Add show_no_video setting

**Time estimate:** 1-2 hours  
**Priority:** High  
**Impact:** Immediate visual improvement

---

## Phase 2: Core Navigation Improvements

### Main Menu Restructure
- [ ] Add "Recently Added" menu item
- [ ] Add "Featured Sessions" menu item
- [ ] Add "Continue Watching" menu item (placeholder)
- [ ] Consolidate Technology/Level/Type into "Browse by Category" sub-menu
- [ ] Reorder menu items (content-first)
- [ ] Add emoji/icons for visual distinction

### New View Functions
- [ ] Implement show_recently_added()
- [ ] Implement show_featured()
- [ ] Implement show_categories()
- [ ] Implement show_history() placeholder
- [ ] Update router() with new actions

### Settings
- [ ] Add General settings section
  - [ ] show_no_video (boolean)
  - [ ] page_size (integer, 10-100)
- [ ] Add Playback settings section
  - [ ] prefer_hls (boolean)
  - [ ] auto_advance (boolean)
- [ ] Add Appearance settings section
  - [ ] show_level_colors (boolean)
  - [ ] show_duration (boolean)

**Time estimate:** 3-4 hours  
**Priority:** High  
**Impact:** Major UX improvement

---

## Phase 3: Polish & Advanced Features

### Session Display Enhancements
- [ ] Implement _format_level_badge() with colors
- [ ] Add subtitle/label2 for secondary info
- [ ] Improve thumbnail selection logic
- [ ] Add plugin fanart to all list items
- [ ] Test readability on actual TV

### Watch History (Optional)
- [ ] Create resources/lib/history.py
- [ ] Implement add_to_history()
- [ ] Implement get_recent()
- [ ] Track playback position
- [ ] Add "Continue Watching" functional view
- [ ] Add resume prompts

### Sorting & Filtering
- [ ] Add sort_by parameter to show_session_list()
- [ ] Implement client-side sorting (duration, title)
- [ ] Add "Sort by..." menu item to lists
- [ ] Consider server-side sorting if API supports it

### Performance
- [ ] Increase cache TTL to 6-24 hours
- [ ] Test cache invalidation
- [ ] Add loading indicators for slow connections
- [ ] Consider background prefetch of next page
- [ ] Profile performance with large result sets

### Additional Features
- [ ] Better thumbnail generation/selection
- [ ] Fetch video thumbnails from Brightcove API
- [ ] Add keyboard shortcuts (if supported)
- [ ] Implement auto-advance to next video
- [ ] Add "Related Sessions" feature

**Time estimate:** 2-3 hours  
**Priority:** Medium  
**Impact:** Nice-to-have enhancements

---

## Testing Checklist

### Functional Testing
- [ ] Test on actual TV with remote control (not just desktop)
- [ ] Verify all menu items navigate correctly
- [ ] Test "Recently Added" shows latest event
- [ ] Test "Featured Sessions" displays correctly
- [ ] Test search functionality
- [ ] Test pagination (first/middle/last pages)
- [ ] Verify all videos play successfully
- [ ] Test sessions without video handling
- [ ] Test with slow network connection
- [ ] Test cache expiration and refresh

### UI/UX Testing
- [ ] Verify text is readable from 10 feet away
- [ ] Check color-coded indicators are visible
- [ ] Verify secondary info line displays in skin
- [ ] Test menu navigation with D-pad only
- [ ] Ensure no "dead ends" in navigation
- [ ] Verify back button works correctly
- [ ] Test context menus (if applicable)
- [ ] Check that icons/fanart display correctly

### Skin Compatibility
- [ ] Test with Estuary skin (Kodi default)
- [ ] Test with Confluence skin (if available)
- [ ] Test with Aeon Nox skin (popular)
- [ ] Test with at least one other popular skin
- [ ] Verify fallbacks work if features not supported

### Edge Cases
- [ ] Test with empty search results
- [ ] Test with very long session titles
- [ ] Test with sessions missing metadata
- [ ] Test with sessions having no speaker photos
- [ ] Test pagination with exactly PAGE_SIZE items
- [ ] Test with special characters in search
- [ ] Test settings persistence across restarts
- [ ] Test cache behavior after manual clear

### Settings Testing
- [ ] Verify all settings save correctly
- [ ] Test show_no_video ON/OFF
- [ ] Test different page_size values (10, 25, 50, 100)
- [ ] Test prefer_hls ON/OFF with different video sources
- [ ] Test show_level_colors ON/OFF
- [ ] Test show_duration ON/OFF
- [ ] Verify settings reset to defaults works

---

## Pre-Release Checklist

### Code Quality
- [ ] Remove debug logging
- [ ] Add docstrings to new functions
- [ ] Check for Python 2/3 compatibility (if needed)
- [ ] Remove unused imports
- [ ] Format code consistently
- [ ] Add error handling for edge cases

### Documentation
- [ ] Update addon.xml version number
- [ ] Update changelog/release notes
- [ ] Document new features for users
- [ ] Update README if applicable
- [ ] Document settings in user guide

### Assets
- [ ] Verify icon.png is 256x256 and optimized
- [ ] Verify fanart.jpg is 1920x1080 and optimized
- [ ] Ensure file sizes are reasonable (<100KB each)
- [ ] Test assets display in Kodi menus
- [ ] Verify assets meet Kodi repository guidelines (if submitting)

### Performance
- [ ] Profile startup time
- [ ] Profile menu loading time
- [ ] Profile video playback startup
- [ ] Check memory usage with large lists
- [ ] Verify cache directory cleanup works

---

## Known Limitations & Future Ideas

### Current Limitations
- No actual "Featured Sessions" curation (uses longest videos as proxy)
- No watch history tracking yet (placeholder only)
- No video thumbnails from Brightcove (uses speaker photos)
- No server-side sorting (client-side only)
- No "Related Sessions" recommendations
- No offline/download support

### Future Enhancement Ideas
- [ ] Implement actual watch history with local database
- [ ] Add video thumbnail extraction from Brightcove API
- [ ] Add "Most Viewed" or "Trending" based on community data
- [ ] Implement manual curation of featured sessions
- [ ] Add "Related Sessions" based on technology/speaker
- [ ] Add filters for duration (short/medium/long)
- [ ] Add filter for event date ranges
- [ ] Implement favorites/bookmarks
- [ ] Add notification for new sessions
- [ ] Support multiple languages
- [ ] Add subtitle/closed caption support
- [ ] Implement progressive loading (virtual scrolling)

---

## Success Metrics

Track these metrics before/after implementation:

### User Experience
- **Clicks to first video**: Before: 3-4 | Target: 1-2
- **Time to first play**: Before: ~30s | Target: <10s
- **Sessions visible on home**: Before: 0 | Target: 50
- **Menu items on home**: Before: 6 | Target: 6 (reorganized)

### Performance
- **Menu load time**: Target: <1s
- **Video start time**: Target: <3s
- **Cache hit rate**: Target: >80%
- **Memory usage**: Target: <50MB for 500 items

### Content Discovery
- **Playable sessions shown**: Before: ~40% | Target: ~90%
- **Non-video session visibility**: Before: Always | Target: Optional
- **Visual difficulty indicators**: Before: None | Target: 100%
- **Session metadata visible**: Before: Minimal | Target: Rich

---

## Support & Resources

### Documentation
- **Full UX Review**: See `UX_REVIEW.md`
- **Before/After Comparison**: See `COMPARISON.md`
- **Implementation Summary**: See `SUMMARY.md`
- **Code Sample**: See `addon_improved_sample.py`

### Assets
- **Icon**: `resources/media/icon.png` (256x256)
- **Fanart**: `resources/media/fanart.jpg` (1920x1080)
- **Generator**: `create_assets.py` (regenerate if needed)

### References
- Kodi Plugin Development: https://kodi.wiki/view/Add-on_development
- Kodi UI Guidelines: https://kodi.wiki/view/Add-on_Rules
- Python 3 API: https://romanvm.github.io/Kodistubs/

---

## Version History

### v1.1.0 (Proposed - UX Improvements)
- ✅ New icon.png and fanart.jpg assets
- Restructured main menu (content-first)
- Added "Recently Added" view
- Added "Featured Sessions" view
- Improved session display (cleaner labels)
- Color-coded difficulty levels
- Better pagination UI
- Hide sessions without video (optional)
- New user settings
- Watch history placeholder

### v1.0.0 (Current)
- Initial release
- Basic browsing by event/technology/level/type
- Search functionality
- Brightcove video playback
- Session filtering and pagination

---

**Last Updated:** February 11, 2026  
**Status:** Phase 1 Complete (Assets Created) ✅  
**Next:** Begin Phase 2 Implementation
