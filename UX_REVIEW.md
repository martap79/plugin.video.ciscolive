# Cisco Live Kodi Plugin - UX Review & Recommendations

**Review Date:** February 11, 2026  
**Plugin Version:** 1.0.0  
**Reviewer:** UX Design Agent  

---

## Executive Summary

The Cisco Live plugin provides access to 6,000+ conference sessions across multiple years and events. The current implementation is functional but can be significantly improved for the **10-foot UI** experience (TV + remote control). This review provides concrete recommendations focused on:

1. **Reducing clicks to content** - Fewer steps from launch to playback
2. **Better content discovery** - Surface the best content first
3. **Visual hierarchy** - Make important info scannable from 10 feet away
4. **Graceful degradation** - Handle 4,000+ sessions without video elegantly
5. **Remote-friendly navigation** - Optimize for D-pad controls

---

## Current State Analysis

### Strengths ✅
- Clean, logical information architecture
- Good use of filtering (event, tech, level, session type)
- Pagination implemented correctly
- Session metadata is comprehensive
- Works with Kodi's native search

### Pain Points ❌
1. **No "Recently Added" or "Featured" section** - Users land in a menu of filters, not content
2. **Sessions without video clutter the interface** - 4,000+ non-playable items reduce signal-to-noise
3. **Sorting is limited** - No "Most Viewed", "Newest First", or "Recommended"
4. **Session labels are verbose** - `"BRKSEC-2011 - Advanced Security Implementation"` is hard to read on TV
5. **No visual distinction by content quality** - All sessions look the same
6. **Pagination shows raw counts** - "Next page (50 / 1234)" is not user-friendly
7. **No content preview** - Speaker photos are used, but no session thumbnails
8. **Main menu is filter-heavy** - Browsing should come before filtering

---

## Recommended Information Architecture

### New Main Menu (Priority Order)

```
1. 🔥 Recently Added        [Top priority - new content]
2. 🎬 Featured Sessions     [Hand-picked or most viewed]
3. 📚 Browse by Event       [Most common entry point]
4. 🔍 Search               [Quick access]
5. 🏷️  Browse by Category   [Technology, Level, Type - sub-menu]
6. ⚙️  Advanced Filters     [For power users]
```

**Rationale:**
- **Content-first approach** - Users see videos immediately, not just filters
- **Discovery over search** - Most users don't know what they want; show them
- **Reduce menu depth** - Consolidate "Technology", "Level", "Session Type" into one sub-menu

---

## Detailed UX Improvements

### 1. **Home Screen: Recently Added**

**Current:** Lands on a menu of 6 filter options  
**Proposed:** Lands on a grid of the newest 50 sessions with video

**Implementation:**
```python
def main_menu():
    """Show the top-level menu."""
    items = [
        ("🔥 Recently Added", build_url("recently_added"), "DefaultRecentlyAddedVideos.png"),
        ("🎬 Featured Sessions", build_url("featured"), "DefaultMovies.png"),
        ("📚 Browse by Event", build_url("events"), "DefaultVideoPlaylists.png"),
        ("🔍 Search", build_url("search"), "DefaultAddonsSearch.png"),
        ("🏷️ Browse by Category", build_url("categories"), "DefaultGenre.png"),
        ("⚙️ Advanced Filters", build_url("advanced_filters"), "DefaultAddonService.png"),
    ]
    # ... rest of menu code
```

**New function:**
```python
def show_recently_added():
    """Show newest sessions with video, sorted by event date descending."""
    # Sort by event date/upload date, filter to has_video=True
    # This becomes the default landing experience
    show_session_list(
        page=0, 
        has_video=True, 
        sort_by="newest"
    )
```

---

### 2. **Session Display: Improved Readability**

**Current:**
```
BRKSEC-2011 - Advanced Security Implementation with Cisco Firepower (no video)
```

**Problems:**
- Too long for TV screens (60+ characters)
- Session code is redundant for browsing
- "(no video)" appears in grey, but item is still clickable

**Proposed Label Format:**
```
Advanced Security Implementation
Security • Expert • 45 min
```

**Implementation:**
```python
def _add_session_item(item):
    """Add a single session as a playable list item."""
    title = item.get("title", "")
    code = item.get("code", "")
    has_video = item.get("has_video", False)
    
    # Primary label: Title only (code goes in secondary info)
    label = title
    
    # Build secondary info line for subtitle
    info_parts = []
    if item.get("technologies"):
        info_parts.append(item["technologies"][0])  # First tech only
    if item.get("level"):
        level_short = item["level"].replace("Technical Level ", "")
        info_parts.append(level_short)
    if item.get("duration"):
        mins = int(item["duration"] / 60)
        info_parts.append(f"{mins} min")
    
    subtitle = " • ".join(info_parts)
    
    li = xbmcgui.ListItem(label)
    
    # Use label2 for secondary info (shown as subtitle in most skins)
    li.setLabel2(subtitle)
    
    # InfoTag with proper Kodi v20+ API
    info_tag = li.getVideoInfoTag()
    info_tag.setTitle(title)
    
    # Put session code in "Episode" field so it's searchable but not prominent
    if code:
        info_tag.setEpisode(int(code.split("-")[-1]) if "-" in code else 0)
        info_tag.setTvShowTitle(code.split("-")[0] if "-" in code else code)
    
    # ... rest of info_tag setup
```

**Visual Result:**
```
Advanced Security Implementation            🎬
Security • Expert • 45 min
```

---

### 3. **Handle Sessions Without Video**

**Current:** Sessions without video are shown in grey with "(no video)" suffix  
**Problem:** They clutter lists and can't be played - confusing UX

**Recommended Options:**

#### **Option A: Hide Them Entirely (Preferred)**
Default behavior: Only show sessions with video. Add a setting:

```xml
<!-- resources/settings.xml -->
<setting id="show_no_video" type="bool" label="Show sessions without video" default="false"/>
```

```python
# In show_session_list()
show_no_video = ADDON.getSettingBool("show_no_video")
if not show_no_video:
    items = [i for i in items if i.get("has_video")]
```

#### **Option B: Separate Menu Item (Alternative)**
Add a menu item for "Sessions without Video (PDF/slides only)" - makes it explicit.

**Rationale:** On a video plugin for a TV interface, non-video content is friction. Users can't read PDFs on TV. If they want to browse slides, they'll use a computer.

---

### 4. **Sorting & Filtering**

**Current:** No sort options, only basic filtering  
**Proposed:** Multiple sort modes with visual indicators

```python
def show_session_list(page=0, filter_key=None, filter_val=None,
                       has_video=False, search_text=None, sort_by="relevance"):
    """
    List sessions with optional filters and pagination.
    
    sort_by options:
    - "relevance" (default for search)
    - "newest" (event date descending)
    - "title" (alphabetical)
    - "duration_short" (short sessions first)
    - "duration_long" (long sessions first)
    """
    filters = {}
    if filter_key and filter_val:
        filters[filter_key] = filter_val
    if search_text:
        filters["search"] = search_text
    
    # Add sort parameter to API call if supported, or sort locally
    result = rainfocus.search_sessions(
        page=page, 
        page_size=PAGE_SIZE, 
        filters=filters,
        sort=sort_by
    )
    
    items = result.get("items", [])
    
    # Client-side sorting if API doesn't support it
    if sort_by == "duration_short":
        items.sort(key=lambda x: x.get("duration", 0))
    elif sort_by == "duration_long":
        items.sort(key=lambda x: x.get("duration", 0), reverse=True)
    elif sort_by == "title":
        items.sort(key=lambda x: x.get("title", ""))
    
    # ... rest of function
```

**UI Addition:** Add "Sort by..." as first item in session lists:
```python
# At the top of any session list
li = xbmcgui.ListItem("⚙️ Sort by: Newest")
li.setArt({"icon": "DefaultIconInfo.png"})
url = build_url("sort_menu", current_context=...)
xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
```

---

### 5. **Visual Enhancements**

#### **A. Color-Coding by Technical Level**

Use label formatting to show difficulty at a glance:

```python
def _format_level_badge(level):
    """Return colored badge for technical level."""
    level_colors = {
        "Introductory": "green",
        "Intermediate": "yellow", 
        "Advanced": "orange",
        "Expert": "red",
    }
    color = level_colors.get(level, "white")
    return f"[COLOR {color}]●[/COLOR] {level}"

# In _add_session_item():
if item.get("level"):
    info_parts.append(_format_level_badge(item["level"]))
```

**Result:**
```
🟢 Introductory
🟡 Intermediate  
🟠 Advanced
🔴 Expert
```

#### **B. Better Thumbnails**

**Current:** Speaker photos are used  
**Problem:** Many sessions have no speaker photo, or multiple speakers

**Proposed:**
1. Generate placeholder thumbnails with session type/category
2. Use event logos when available
3. Fall back to colored backgrounds based on technology category

```python
def _get_session_thumbnail(item):
    """Get the best available thumbnail for a session."""
    # Priority 1: Brightcove video thumbnail (if available via API)
    if item.get("video_ids"):
        video_thumb = brightcove.get_thumbnail(item["video_ids"][0])
        if video_thumb:
            return video_thumb
    
    # Priority 2: Speaker photo (current behavior)
    photos = item.get("speaker_photos", [])
    if photos and photos[0]:
        return photos[0]
    
    # Priority 3: Generated placeholder based on category
    tech = item.get("technologies", ["Default"])[0]
    return _get_placeholder_thumb(tech, item.get("level", ""))

def _get_placeholder_thumb(technology, level):
    """Generate or return a cached placeholder thumbnail URL."""
    # Could generate these on-the-fly or pre-create them
    # For now, map to Kodi default icons
    tech_icons = {
        "Security": "DefaultIconInfo.png",
        "Data Center": "DefaultHardDisk.png",
        "Collaboration": "DefaultIconInfo.png",
        "Wireless": "DefaultNetwork.png",
        # ... etc
    }
    return tech_icons.get(technology, "DefaultVideo.png")
```

---

### 6. **Pagination Improvements**

**Current:**
```
[COLOR yellow]Next page (50 / 1234)[/COLOR]
```

**Problems:**
- Exact counts are not user-friendly on TV
- Yellow color is harsh
- Doesn't indicate page position

**Proposed:**
```
▶️ More sessions... (page 2 of 25)
```

```python
# In show_session_list()
next_offset = (page + 1) * PAGE_SIZE
if next_offset < total:
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE  # Ceiling division
    current_page = page + 1
    
    label = f"▶️ More sessions... (page {current_page + 1} of {total_pages})"
    li = xbmcgui.ListItem(label)
    li.setArt({"icon": "DefaultFolderBack.png"})
    # ... rest of pagination code
```

**Alternative (even simpler):**
```
▶️ Load more...
```
No page numbers - just infinite scroll style.

---

### 7. **Featured Content**

Add a "Featured Sessions" menu that highlights:
- Most viewed (if analytics available)
- Editor's picks (manual curation)
- Newest from the latest event
- Popular topics (e.g., "AI", "Security", "Automation")

```python
def show_featured():
    """Show hand-picked featured sessions."""
    # Could be a static list maintained in code or fetched from a server
    featured_ids = [
        "session_id_1",  # "What's New in Cisco Security"
        "session_id_2",  # "AI-Powered Networks"
        # ... etc
    ]
    
    for sid in featured_ids:
        item = rainfocus.get_session(sid)
        if item:
            _add_session_item(item)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
```

Or dynamically:
```python
def show_featured():
    """Show newest sessions from the latest event."""
    events = rainfocus.get_events()
    if events:
        latest_event = events[-1]  # Already reversed in show_events()
        show_session_list(
            filter_key="search.event",
            filter_val=latest_event["id"],
            has_video=True,
            sort_by="newest"
        )
```

---

## Additional Recommendations

### 8. **Keyboard Shortcuts & Gestures**

For users with a keyboard or advanced remote:
- **[** / **]** : Jump to previous/next session
- **F** : Mark as favorite (requires local storage)
- **R** : Refresh catalog

```python
# In addon.py, add keyboard listener for playback
def on_playback_ended(session_id):
    """Auto-advance to next session."""
    if ADDON.getSettingBool("auto_advance"):
        # Play next session in current list
        pass
```

### 9. **Recently Played / Resume**

Track watch history locally:
```python
# In resources/lib/history.py
import json
import os

HISTORY_FILE = os.path.join(ADDON.getAddonInfo("profile"), "history.json")

def add_to_history(session_id, position=0):
    """Track that a session was played."""
    history = _load_history()
    history[session_id] = {
        "timestamp": time.time(),
        "position": position,
    }
    _save_history(history)

def get_recent():
    """Get recently played sessions."""
    history = _load_history()
    return sorted(history.items(), key=lambda x: x[1]["timestamp"], reverse=True)
```

Add to main menu:
```
📜 Continue Watching
```

### 10. **Performance Optimization**

**Current:** Fetches fresh data every time, with 1-hour cache  
**Recommendation:**
- Increase cache TTL to 6-24 hours (conference content doesn't change frequently)
- Pre-fetch next page in background
- Add loading indicators for slow connections

```python
# In rainfocus.py
CACHE_TTL = 21600  # 6 hours instead of 1 hour

# Add background prefetch
def prefetch_next_page(page, filters):
    """Pre-fetch next page in background thread."""
    import threading
    thread = threading.Thread(
        target=lambda: search_sessions(page=page+1, filters=filters)
    )
    thread.daemon = True
    thread.start()
```

---

## Code Patches

### **Patch 1: Improved Main Menu**

**File:** `addon.py`

Replace the `main_menu()` function:

```python
def main_menu():
    """Show the top-level menu with content-first approach."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    items = [
        ("🔥 Recently Added", build_url("recently_added"), "DefaultRecentlyAddedVideos.png", 
         "Browse newest Cisco Live sessions"),
        ("🎬 Featured Sessions", build_url("featured"), "DefaultMovies.png",
         "Hand-picked popular sessions"),
        ("📚 Browse by Event", build_url("events"), "DefaultVideoPlaylists.png",
         "Browse by Cisco Live event year"),
        ("🔍 Search", build_url("search"), "DefaultAddonsSearch.png",
         "Search all sessions"),
        ("🏷️ Browse by Category", build_url("categories"), "DefaultGenre.png",
         "Browse by technology, level, or type"),
        ("📜 Recently Played", build_url("history"), "DefaultRecentlyAddedVideos.png",
         "Continue watching"),
    ]
    
    for label, url, icon, description in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon, "thumb": icon})
        info_tag = li.getVideoInfoTag()
        info_tag.setPlot(description)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_recently_added():
    """Show newest sessions with video."""
    # Get newest event's sessions
    events = rainfocus.get_events()
    if not events:
        xbmcgui.Dialog().notification(
            "Cisco Live", "No events found", xbmcgui.NOTIFICATION_WARNING
        )
        return
    
    # Show sessions from the most recent event
    latest_event = events[-1]  # Events are reversed in show_events()
    show_session_list(
        filter_key="search.event",
        filter_val=latest_event["id"],
        has_video=True
    )


def show_featured():
    """Show featured/popular sessions."""
    # For now, show all sessions with video, sorted by duration (longest first)
    # In production, this could be a curated list or "most viewed"
    show_session_list(has_video=True, sort_by="duration_long")


def show_categories():
    """Show a sub-menu of category types."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    items = [
        ("Technology", build_url("technologies"), "DefaultGenre.png"),
        ("Technical Level", build_url("levels"), "DefaultProgram.png"),
        ("Session Type", build_url("session_types"), "DefaultVideoPlaylists.png"),
    ]
    
    for label, url, icon in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon})
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# Add to router():
def router():
    """Route to the correct handler based on the action parameter."""
    params = get_params()
    action = params.get("action", "")

    if action == "":
        main_menu()
    elif action == "recently_added":
        show_recently_added()
    elif action == "featured":
        show_featured()
    elif action == "categories":
        show_categories()
    elif action == "events":
        show_events()
    # ... rest of router
```

---

### **Patch 2: Improved Session Display**

**File:** `addon.py`

Replace `_add_session_item()`:

```python
def _add_session_item(item):
    """Add a single session as a playable list item with improved formatting."""
    title = item.get("title", "")
    code = item.get("code", "")
    has_video = item.get("has_video", False)
    
    # Don't show sessions without video by default
    if not has_video and not ADDON.getSettingBool("show_no_video"):
        return
    
    # Primary label: Title only (cleaner for TV)
    label = title
    
    # Build secondary info line (shown as subtitle in most skins)
    info_parts = []
    
    # Add first technology category
    if item.get("technologies"):
        tech = item["technologies"][0]
        info_parts.append(tech)
    
    # Add level with color indicator
    if item.get("level"):
        level = item["level"].replace("Technical Level ", "")
        level_colors = {
            "Introductory": "green",
            "Intermediate": "yellow",
            "Advanced": "orange",
            "Expert": "red",
        }
        color = level_colors.get(level, "white")
        info_parts.append(f"[COLOR {color}]●[/COLOR] {level}")
    
    # Add duration
    if item.get("duration"):
        mins = int(item["duration"] / 60)
        info_parts.append(f"{mins} min")
    
    subtitle = " • ".join(info_parts)
    
    # Create list item
    li = xbmcgui.ListItem(label)
    li.setLabel2(subtitle)  # Secondary info line
    
    # Build detailed plot
    speakers = ", ".join(item.get("speakers", []))
    abstract = item.get("abstract", "")
    event = item.get("event", "")
    techs = ", ".join(item.get("technologies", []))
    
    plot_parts = []
    if event:
        plot_parts.append(f"[B]Event:[/B] {event}")
    if code:
        plot_parts.append(f"[B]Session:[/B] {code}")
    if item.get("level"):
        plot_parts.append(f"[B]Level:[/B] {item['level']}")
    if techs:
        plot_parts.append(f"[B]Technology:[/B] {techs}")
    if speakers:
        plot_parts.append(f"[B]Speaker(s):[/B] {speakers}")
    if abstract:
        plot_parts.append("")
        plot_parts.append(abstract)
    
    # Set video info tag
    info_tag = li.getVideoInfoTag()
    info_tag.setTitle(title)
    info_tag.setPlot("\n".join(plot_parts))
    
    if item.get("duration"):
        info_tag.setDuration(int(item["duration"]))
    
    if event:
        info_tag.setStudios([event])
    
    # Set thumbnail (speaker photo or default)
    photos = item.get("speaker_photos", [])
    if photos and photos[0]:
        li.setArt({"thumb": photos[0], "poster": photos[0]})
    else:
        # Use default video icon
        li.setArt({"thumb": "DefaultVideo.png"})
    
    # Add fanart (use plugin fanart)
    fanart_path = os.path.join(
        xbmcaddon.Addon().getAddonInfo("path"),
        "resources", "media", "fanart.jpg"
    )
    if os.path.exists(fanart_path):
        li.setArt({"fanart": fanart_path})
    
    if has_video:
        li.setProperty("IsPlayable", "true")
        video_id = item["video_ids"][0]
        url = build_url("play", video_id=video_id, title=label)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)
    else:
        # No video - make it clear in the label
        li.setLabel(f"[COLOR gray]{label}[/COLOR]")
        li.setLabel2(f"[COLOR gray]{subtitle} • No Video[/COLOR]")
        url = build_url("info", session_id=item.get("id", ""))
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)
```

---

### **Patch 3: Better Pagination**

**File:** `addon.py`

In `show_session_list()`, replace the pagination section:

```python
# Better pagination UI
next_offset = (page + 1) * PAGE_SIZE
if next_offset < total:
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    current_page = page + 1
    
    # Simple, friendly pagination label
    if total_pages <= 10:
        label = f"▶️ More sessions... (page {current_page + 1} of {total_pages})"
    else:
        label = "▶️ Load more sessions..."
    
    li = xbmcgui.ListItem(label)
    li.setArt({"icon": "DefaultFolderBack.png"})
    
    params = {"page": str(page + 1)}
    if filter_key:
        params["filter_key"] = filter_key
        params["filter_val"] = filter_val
    if has_video:
        params["has_video"] = "1"
    if search_text:
        params["search_text"] = search_text
    
    url = build_url("list", **params)
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
```

---

### **Patch 4: Add Settings**

**File:** `resources/settings.xml`

Add new settings:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings version="1">
    <section id="plugin.video.ciscolive">
        <category id="general" label="General">
            <group id="1">
                <setting id="show_no_video" type="boolean" label="Show sessions without video" help="Display sessions that don't have video recordings" default="false"/>
                <setting id="page_size" type="integer" label="Items per page" default="50">
                    <level>1</level>
                    <constraints>
                        <minimum>10</minimum>
                        <maximum>100</maximum>
                        <step>10</step>
                    </constraints>
                </setting>
            </group>
        </category>
        
        <category id="playback" label="Playback">
            <group id="1">
                <setting id="prefer_hls" type="boolean" label="Prefer HLS streams" help="Use HLS streaming when available (recommended)" default="true"/>
                <setting id="auto_advance" type="boolean" label="Auto-play next session" help="Automatically play the next session in a list" default="false"/>
            </group>
        </category>
        
        <category id="appearance" label="Appearance">
            <group id="1">
                <setting id="show_level_colors" type="boolean" label="Color-code by technical level" help="Show colored indicators for session difficulty" default="true"/>
                <setting id="show_duration" type="boolean" label="Show session duration" help="Display video length in session info" default="true"/>
            </group>
        </category>
    </section>
</settings>
```

---

## Visual Assets Created

✅ **icon.png** (256x256)
- Professional play-button design
- Dark theme with Cisco teal/blue accents
- Signal wave bars representing "Live"
- Clean, recognizable from TV distance

✅ **fanart.jpg** (1920x1080)  
- Modern gradient background (dark theme)
- Abstract geometric network design
- Large central play button
- "CISCO LIVE ON-DEMAND" text
- Professional conference aesthetic

Both assets saved to: `resources/media/`

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Create icon.png and fanart.jpg
2. Improve session labels (remove code prefix)
3. Add color indicators for technical level
4. Improve pagination text
5. Hide sessions without video by default

### Phase 2: Core UX (3-4 hours)
1. Restructure main menu (content-first)
2. Add "Recently Added" view
3. Add "Featured Sessions" view
4. Consolidate category browsing
5. Add settings for user preferences

### Phase 3: Polish (2-3 hours)
1. Add local watch history
2. Implement better thumbnails
3. Add sorting options
4. Performance optimizations
5. Keyboard shortcuts

---

## Testing Checklist

Before deploying to production:

- [ ] Test on actual TV (not just desktop Kodi)
- [ ] Verify all sessions are playable
- [ ] Test pagination with large result sets (1000+ items)
- [ ] Test search with special characters
- [ ] Verify cache expiration works correctly
- [ ] Test with slow network connection
- [ ] Ensure settings persist across restarts
- [ ] Test with different Kodi skins (Estuary, Confluence, Aeon Nox)
- [ ] Verify remote control navigation (no "dead ends")
- [ ] Test "Recently Played" with empty history

---

## Conclusion

The Cisco Live plugin has a solid foundation. With these UX improvements, it will transform from a **functional catalog browser** into a **TV-optimized content discovery platform**.

**Key Takeaways:**
1. **Content first** - Show videos, not menus
2. **Reduce friction** - Fewer clicks to play
3. **Visual hierarchy** - Make the important stuff obvious
4. **Progressive disclosure** - Simple by default, powerful when needed
5. **TV-native design** - 10-foot UI principles throughout

Implementing these changes will make the plugin feel native to Kodi and provide a premium viewing experience for Cisco Live's extensive video library.

---

**Generated by:** UX Design Agent  
**Date:** February 11, 2026  
**Plugin:** plugin.video.ciscolive v1.0.0
