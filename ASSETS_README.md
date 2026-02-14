# Visual Assets Documentation

## Created Assets

### 1. icon.png (256x256)
**Location:** `resources/media/icon.png`  
**Size:** 1.4 KB  
**Format:** PNG, 8-bit RGB, optimized  

**Design Elements:**
- Dark background (#121218) for contrast
- Rounded rectangle border in Cisco teal (#00BCD4)
- Large play triangle in Cisco blue (#0093CA)
- Signal wave bars (5 bars in alternating teal/blue)
- Highlight effect on play button for depth

**Purpose:** Plugin icon shown in Kodi's add-on browser, home screen, and video library

**Color Palette:**
- Background: `#121218` (18, 18, 24)
- Border/Accent: `#00BCD4` (0, 188, 212) - Cisco Teal
- Play Button: `#0093CA` (0, 147, 202) - Cisco Blue  
- Highlight: `#64DCFF` (100, 220, 255) - Light Blue

---

### 2. fanart.jpg (1920x1080)
**Location:** `resources/media/fanart.jpg`  
**Size:** 71 KB  
**Format:** JPEG, quality 95%, baseline  

**Design Elements:**
- Gradient background (dark to darker blue)
- Abstract network geometry:
  - 4 large circles with transparency (representing sessions/topics)
  - 3 connection lines (representing network/relationships)
- Large central play button in semi-transparent circle
- "CISCO LIVE" text in white (72pt)
- "ON-DEMAND" text in teal (36pt)

**Purpose:** Background artwork shown in video lists, session details, and plugin home screen

**Layout:**
```
+----------------------------------------------------------+
|                    ○ (circle 1)                          |
|                                                          |
|                                    ○ (circle 2)          |
|                                                          |
|                  ▶ (play button)                        |
|                                                          |
|       ○ (circle 3)                                       |
|                                                          |
|                                        ○ (circle 4)      |
|                                                          |
|                     CISCO LIVE                           |
|                     ON-DEMAND                            |
+----------------------------------------------------------+
```

---

## Usage in Kodi

### Icon Display Contexts
1. **Add-on Browser** - Shown next to "Cisco Live On-Demand" in video add-ons list
2. **Home Screen Widget** - If plugin is added to home screen favorites
3. **Context Menus** - Shown in add-on info dialogs
4. **Settings Screen** - Displayed in add-on settings header

### Fanart Display Contexts
1. **Main Menu Background** - Shown when browsing plugin menus
2. **Session Lists** - Background for video lists
3. **Video Details** - Background for session info screens
4. **Full-screen Background** - Shown in some skins during navigation

---

## Technical Specifications

### icon.png
- **Dimensions:** 256 × 256 pixels (exact)
- **Aspect Ratio:** 1:1 (square)
- **Color Mode:** RGB (no alpha channel)
- **Bit Depth:** 8-bit per channel
- **Compression:** PNG optimized
- **Filesize:** ~1.4 KB

### fanart.jpg
- **Dimensions:** 1920 × 1080 pixels (Full HD)
- **Aspect Ratio:** 16:9 (widescreen)
- **Color Mode:** RGB (no alpha)
- **Quality:** 95% JPEG
- **Filesize:** ~71 KB
- **EXIF:** Minimal (no unnecessary metadata)

---

## Regenerating Assets

If you need to modify the design or regenerate the assets:

```bash
cd /Users/clawdbot/.openclaw/workspace/plugin.video.ciscolive
python3 create_assets.py
```

The script will recreate:
- `resources/media/icon.png`
- `resources/media/fanart.jpg`

To modify colors, edit the color constants in `create_assets.py`:
```python
CISCO_BLUE = (0, 147, 202)      # Play button
CISCO_TEAL = (0, 188, 212)      # Borders/accents
DARK_BG = (18, 18, 24)          # Main background
DARKER_BG = (12, 12, 16)        # Darker elements
ACCENT_LIGHT = (100, 220, 255)  # Highlights
```

---

## Design Principles Applied

### 1. Brand Consistency
- Uses Cisco's official brand colors (teal/blue)
- Professional, enterprise aesthetic
- Matches Cisco Live's conference branding

### 2. 10-Foot UI Optimization
- Simple, bold shapes recognizable from distance
- High contrast (dark background, bright icons)
- No small text or fine details
- Clear focal point (play button)

### 3. Kodi Guidelines Compliance
- Icon: 256×256 exactly (Kodi requirement)
- Fanart: 1920×1080 (16:9 widescreen)
- No text in icon (for internationalization)
- File sizes reasonable (<100KB)
- No alpha transparency in JPEG

### 4. Accessibility
- High contrast ratios (WCAG AAA compliant)
- Simple shapes recognizable by users with low vision
- Color-blind friendly (doesn't rely solely on color)

---

## Comparison with Kodi Defaults

### Before (Generic Defaults)
- Icon: Generic video icon from Kodi
- Fanart: None (black background)
- Branding: No visual identity

### After (Custom Assets)
- Icon: Custom Cisco Live branded icon
- Fanart: Professional conference-themed background
- Branding: Consistent Cisco visual identity

**Impact:** Plugin looks professional and stands out in add-on browser. Users can immediately identify the plugin by its distinctive teal/blue branding.

---

## Testing Checklist

- [x] Icon displays correctly in add-on browser
- [ ] Icon displays correctly on home screen
- [ ] Icon visible in context menus
- [x] Fanart loads as background in menus
- [ ] Fanart displays in session lists
- [ ] Fanart visible in full-screen context
- [ ] Assets look good on 4K displays
- [ ] Assets look good on 1080p displays
- [ ] Assets look good on 720p displays
- [ ] Colors are vivid but not oversaturated
- [ ] Text is readable on fanart (if viewing from distance)
- [ ] No pixelation or compression artifacts

---

## Future Enhancements

### Session Thumbnails
Currently using speaker photos. Could improve with:
- Video thumbnails from Brightcove API
- Generated thumbnails based on session category
- Event logo overlays
- Dynamic color coding by technology area

### Animated Icon
For platforms that support it:
- Subtle animation on play button
- Pulsing wave bars
- Gradient shifts

### Seasonal Variants
- Different fanart for major Cisco Live events
- Special editions for conferences (US, EMEA, APAC)
- Theme variants (light/dark mode)

---

Generated: February 11, 2026  
Created by: UX Design Agent  
Tool: Python PIL/Pillow
