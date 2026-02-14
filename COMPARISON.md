# Cisco Live Plugin - Before & After Comparison

## Main Menu Flow

### BEFORE (Current)
```
┌─────────────────────────────────────┐
│  Cisco Live On-Demand               │
├─────────────────────────────────────┤
│  Browse by Event                    │
│  Browse by Technology               │
│  Browse by Level                    │
│  Browse by Session Type             │
│  Search                             │
│  All Sessions (with video)          │
└─────────────────────────────────────┘
        ↓ (3 clicks to see content)
┌─────────────────────────────────────┐
│  Select Event                       │
├─────────────────────────────────────┤
│  Cisco Live US 2024                 │
│  Cisco Live EMEA 2023               │
│  ...                                │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Sessions (50 of 1234)              │
├─────────────────────────────────────┤
│  BRKSEC-2011 - Advanced Security... │
│  BRKDCT-3001 - Data Center Arch...  │
│  LTRSEC-1000 - Security Fundamen... │
│  ...                                │
└─────────────────────────────────────┘
```

### AFTER (Proposed)
```
┌─────────────────────────────────────┐
│  Cisco Live On-Demand               │
├─────────────────────────────────────┤
│  🔥 Recently Added                   │  ← Lands here by default
│  🎬 Featured Sessions                │     Shows content immediately
│  📚 Browse by Event                  │
│  🔍 Search                           │
│  🏷️  Browse by Category              │
│  📜 Recently Played                  │
└─────────────────────────────────────┘
        ↓ (1 click to see content)
┌─────────────────────────────────────┐
│  Recently Added Sessions            │
├─────────────────────────────────────┤
│  Advanced Security Implementation   │  ← Clean, readable
│  Security • 🔴 Expert • 45 min      │  ← Visual hierarchy
│                                     │
│  AI-Powered Network Automation      │
│  Automation • 🟡 Intermediate • 60m │
│                                     │
│  Introduction to Cisco DNA          │
│  Infrastructure • 🟢 Intro • 30 min │
│                                     │
│  ▶️ Load more sessions...           │  ← Friendly pagination
└─────────────────────────────────────┘
```

---

## Session Detail View

### BEFORE
```
┌───────────────────────────────────────────────────┐
│  BRKSEC-2011 - Advanced Security Implementation   │
│  with Cisco Firepower Threat Defense              │
├───────────────────────────────────────────────────┤
│  Event: Cisco Live US 2024                        │
│  Level: Expert                                    │
│  Speaker(s): John Doe, Jane Smith                 │
│                                                   │
│  This session covers advanced topics in security  │
│  architecture and deployment strategies...        │
└───────────────────────────────────────────────────┘
```

### AFTER
```
┌───────────────────────────────────────────────────┐
│  Advanced Security Implementation                 │  ← Title only
│  Security • 🔴 Expert • 45 min                    │  ← At-a-glance info
├───────────────────────────────────────────────────┤
│  Event: Cisco Live US 2024                        │
│  Session: BRKSEC-2011                             │  ← Code in details
│  Level: Expert                                    │
│  Technology: Security                             │
│  Speaker(s): John Doe, Jane Smith                 │
│                                                   │
│  This session covers advanced topics in security  │
│  architecture and deployment strategies...        │
└───────────────────────────────────────────────────┘
```

---

## Pagination

### BEFORE
```
┌─────────────────────────────────────┐
│  ...sessions...                     │
│                                     │
│  [COLOR yellow]Next page (50 / 1234)│  ← Technical, not friendly
│  [/COLOR]                           │
└─────────────────────────────────────┘
```

### AFTER
```
┌─────────────────────────────────────┐
│  ...sessions...                     │
│                                     │
│  ▶️ Load more sessions...           │  ← Clear, simple
└─────────────────────────────────────┘
```

---

## Menu Depth Reduction

### BEFORE: 3-4 clicks to content
```
Main Menu (6 filter options)
    → Choose a filter category
        → Choose a specific filter value
            → See sessions
                → Play video
```

### AFTER: 1-2 clicks to content
```
Main Menu (Recently Added shows immediately)
    → Play video

OR

Main Menu
    → Browse by Event
        → Play video
```

---

## Color Coding (Technical Level)

### Visual Indicators

```
🟢 Introductory    - Green dot for beginners
🟡 Intermediate    - Yellow dot for intermediate users
🟠 Advanced        - Orange dot for experienced users
🔴 Expert          - Red dot for experts
```

Example in list:
```
Introduction to SD-WAN
Infrastructure • 🟢 Introductory • 30 min

Advanced Routing Protocols
Routing • 🟠 Advanced • 60 min

Expert-Level Troubleshooting
Service Provider • 🔴 Expert • 90 min
```

---

## Settings Organization

### New Settings Structure
```
⚙️ Settings
├─ General
│   ├─ Show sessions without video [OFF]
│   └─ Items per page [50]
│
├─ Playback
│   ├─ Prefer HLS streams [ON]
│   └─ Auto-play next session [OFF]
│
└─ Appearance
    ├─ Color-code by technical level [ON]
    └─ Show session duration [ON]
```

---

## Information Architecture Changes

### BEFORE (Filter-First)
```
Main Menu
├─ Browse by Event
├─ Browse by Technology
├─ Browse by Level
├─ Browse by Session Type
├─ Search
└─ All Sessions (with video)
```
**Problem:** Too many choices, no content preview

### AFTER (Content-First)
```
Main Menu
├─ 🔥 Recently Added          [DEFAULT VIEW]
├─ 🎬 Featured Sessions
├─ 📚 Browse by Event
├─ 🔍 Search
├─ 🏷️  Browse by Category
│   ├─ Technology
│   ├─ Technical Level
│   └─ Session Type
└─ 📜 Recently Played
```
**Benefit:** Content is immediately visible, filters are discoverable

---

## Key Metrics Improvement

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Clicks to first video | 3-4 | 1 | 66-75% reduction |
| Menu items on home | 6 | 6 | Same (reorganized) |
| Sessions without video shown | All | Optional | User choice |
| Visual distinction of difficulty | None | Color-coded | 100% improvement |
| Content preview on home | None | 50 items | Instant discovery |

---

## 10-Foot UI Principles Applied

1. **Big, readable text**
   - Removed session codes from primary label
   - Increased importance of title
   - Added subtitle line for metadata

2. **Clear visual hierarchy**
   - Title (largest)
   - Category/Level/Duration (medium, with colors)
   - Details (in info panel)

3. **Minimal clicks**
   - Content on home screen
   - Reduced menu depth
   - Smart defaults (hide no-video sessions)

4. **Remote-friendly navigation**
   - Linear menu structure
   - No deep nesting
   - Clear "back" path

5. **Scannable lists**
   - Consistent format
   - Color-coded difficulty
   - Duration visible
   - Clear pagination

---

## Files Modified/Created

### Created ✅
- `resources/media/icon.png` (256x256)
- `resources/media/fanart.jpg` (1920x1080)
- `UX_REVIEW.md` (this comprehensive guide)
- `create_assets.py` (asset generation script)
- `COMPARISON.md` (this file)

### To Modify 📝
- `addon.py` (main navigation and display logic)
- `resources/settings.xml` (add new user preferences)
- `resources/lib/rainfocus.py` (optional: add sorting support)

---

**Next Steps:**
1. Review the proposed changes in `UX_REVIEW.md`
2. Apply the code patches incrementally
3. Test on actual TV hardware with remote
4. Iterate based on user feedback
5. Consider adding watch history tracking
6. Explore video thumbnail extraction from Brightcove

---

Generated: February 11, 2026
