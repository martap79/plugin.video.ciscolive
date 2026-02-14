"""
Sample implementation showing key UX improvements applied to addon.py

This is a reference implementation demonstrating the major changes.
Copy sections into your addon.py as needed.
"""

# ============================================================================
# IMPROVED MAIN MENU - Content First Approach
# ============================================================================

def main_menu():
    """Show the top-level menu with content-first approach."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    # Use emoji/icons for visual distinction on supported skins
    items = [
        ("🔥 Recently Added", build_url("recently_added"), "DefaultRecentlyAddedVideos.png", 
         "Browse newest Cisco Live sessions with video"),
        
        ("🎬 Featured Sessions", build_url("featured"), "DefaultMovies.png",
         "Hand-picked popular and trending sessions"),
        
        ("📚 Browse by Event", build_url("events"), "DefaultVideoPlaylists.png",
         "Browse by Cisco Live event year (2024, 2023, ...)"),
        
        ("🔍 Search", build_url("search"), "DefaultAddonsSearch.png",
         "Search all sessions by keyword"),
        
        ("🏷️ Browse by Category", build_url("categories"), "DefaultGenre.png",
         "Browse by technology, level, or session type"),
        
        ("📜 Continue Watching", build_url("history"), "DefaultRecentlyAddedVideos.png",
         "Resume previously played sessions"),
    ]
    
    for label, url, icon, description in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon, "thumb": icon})
        
        # Add description as plot for context menus
        info_tag = li.getVideoInfoTag()
        info_tag.setPlot(description)
        
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ============================================================================
# NEW VIEWS
# ============================================================================

def show_recently_added():
    """Show newest sessions with video from the most recent event."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    # Get the most recent event
    events = rainfocus.get_events()
    if not events:
        xbmcgui.Dialog().notification(
            "Cisco Live", "No events found", xbmcgui.NOTIFICATION_WARNING
        )
        return
    
    # Events are already reversed (newest first) in show_events()
    latest_event = events[-1]
    
    # Show sessions from latest event with video
    show_session_list(
        filter_key="search.event",
        filter_val=latest_event["id"],
        has_video=True
    )


def show_featured():
    """Show featured/popular sessions."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    # Option 1: Hand-picked list (maintain this list manually)
    featured_session_codes = [
        # Example: manually curate top sessions
        # These would be session codes or IDs
    ]
    
    if featured_session_codes:
        for code in featured_session_codes:
            # Fetch and display each featured session
            # This requires adding a search by code function to rainfocus.py
            pass
    else:
        # Option 2: Dynamic - show longest sessions (usually keynotes/important)
        # or most recent from all events
        show_session_list(has_video=True, sort_by="duration_long")


def show_categories():
    """Show a sub-menu of category types (consolidates 3 menus into 1)."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    items = [
        ("Technology", build_url("technologies"), "DefaultGenre.png",
         "Browse by technology category (Security, Data Center, ...)"),
        ("Technical Level", build_url("levels"), "DefaultProgram.png",
         "Browse by difficulty (Introductory, Intermediate, Advanced, Expert)"),
        ("Session Type", build_url("session_types"), "DefaultVideoPlaylists.png",
         "Browse by session type (Breakout, Lab, ...)"),
    ]
    
    for label, url, icon, description in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon})
        info_tag = li.getVideoInfoTag()
        info_tag.setPlot(description)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_history():
    """Show recently played sessions (requires watch history tracking)."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    # Placeholder - would require implementing history tracking
    # See history.py example in UX_REVIEW.md
    xbmcgui.Dialog().notification(
        "Cisco Live", "Watch history coming soon!", xbmcgui.NOTIFICATION_INFO
    )
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ============================================================================
# IMPROVED SESSION DISPLAY
# ============================================================================

def _add_session_item(item):
    """Add a single session as a playable list item with improved formatting."""
    title = item.get("title", "")
    code = item.get("code", "")
    has_video = item.get("has_video", False)
    
    # Check if user wants to see sessions without video
    show_no_video = ADDON.getSettingBool("show_no_video")
    if not has_video and not show_no_video:
        return  # Skip this item
    
    # Primary label: Title only (much cleaner for TV)
    label = title
    
    # Build secondary info line (shown as subtitle in most skins)
    info_parts = []
    
    # Add first technology category only (keep it concise)
    if item.get("technologies"):
        tech = item["technologies"][0]
        # Shorten common long names
        tech = tech.replace("and ", "& ")
        if len(tech) > 20:
            tech = tech[:17] + "..."
        info_parts.append(tech)
    
    # Add level with color indicator (if enabled in settings)
    if item.get("level"):
        level = item["level"].replace("Technical Level ", "").strip()
        
        if ADDON.getSettingBool("show_level_colors"):
            # Color-coded difficulty indicators
            level_colors = {
                "Introductory": "green",
                "Intermediate": "yellow",
                "Advanced": "orange",
                "Expert": "red",
            }
            color = level_colors.get(level, "white")
            level_display = f"[COLOR {color}]●[/COLOR] {level}"
        else:
            level_display = level
        
        info_parts.append(level_display)
    
    # Add duration (if enabled in settings)
    if item.get("duration") and ADDON.getSettingBool("show_duration"):
        mins = int(item["duration"] / 60)
        if mins > 0:
            info_parts.append(f"{mins} min")
    
    subtitle = " • ".join(info_parts)
    
    # Create list item
    li = xbmcgui.ListItem(label)
    li.setLabel2(subtitle)  # Secondary info line
    
    # Build detailed plot for info screen
    speakers = ", ".join(item.get("speakers", []))
    abstract = item.get("abstract", "")
    event = item.get("event", "")
    techs = ", ".join(item.get("technologies", []))
    
    plot_parts = []
    if event:
        plot_parts.append(f"[B]Event:[/B] {event}")
    if code:
        plot_parts.append(f"[B]Session Code:[/B] {code}")
    if item.get("level"):
        plot_parts.append(f"[B]Technical Level:[/B] {item['level']}")
    if techs:
        plot_parts.append(f"[B]Technology:[/B] {techs}")
    if item.get("session_type"):
        plot_parts.append(f"[B]Type:[/B] {item['session_type']}")
    if speakers:
        plot_parts.append(f"[B]Speaker(s):[/B] {speakers}")
    if abstract:
        plot_parts.append("")
        plot_parts.append(abstract)
    
    # Set video info tag (Kodi v20+ API)
    info_tag = li.getVideoInfoTag()
    info_tag.setTitle(title)
    info_tag.setPlot("\n".join(plot_parts))
    info_tag.setGenres(item.get("technologies", []))
    
    if item.get("duration"):
        info_tag.setDuration(int(item["duration"]))
    
    if event:
        info_tag.setStudios([event])
    
    # Set thumbnail
    photos = item.get("speaker_photos", [])
    if photos and photos[0]:
        li.setArt({"thumb": photos[0], "poster": photos[0]})
    else:
        # Use default video icon
        li.setArt({"thumb": "DefaultVideo.png"})
    
    # Add plugin fanart as background
    fanart_path = os.path.join(
        ADDON.getAddonInfo("path"),
        "resources", "media", "fanart.jpg"
    )
    if os.path.exists(fanart_path):
        li.setArt({"fanart": fanart_path})
    
    # Different behavior for sessions with/without video
    if has_video:
        li.setProperty("IsPlayable", "true")
        video_id = item["video_ids"][0]
        url = build_url("play", video_id=video_id, title=label)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)
    else:
        # No video - make it visually distinct
        li.setLabel(f"[COLOR gray]{label}[/COLOR]")
        li.setLabel2(f"[COLOR gray]{subtitle} • No Video Available[/COLOR]")
        
        # Show info dialog instead of trying to play
        url = build_url("info", session_id=item.get("id", ""))
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)


# ============================================================================
# IMPROVED PAGINATION
# ============================================================================

def show_session_list(page=0, filter_key=None, filter_val=None,
                       has_video=False, search_text=None, sort_by=None):
    """List sessions with optional filters and pagination."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    
    # Get page size from settings (allow user customization)
    page_size = ADDON.getSettingInt("page_size") or PAGE_SIZE
    
    filters = {}
    if filter_key and filter_val:
        filters[filter_key] = filter_val
    if search_text:
        filters["search"] = search_text

    result = rainfocus.search_sessions(
        page=page, 
        page_size=page_size, 
        filters=filters
    )
    items = result.get("items", [])
    total = result.get("total", 0)

    # Filter to sessions with video if requested
    if has_video:
        items = [i for i in items if i.get("has_video")]

    # Client-side sorting (if rainfocus.py doesn't support it)
    if sort_by == "duration_long":
        items.sort(key=lambda x: x.get("duration", 0), reverse=True)
    elif sort_by == "duration_short":
        items.sort(key=lambda x: x.get("duration", 0))
    elif sort_by == "title":
        items.sort(key=lambda x: x.get("title", "").lower())

    # Add each session
    for item in items:
        _add_session_item(item)

    # Improved pagination UI
    next_offset = (page + 1) * page_size
    if next_offset < total:
        total_pages = (total + page_size - 1) // page_size  # Ceiling division
        current_page = page + 1
        
        # Friendly pagination label
        if total_pages <= 10:
            # Show page numbers for small result sets
            label = f"▶️ More sessions... (page {current_page + 1} of {total_pages})"
        else:
            # Just "Load more" for large result sets
            label = "▶️ Load more sessions..."
        
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": "DefaultFolderBack.png"})
        
        # Build next page URL
        params = {"page": str(page + 1)}
        if filter_key:
            params["filter_key"] = filter_key
            params["filter_val"] = filter_val
        if has_video:
            params["has_video"] = "1"
        if search_text:
            params["search_text"] = search_text
        if sort_by:
            params["sort_by"] = sort_by
        
        url = build_url("list", **params)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    # Enable Kodi's built-in sorting
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_DURATION)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ============================================================================
# UPDATED ROUTER
# ============================================================================

def router():
    """Route to the correct handler based on the action parameter."""
    params = get_params()
    action = params.get("action", "")

    if action == "":
        main_menu()
    
    # New views
    elif action == "recently_added":
        show_recently_added()
    elif action == "featured":
        show_featured()
    elif action == "categories":
        show_categories()
    elif action == "history":
        show_history()
    
    # Existing views
    elif action == "events":
        show_events()
    elif action == "technologies":
        show_technologies()
    elif action == "levels":
        show_levels()
    elif action == "session_types":
        show_session_types()
    elif action == "search":
        do_search()
    elif action == "list":
        page = int(params.get("page", "0"))
        fk = params.get("filter_key")
        fv = params.get("filter_val")
        hv = params.get("has_video", "") == "1"
        st = params.get("search_text")
        sb = params.get("sort_by")
        show_session_list(page=page, filter_key=fk, filter_val=fv,
                          has_video=hv, search_text=st, sort_by=sb)
    elif action == "play":
        vid = params.get("video_id", "")
        title = params.get("title", "")
        play_video(vid, title)
    elif action == "info":
        sid = params.get("session_id", "")
        show_info(sid)
    else:
        main_menu()


# ============================================================================
# USAGE NOTES
# ============================================================================
"""
To integrate these improvements:

1. Copy the improved functions above into your addon.py
2. Update resources/settings.xml with the new settings (see UX_REVIEW.md)
3. Test each view individually:
   - Main menu should show new items
   - Recently Added should show latest event sessions
   - Session labels should be cleaner
   - Pagination should be friendlier
   
4. Optional enhancements:
   - Implement watch history tracking (see UX_REVIEW.md)
   - Add video thumbnail fetching from Brightcove
   - Add manual featured session curation
   - Implement sorting in rainfocus.py API calls

5. Test on actual TV with remote control to verify:
   - Text is readable from 10 feet
   - Navigation is intuitive
   - No "dead ends" in menu structure
   - All videos play correctly

Settings to add to resources/settings.xml:
- show_no_video (boolean, default: false)
- page_size (integer, default: 50, range: 10-100)
- prefer_hls (boolean, default: true)
- show_level_colors (boolean, default: true)
- show_duration (boolean, default: true)

See UX_REVIEW.md for complete settings XML code.
"""
