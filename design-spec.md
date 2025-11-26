# Design Specification: Blockchair Downloader UI/UX Redesign

## Overview
Redesign of the Blockchair Downloader application from a single scrollable vertical layout to a modern, multi-view horizontal interface that fits on screen without scrolling. The redesign focuses on a wizard-like workflow that guides users through configuration, size calculation, and download progress monitoring.

**Target Window Size:** 1000x800px (or similar reasonable dimensions)
**Design Philosophy:** Wizard-based workflow, no scrolling, efficient horizontal space usage, modern dark mode aesthetic

---

## Current State Analysis

### Current UI Workflow
1. User selects output directory
2. User selects date range (with preset buttons)
3. User selects tables to download (checkboxes)
4. User optionally enables "Remove .gz" option
5. User clicks "Calculate Size" to see download size estimate
6. User clicks "Start Download" to begin
7. Progress bars and log display download status

### Problems Identified
- **Vertical scrolling required** - All elements stacked vertically
- **Poor space utilization** - Horizontal space underused
- **Unclear workflow** - All options visible simultaneously
- **No clear progression** - Configuration and progress mixed together
- **Overwhelming first impression** - Too many options at once

---

## Proposed Solution: Three-View Wizard

### Design Concept
Transform the application into a **3-step wizard** with distinct views:

**View 1: Configuration** → **View 2: Size Calculation** → **View 3: Download Progress**

Each view fits within 1000x800px without scrolling. Navigation uses a combination of:
- **Progress stepper** (top of window) showing: Configure → Calculate → Download
- **Action buttons** (bottom of window) for navigation: Back, Next, Start Download
- **Automatic transitions** when actions complete

---

## User Flow

### Entry Point
- Application launches directly to View 1 (Configuration)
- Stepper at top shows: **1. Configure** (active) → 2. Calculate → 3. Download

### Main Flow

**Step 1: Configuration View**
1. User lands on Configuration view
2. User configures:
   - Output directory
   - Date range (presets or custom dates)
   - Tables to download (checkboxes with descriptions)
   - Advanced options (Remove .gz)
3. User clicks "Next: Calculate Size" button
4. → Automatic transition to View 2

**Step 2: Size Calculation View**
1. View 2 loads with calculating spinner
2. Automatic size calculation runs in background
3. Results display:
   - Total download size (prominent)
   - Breakdown by table (Blocks, Transactions, Outputs)
   - Estimated time (based on connection speed)
   - Disk space warning (if insufficient)
4. User reviews information
5. User clicks:
   - "Back" to modify configuration → Returns to View 1
   - "Start Download" to proceed → Transition to View 3

**Step 3: Download Progress View**
1. Download begins automatically
2. Real-time progress display:
   - Overall progress bar (0-100%)
   - Per-table progress bars
   - Download speed, ETA, downloaded/total size
   - Live log of operations
3. User can:
   - "Pause" download (pause/resume toggle)
   - "Cancel" download (with confirmation dialog)
4. On completion:
   - Success message with summary
   - "Open Output Folder" button
   - "Start New Download" button (returns to View 1)

### Alternative Flows
- **Insufficient disk space**: Warning on View 2, cannot proceed until resolved
- **Network error**: Error displayed on View 3 with "Retry" option
- **Cancel during calculation**: Returns to View 1
- **Cancel during download**: Confirmation dialog → Cleanup → Return to View 1

### Exit Points
- Success: View 3 completion screen with "Done" button
- Cancel: Return to View 1 to start over
- Error: Error state with "Retry" or "Back to Configuration" options

---

## Wireframes

### View 1: Configuration (1000x800px)

```
┌────────────────────────────────────────────────────────────────────┐
│  Blockchair Downloader                                    [_][□][X] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Progress Stepper (horizontal)                               │  │
│  │                                                               │  │
│  │  ●━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━●                          │  │
│  │  1. Configure        2. Calculate      3. Download            │  │
│  │  (active - blue)     (inactive)        (inactive)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Configuration                                              │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────┐   │   │
│  │ │ Output Directory                                    │   │   │
│  │ │ ┌────────────────────────────────────┐  ┌────────┐ │   │   │
│  │ │ │ /Users/roman/downloads/blockchair  │  │ Browse │ │   │   │
│  │ │ └────────────────────────────────────┘  └────────┘ │   │   │
│  │ └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │ ┌────────────────────────┐  ┌─────────────────────────┐  │   │
│  │ │ Date Range             │  │ Quick Presets           │  │   │
│  │ │                        │  │                         │  │   │
│  │ │ From:  [2024-01-01]    │  │ [Last 7 Days]           │  │   │
│  │ │        [Calendar icon] │  │ [Last 30 Days]          │  │   │
│  │ │                        │  │ [Last 90 Days]          │  │   │
│  │ │ To:    [2024-01-31]    │  │ [Last Year]             │  │   │
│  │ │        [Calendar icon] │  │ [All Time]              │  │   │
│  │ │                        │  │                         │  │   │
│  │ │ Selected: 31 days      │  │                         │  │   │
│  │ └────────────────────────┘  └─────────────────────────┘  │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────┐   │   │
│  │ │ Tables to Download                                  │   │   │
│  │ │                                                      │   │   │
│  │ │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │   │
│  │ │ │ ☑ Blocks    │  │ ☑ Transact. │  │ ☑ Outputs   │ │   │   │
│  │ │ │             │  │             │  │             │ │   │   │
│  │ │ │ Block data  │  │ Transaction │  │ UTXO data   │ │   │   │
│  │ │ │ & metadata  │  │ details     │  │ & addresses │ │   │   │
│  │ │ │             │  │             │  │             │ │   │   │
│  │ │ │ ~50MB/day   │  │ ~200MB/day  │  │ ~150MB/day  │ │   │   │
│  │ │ └─────────────┘  └─────────────┘  └─────────────┘ │   │   │
│  │ └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────┐   │   │
│  │ │ Advanced Options                                    │   │   │
│  │ │                                                      │   │   │
│  │ │ ☑ Remove .gz files after extraction                │   │   │
│  │ │   (Saves disk space, requires extraction time)      │   │   │
│  │ └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                    [Cancel]  [Next: Calculate│  │
│  │                                                Size →]       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### View 2: Size Calculation (1000x800px)

```
┌────────────────────────────────────────────────────────────────────┐
│  Blockchair Downloader                                    [_][□][X] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Progress Stepper                                            │  │
│  │                                                               │  │
│  │  ✓━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━○                          │  │
│  │  1. Configure        2. Calculate      3. Download            │  │
│  │  (complete)          (active - blue)   (inactive)             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Download Size Calculation                                  │   │
│  │                                                             │   │
│  │        ┌────────────────────────────────────┐              │   │
│  │        │                                    │              │   │
│  │        │   Total Download Size              │              │   │
│  │        │                                    │              │   │
│  │        │        12.4 GB                     │              │   │
│  │        │                                    │              │   │
│  │        │   Estimated Time: 18 minutes       │              │   │
│  │        │   (at 12 MB/s average)             │              │   │
│  │        │                                    │              │   │
│  │        └────────────────────────────────────┘              │   │
│  │                                                             │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Breakdown by Table                                  │   │   │
│  │  │                                                      │   │   │
│  │  │ ┌──────────────┬──────────────┬──────────────────┐ │   │   │
│  │  │ │ Table        │ Size         │ Files            │ │   │   │
│  │  │ ├──────────────┼──────────────┼──────────────────┤ │   │   │
│  │  │ │ Blocks       │ 1.5 GB       │ 31 files         │ │   │   │
│  │  │ │ Transactions │ 6.2 GB       │ 31 files         │ │   │   │
│  │  │ │ Outputs      │ 4.7 GB       │ 31 files         │ │   │   │
│  │  │ └──────────────┴──────────────┴──────────────────┘ │   │   │
│  │  │                                                      │   │   │
│  │  │ Total Files: 93                                     │   │   │
│  │  │ Date Range: 2024-01-01 to 2024-01-31 (31 days)     │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ ✓ Available Disk Space: 50.2 GB                     │   │   │
│  │  │   Sufficient space for download                      │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Configuration Summary                                │   │   │
│  │  │                                                      │   │   │
│  │  │ Output: /Users/roman/downloads/blockchair           │   │   │
│  │  │ Tables: Blocks, Transactions, Outputs               │   │   │
│  │  │ Options: Remove .gz after extraction                │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                           [← Back]  [Start Download]         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### View 3: Download Progress (1000x800px)

```
┌────────────────────────────────────────────────────────────────────┐
│  Blockchair Downloader                                    [_][□][X] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Progress Stepper                                            │  │
│  │                                                               │  │
│  │  ✓━━━━━━━━━━━━━━━✓━━━━━━━━━━━━━━━●                          │  │
│  │  1. Configure        2. Calculate      3. Download            │  │
│  │  (complete)          (complete)        (active - blue)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Downloading Blockchain Data                                │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────────┐ │   │
│  │ │ Overall Progress                                        │ │   │
│  │ │                                                          │ │   │
│  │ │ ████████████████████████░░░░░░░░░░░░░░░░  67%          │ │   │
│  │ │                                                          │ │   │
│  │ │ 62 of 93 files • 8.3 GB of 12.4 GB                      │ │   │
│  │ │ Speed: 11.2 MB/s • ETA: 6 minutes                       │ │   │
│  │ └─────────────────────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  │ ┌──────────────┬──────────────┬──────────────────────────┐ │   │
│  │ │ Left Panel   │ Right Panel: Table Progress              │ │   │
│  │ │ (Stats)      │                                          │ │   │
│  │ ├──────────────┤                                          │ │   │
│  │ │ Current File │ Blocks                                   │ │   │
│  │ │              │ ████████████████████████████████  100%   │ │   │
│  │ │ blocks_2024  │ 31/31 files • 1.5 GB                     │ │   │
│  │ │ -01-25.tsv   │ Status: Complete ✓                       │ │   │
│  │ │ .gz          │                                          │ │   │
│  │ │              │                                          │ │   │
│  │ │ Downloaded   │ Transactions                             │ │   │
│  │ │ 8.3 GB       │ ████████████████████░░░░░░░░  71%        │ │   │
│  │ │              │ 22/31 files • 4.4 GB of 6.2 GB           │ │   │
│  │ │ Remaining    │ Status: Downloading...                   │ │   │
│  │ │ 4.1 GB       │                                          │ │   │
│  │ │              │                                          │ │   │
│  │ │ Files        │ Outputs                                  │ │   │
│  │ │ 62/93        │ █████████░░░░░░░░░░░░░░░░░░  29%         │ │   │
│  │ │              │ 9/31 files • 1.4 GB of 4.7 GB            │ │   │
│  │ │ Elapsed      │ Status: Queued                           │ │   │
│  │ │ 12m 34s      │                                          │ │   │
│  │ └──────────────┴──────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────────┐ │   │
│  │ │ Activity Log                            [Clear Log]     │ │   │
│  │ │                                                          │ │   │
│  │ │ [12:34:56] Downloaded: blocks_2024-01-25.tsv.gz        │ │   │
│  │ │ [12:34:52] Extracting: blocks_2024-01-24.tsv.gz        │ │   │
│  │ │ [12:34:48] Downloaded: blocks_2024-01-24.tsv.gz        │ │   │
│  │ │ [12:34:42] Downloaded: blocks_2024-01-23.tsv.gz        │ │   │
│  │ │ [12:34:38] Starting download: transactions_2024-01...  │ │   │
│  │ │                                                          │ │   │
│  │ │ (Auto-scrolls to bottom, max 100 lines)                │ │   │
│  │ └─────────────────────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                  [Pause]  [Cancel Download]  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### View 3b: Download Complete (Success State)

```
┌────────────────────────────────────────────────────────────────────┐
│  Blockchair Downloader                                    [_][□][X] │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Progress Stepper                                            │  │
│  │                                                               │  │
│  │  ✓━━━━━━━━━━━━━━━✓━━━━━━━━━━━━━━━✓                          │  │
│  │  1. Configure        2. Calculate      3. Download            │  │
│  │  (complete)          (complete)        (complete - green)     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │                                                             │   │
│  │                    ✓ Download Complete!                    │   │
│  │                                                             │   │
│  │              Successfully downloaded 93 files               │   │
│  │                      Total: 12.4 GB                         │   │
│  │                   Time taken: 18m 42s                       │   │
│  │                                                             │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Download Summary                                    │   │   │
│  │  │                                                      │   │   │
│  │  │ Blocks:        31 files • 1.5 GB                    │   │   │
│  │  │ Transactions:  31 files • 6.2 GB                    │   │   │
│  │  │ Outputs:       31 files • 4.7 GB                    │   │   │
│  │  │                                                      │   │   │
│  │  │ Output location:                                     │   │   │
│  │  │ /Users/roman/downloads/blockchair                   │   │   │
│  │  │                                                      │   │   │
│  │  │ .gz files removed: Yes                              │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │ Activity Log                            [Clear Log]  │   │   │
│  │  │                                                      │   │   │
│  │  │ [12:52:18] ✓ All downloads completed successfully   │   │   │
│  │  │ [12:52:15] Removed: outputs_2024-01-31.tsv.gz       │   │   │
│  │  │ [12:52:12] Downloaded: outputs_2024-01-31.tsv.gz    │   │   │
│  │  │ ...                                                  │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              [Open Output Folder]  [Start New Download]      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component Specification

### Framework: CustomTkinter (Current)

Since the application is built with CustomTkinter (CTk), we'll use existing CTk components:

#### View 1: Configuration

**Layout Structure:**
```python
# Main container (no scrolling)
main_frame = ctk.CTkFrame(window)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Stepper at top
stepper_frame = ctk.CTkFrame(main_frame, height=80)
stepper_frame.pack(fill="x", pady=(0, 20))

# Content area (grid layout)
content_frame = ctk.CTkFrame(main_frame)
content_frame.pack(fill="both", expand=True)

# Configure grid weights for responsive layout
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=1)

# Row 0: Output Directory (spans 2 columns)
dir_frame = ctk.CTkFrame(content_frame)
dir_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

# Row 1: Date Range (left) | Quick Presets (right)
date_frame = ctk.CTkFrame(content_frame)
date_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 15))

preset_frame = ctk.CTkFrame(content_frame)
preset_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 15))

# Row 2: Tables to Download (spans 2 columns)
tables_frame = ctk.CTkFrame(content_frame)
tables_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))

# Inner grid for table cards (horizontal arrangement)
blocks_card = ctk.CTkFrame(tables_frame)
blocks_card.grid(row=0, column=0, padx=5)

transactions_card = ctk.CTkFrame(tables_frame)
transactions_card.grid(row=0, column=1, padx=5)

outputs_card = ctk.CTkFrame(tables_frame)
outputs_card.grid(row=0, column=2, padx=5)

# Row 3: Advanced Options (spans 2 columns)
options_frame = ctk.CTkFrame(content_frame)
options_frame.grid(row=3, column=0, columnspan=2, sticky="ew")

# Bottom navigation bar
nav_frame = ctk.CTkFrame(main_frame, height=60)
nav_frame.pack(fill="x", pady=(20, 0))

cancel_btn = ctk.CTkButton(nav_frame, text="Cancel")
cancel_btn.pack(side="left", padx=10)

next_btn = ctk.CTkButton(nav_frame, text="Next: Calculate Size →")
next_btn.pack(side="right", padx=10)
```

**Components:**

1. **Progress Stepper** (Custom Component)
```python
class ProgressStepper(ctk.CTkFrame):
    """
    Horizontal stepper showing: Configure → Calculate → Download

    Props:
    - current_step: int (1, 2, or 3)
    - completed_steps: list[int]

    Visual:
    - Circles with numbers (1, 2, 3)
    - Lines connecting circles
    - Active step: blue circle
    - Completed step: green circle with checkmark
    - Inactive step: gray circle
    """
```

2. **Output Directory Selector**
```python
# CTkFrame with:
# - CTkLabel: "Output Directory"
# - CTkEntry: text field (width=500px)
# - CTkButton: "Browse" button
# - Horizontal arrangement using grid/pack
```

3. **Date Range Picker**
```python
# CTkFrame with:
# - CTkLabel: "From:"
# - CTkEntry: date input (with calendar icon button)
# - CTkLabel: "To:"
# - CTkEntry: date input (with calendar icon button)
# - CTkLabel: "Selected: X days"
# Use DateEntry from tkcalendar if available
```

4. **Quick Presets (Vertical Button Stack)**
```python
# CTkFrame with vertical buttons:
# - CTkButton: "Last 7 Days" (fg_color="transparent", border)
# - CTkButton: "Last 30 Days"
# - CTkButton: "Last 90 Days"
# - CTkButton: "Last Year"
# - CTkButton: "All Time"
# Each button has hover effect and active state
```

5. **Table Selection Cards**
```python
class TableCard(ctk.CTkFrame):
    """
    Card component for each table (Blocks, Transactions, Outputs)

    Layout:
    - CTkCheckBox: Table name (top)
    - CTkLabel: Description (middle, text wrapping)
    - CTkLabel: Estimated size (bottom, muted color)

    Visual:
    - Border highlight when checked
    - Card size: ~280px width, auto height
    """
```

6. **Advanced Options**
```python
# CTkFrame with:
# - CTkCheckBox: "Remove .gz files after extraction"
# - CTkLabel: Help text (smaller font, muted color)
```

#### View 2: Size Calculation

**Layout Structure:**
```python
# Main container
main_frame = ctk.CTkFrame(window)

# Stepper at top (same as View 1)
stepper_frame = ProgressStepper(main_frame, current_step=2, completed_steps=[1])

# Content area (centered layout)
content_frame = ctk.CTkFrame(main_frame)
content_frame.pack(fill="both", expand=True)

# Center content using grid
content_frame.grid_rowconfigure(0, weight=1)
content_frame.grid_rowconfigure(1, weight=0)
content_frame.grid_rowconfigure(2, weight=1)
content_frame.grid_columnconfigure(0, weight=1)

# Large size display (centered)
size_display_frame = ctk.CTkFrame(content_frame)
size_display_frame.grid(row=1, column=0)

# CTkLabel: "Total Download Size"
# CTkLabel: "12.4 GB" (large font, bold)
# CTkLabel: "Estimated Time: 18 minutes"

# Breakdown table (below size display)
breakdown_frame = ctk.CTkFrame(content_frame)
breakdown_frame.grid(row=2, column=0, pady=20)

# Use CTkFrame with grid for table layout
# Headers: Table | Size | Files
# Rows: Data for each table

# Configuration summary (bottom)
summary_frame = ctk.CTkFrame(content_frame)
summary_frame.grid(row=3, column=0)

# Bottom navigation
nav_frame = ctk.CTkFrame(main_frame)
back_btn = ctk.CTkButton(nav_frame, text="← Back")
start_btn = ctk.CTkButton(nav_frame, text="Start Download")
```

**Components:**

1. **Size Display Card** (Large, Centered)
```python
class SizeDisplayCard(ctk.CTkFrame):
    """
    Large centered card showing total download size

    Props:
    - total_size: str (e.g., "12.4 GB")
    - estimated_time: str (e.g., "18 minutes")
    - is_calculating: bool (shows spinner if True)

    Visual:
    - Large font for size (48px)
    - Background: slightly elevated (darker shade)
    - Padding: generous (30px all sides)
    """
```

2. **Breakdown Table**
```python
# CTkFrame with grid layout:
# Header row:
# - CTkLabel: "Table" (bold)
# - CTkLabel: "Size" (bold)
# - CTkLabel: "Files" (bold)

# Data rows (for each table):
# - CTkLabel: table name
# - CTkLabel: size
# - CTkLabel: file count

# Style: alternating row colors for readability
```

3. **Disk Space Indicator**
```python
# CTkFrame with:
# - Icon: checkmark or warning
# - CTkLabel: "Available Disk Space: X GB"
# - CTkLabel: Status message
# Colors: green for sufficient, orange/red for warning
```

4. **Configuration Summary**
```python
# CTkFrame with:
# - CTkLabel: "Configuration Summary" (header)
# - CTkLabel: "Output: [path]"
# - CTkLabel: "Tables: [list]"
# - CTkLabel: "Options: [list]"
# Style: smaller font, muted color
```

#### View 3: Download Progress

**Layout Structure:**
```python
# Main container
main_frame = ctk.CTkFrame(window)

# Stepper at top
stepper_frame = ProgressStepper(main_frame, current_step=3, completed_steps=[1, 2])

# Content area
content_frame = ctk.CTkFrame(main_frame)
content_frame.pack(fill="both", expand=True)

# Overall progress section (top)
overall_frame = ctk.CTkFrame(content_frame, height=100)
overall_frame.pack(fill="x", pady=(0, 15))

# CTkProgressBar: overall progress (0-1 float)
# CTkLabel: "62 of 93 files • 8.3 GB of 12.4 GB"
# CTkLabel: "Speed: 11.2 MB/s • ETA: 6 minutes"

# Two-column layout for details
details_frame = ctk.CTkFrame(content_frame)
details_frame.pack(fill="both", expand=True)

details_frame.grid_columnconfigure(0, weight=1)  # Left panel
details_frame.grid_columnconfigure(1, weight=2)  # Right panel

# Left panel: Stats
stats_frame = ctk.CTkFrame(details_frame)
stats_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

# Right panel: Table progress
tables_progress_frame = ctk.CTkFrame(details_frame)
tables_progress_frame.grid(row=0, column=1, sticky="nsew")

# Activity log (bottom)
log_frame = ctk.CTkFrame(content_frame, height=150)
log_frame.pack(fill="x", pady=(15, 0))

# CTkTextbox: scrollable log (read-only)

# Bottom navigation
nav_frame = ctk.CTkFrame(main_frame)
pause_btn = ctk.CTkButton(nav_frame, text="Pause")
cancel_btn = ctk.CTkButton(nav_frame, text="Cancel Download")
```

**Components:**

1. **Overall Progress Bar**
```python
class OverallProgress(ctk.CTkFrame):
    """
    Large progress bar showing overall download progress

    Props:
    - progress: float (0.0 to 1.0)
    - current_files: int
    - total_files: int
    - downloaded_size: str
    - total_size: str
    - speed: str
    - eta: str

    Visual:
    - CTkProgressBar: height=20px, full width
    - Progress text: "67%" overlaid on bar
    - Stats labels below bar
    """
```

2. **Stats Panel** (Left Side)
```python
# CTkFrame with vertical stack:
# - CTkLabel: "Current File" (header)
# - CTkLabel: filename (wrapped text)
# - Separator
# - CTkLabel: "Downloaded"
# - CTkLabel: size value (large font)
# - Separator
# - CTkLabel: "Remaining"
# - CTkLabel: size value
# - Separator
# - CTkLabel: "Files"
# - CTkLabel: count value
# - Separator
# - CTkLabel: "Elapsed"
# - CTkLabel: time value
```

3. **Table Progress Cards** (Right Side)
```python
class TableProgressCard(ctk.CTkFrame):
    """
    Progress card for each table (Blocks, Transactions, Outputs)

    Props:
    - table_name: str
    - progress: float (0.0 to 1.0)
    - current_files: int
    - total_files: int
    - downloaded_size: str
    - total_size: str
    - status: str ("Downloading...", "Queued", "Complete")

    Layout:
    - CTkLabel: table name (header)
    - CTkProgressBar: progress bar
    - CTkLabel: "X/Y files • X.X GB of Y.Y GB"
    - CTkLabel: status

    Visual:
    - Status color: blue (downloading), gray (queued), green (complete)
    - Progress bar color matches status
    """
```

4. **Activity Log**
```python
# CTkFrame with:
# - CTkLabel: "Activity Log" (header, left)
# - CTkButton: "Clear Log" (header, right)
# - CTkTextbox: scrollable text area
#   - read-only
#   - monospace font
#   - auto-scroll to bottom
#   - max 100 lines (older lines removed)
#   - timestamp format: [HH:MM:SS]
```

5. **Success Screen Components**
```python
# CTkFrame (centered):
# - CTkLabel: "✓" checkmark icon (large, green)
# - CTkLabel: "Download Complete!" (header)
# - CTkLabel: "Successfully downloaded X files" (subheader)
# - CTkLabel: "Total: X GB"
# - CTkLabel: "Time taken: Xm Ys"
#
# Summary card:
# - CTkFrame with breakdown by table
# - CTkLabel: output location
# - CTkLabel: options applied
#
# Buttons:
# - CTkButton: "Open Output Folder" (primary)
# - CTkButton: "Start New Download" (secondary)
```

---

## Navigation & Transitions

### Navigation Pattern

**Forward Navigation:**
- View 1 → View 2: Click "Next: Calculate Size" button
- View 2 → View 3: Click "Start Download" button
- View 3 → View 1: Click "Start New Download" button (after completion)

**Backward Navigation:**
- View 2 → View 1: Click "← Back" button
- View 3 → View 1: Click "Cancel Download" (with confirmation)

**No navigation from View 3 in progress** - User must wait, pause, or cancel

### Transition Animations (Optional)

```python
# Smooth fade transitions between views
def transition_to_view(new_view_frame):
    """
    Fade out current view, fade in new view

    Steps:
    1. Fade out current_view (alpha: 1.0 → 0.0 over 150ms)
    2. Pack_forget() current view
    3. Pack() new view
    4. Fade in new_view (alpha: 0.0 → 1.0 over 150ms)
    """
    # Use CTkFrame configure(alpha=...) if supported
    # Or simple pack_forget/pack swap
```

### Stepper State Management

```python
class StepperState:
    """
    Manages stepper state across views

    Attributes:
    - current_step: int (1, 2, or 3)
    - completed_steps: set[int]

    Methods:
    - advance_step(): Move to next step
    - go_back(): Return to previous step
    - complete_step(step: int): Mark step as complete
    """
```

---

## Responsive Behavior

### Window Resizing

**Minimum Window Size:** 900x700px
**Recommended Size:** 1000x800px
**Maximum Size:** No limit (scales up)

**Responsive Patterns:**

1. **Horizontal Scaling (width < 1000px):**
   - Date Range and Quick Presets stack vertically instead of side-by-side
   - Table cards adjust size to fit
   - Log area maintains minimum height

2. **Vertical Scaling (height < 800px):**
   - Reduce padding between sections
   - Reduce stepper height slightly
   - Log area shrinks first (minimum 100px)

3. **Large Screens (width > 1200px):**
   - Content centers with max-width constraint
   - Additional side padding
   - Log area expands

```python
# Implement responsive layout using grid weights
def configure_responsive_layout(window_width, window_height):
    if window_width < 1000:
        # Switch to vertical layout for date picker
        date_frame.grid(row=1, column=0, columnspan=2)
        preset_frame.grid(row=2, column=0, columnspan=2)
    else:
        # Horizontal layout
        date_frame.grid(row=1, column=0)
        preset_frame.grid(row=1, column=1)

    if window_height < 800:
        # Reduce log height
        log_frame.configure(height=100)
    else:
        log_frame.configure(height=150)
```

---

## Interaction Design

### Loading States

**View 1 → View 2 Transition:**
```python
# When "Next: Calculate Size" clicked:
# 1. Button disabled
# 2. Button text changes to "Calculating..."
# 3. Spinner icon appears
# 4. Transition to View 2
# 5. View 2 shows calculating state with spinner
# 6. After calculation completes (async), show results
```

**Calculating State (View 2):**
```python
class CalculatingState(ctk.CTkFrame):
    """
    Shown in View 2 while size calculation runs

    Visual:
    - Centered spinner animation
    - CTkLabel: "Calculating download size..."
    - CTkLabel: "Analyzing X files..." (updates in real-time)

    Duration: ~1-3 seconds depending on date range
    """
```

**Download Progress (View 3):**
```python
# Real-time updates:
# - Overall progress bar updates every 100ms
# - Table progress bars update every 500ms
# - Stats panel updates every 500ms
# - Log appends new lines immediately
# - Speed/ETA recalculated every 1 second
```

### Button States

**Primary Buttons:**
```python
# Normal state:
# - fg_color: primary blue
# - hover_color: lighter blue
# - cursor: pointer

# Disabled state:
# - fg_color: gray
# - text_color: darker gray
# - cursor: not-allowed

# Loading state:
# - Spinner icon
# - Text changes (e.g., "Starting...")
# - Disabled interaction
```

**Pause/Resume Button:**
```python
# Toggle button:
pause_btn = ctk.CTkButton(
    nav_frame,
    text="Pause",
    command=toggle_pause
)

def toggle_pause():
    if is_paused:
        pause_btn.configure(text="Pause")
        resume_download()
    else:
        pause_btn.configure(text="Resume")
        pause_download()
```

### Error Handling

**Insufficient Disk Space (View 2):**
```python
# Replace disk space indicator with warning:
# - Icon: warning triangle (orange)
# - CTkLabel: "Insufficient disk space!"
# - CTkLabel: "Available: X GB • Required: Y GB"
# - "Start Download" button disabled
# - Show "Free Up Space" help text
```

**Network Error (View 3):**
```python
# Show error banner at top of View 3:
# - Background: red/orange
# - Icon: error icon
# - CTkLabel: "Network error: Connection lost"
# - CTkButton: "Retry" (attempts to resume)
# - Download pauses automatically
```

**File System Error:**
```python
# Show error dialog (CTkMessagebox):
# - Title: "Error"
# - Message: "Failed to write file: [filename]"
# - Detail: [error message]
# - Buttons: "Retry", "Skip File", "Cancel Download"
```

### Success Feedback

**Calculation Complete (View 2):**
```python
# Smooth transition from calculating spinner to results
# - Fade out spinner (150ms)
# - Fade in size display (150ms)
# - Pulse animation on total size (subtle scale effect)
```

**Download Complete (View 3):**
```python
# Transition to success state:
# 1. Final progress update (100%)
# 2. All progress bars turn green
# 3. Log appends: "✓ All downloads completed successfully"
# 4. 500ms delay
# 5. Fade to success screen
# 6. Show success checkmark with bounce animation
# 7. Enable "Open Output Folder" and "Start New Download" buttons
```

**File Downloaded (View 3):**
```python
# Real-time feedback in log:
# - New line appends: "[HH:MM:SS] Downloaded: [filename]"
# - Progress bars update
# - Brief highlight flash on current file stat
```

### Confirmation Dialogs

**Cancel Download (View 3):**
```python
# Show confirmation dialog:
dialog = CTkMessagebox(
    title="Cancel Download?",
    message="Download is in progress. Are you sure you want to cancel?",
    icon="warning",
    option_1="Continue Download",
    option_2="Cancel Download"
)

if dialog.get() == "Cancel Download":
    stop_download()
    cleanup_partial_files()
    transition_to_view(configuration_view)
```

**Exit Application During Download:**
```python
# Override window close event:
def on_closing():
    if download_in_progress:
        dialog = CTkMessagebox(
            title="Download in Progress",
            message="A download is currently running. Exit anyway?",
            icon="warning",
            option_1="Keep Running",
            option_2="Exit"
        )
        if dialog.get() == "Exit":
            stop_download()
            window.destroy()
    else:
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
```

---

## Design Tokens (CustomTkinter)

### Colors (Dark Mode)

```python
# Primary Colors
PRIMARY_BLUE = "#1f6feb"
PRIMARY_BLUE_HOVER = "#388bfd"
PRIMARY_BLUE_DARK = "#0d419d"

# Semantic Colors
SUCCESS_GREEN = "#238636"
WARNING_ORANGE = "#d29922"
ERROR_RED = "#da3633"

# Neutral Colors
BG_DARK = "#0d1117"          # Main background
BG_ELEVATED = "#161b22"       # Card backgrounds
BG_HOVER = "#21262d"          # Hover states
BORDER_COLOR = "#30363d"      # Borders
TEXT_PRIMARY = "#c9d1d9"      # Main text
TEXT_SECONDARY = "#8b949e"    # Muted text
TEXT_DISABLED = "#484f58"     # Disabled text

# Progress Bar Colors
PROGRESS_TRACK = "#21262d"    # Empty track
PROGRESS_FILL = "#1f6feb"     # Filled portion
PROGRESS_COMPLETE = "#238636" # Complete state
```

### Typography

```python
# Font Sizes
FONT_LARGE = ("Segoe UI", 48, "bold")      # Size display
FONT_TITLE = ("Segoe UI", 24, "bold")      # Page titles
FONT_HEADING = ("Segoe UI", 18, "bold")    # Section headings
FONT_BODY = ("Segoe UI", 14)               # Body text
FONT_SMALL = ("Segoe UI", 12)              # Helper text
FONT_MONO = ("Consolas", 12)               # Log text

# Line Heights (spacing)
LINE_HEIGHT_TIGHT = 1.2
LINE_HEIGHT_NORMAL = 1.5
LINE_HEIGHT_RELAXED = 1.8
```

### Spacing

```python
# Padding (internal component spacing)
PADDING_XS = 5
PADDING_SM = 10
PADDING_MD = 15
PADDING_LG = 20
PADDING_XL = 30

# Gaps (space between components)
GAP_SM = 10
GAP_MD = 15
GAP_LG = 20

# Component Sizes
BUTTON_HEIGHT = 36
INPUT_HEIGHT = 36
PROGRESS_BAR_HEIGHT = 20
STEPPER_HEIGHT = 80
NAV_BAR_HEIGHT = 60
```

### Borders & Shadows

```python
# Border Radius
RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 8

# Border Width
BORDER_THIN = 1
BORDER_MEDIUM = 2

# Shadows (if supported by CustomTkinter)
SHADOW_SM = "0 1px 3px rgba(0,0,0,0.3)"
SHADOW_MD = "0 4px 6px rgba(0,0,0,0.4)"
SHADOW_LG = "0 10px 15px rgba(0,0,0,0.5)"
```

---

## Accessibility

### Keyboard Navigation

**View 1 (Configuration):**
```
Tab Order:
1. Output directory text field
2. Browse button
3. From date field
4. From calendar button
5. To date field
6. To calendar button
7. Last 7 Days preset
8. Last 30 Days preset
9. Last 90 Days preset
10. Last Year preset
11. All Time preset
12. Blocks checkbox
13. Transactions checkbox
14. Outputs checkbox
15. Remove .gz checkbox
16. Cancel button
17. Next button

Shortcuts:
- Enter: Submit (equivalent to clicking Next button)
- Escape: Cancel (close dialog if any)
```

**View 2 (Size Calculation):**
```
Tab Order:
1. Back button
2. Start Download button

Shortcuts:
- Enter: Start Download
- Escape: Go Back
```

**View 3 (Download Progress):**
```
Tab Order:
1. Pause button
2. Cancel Download button
3. Clear Log button (if applicable)

Shortcuts:
- Space: Pause/Resume
- Escape: Cancel Download (with confirmation)
```

### Screen Reader Support

```python
# Add accessibility labels to components:

# Buttons
next_btn.configure(text="Next: Calculate Size",
                  cursor="hand2")  # Visual feedback

# Progress bars
overall_progress.configure(
    # Would need custom implementation for aria-label
    # CustomTkinter doesn't natively support ARIA
)

# Announce state changes (pseudo-code):
def announce(message):
    """
    Announce to screen readers (if accessible mode enabled)
    Could use platform-specific APIs:
    - Windows: UI Automation
    - macOS: Accessibility API
    - Linux: AT-SPI
    """
    pass

# Example usage:
announce("Calculation complete. Total download size: 12.4 gigabytes")
announce("Download started. Overall progress: 0 percent")
announce("File downloaded: blocks 2024-01-01.tsv.gz")
announce("Download complete. 93 files downloaded successfully")
```

### Focus Indicators

```python
# Ensure all interactive elements have visible focus:
button_style = {
    "corner_radius": RADIUS_MD,
    "border_width": 2,
    "border_color": "transparent",
    "fg_color": PRIMARY_BLUE,
    "hover_color": PRIMARY_BLUE_HOVER,
}

# On focus (would need custom implementation):
# border_color: PRIMARY_BLUE_HOVER (2px border)
# Possible with CustomTkinter events:
def on_focus(event):
    event.widget.configure(border_color=PRIMARY_BLUE_HOVER)

def on_blur(event):
    event.widget.configure(border_color="transparent")

button.bind("<FocusIn>", on_focus)
button.bind("<FocusOut>", on_blur)
```

### High Contrast Mode

```python
# Support system high contrast mode (optional enhancement)
def detect_high_contrast():
    """
    Detect if OS high contrast mode is enabled
    Adjust colors accordingly
    """
    # Windows: Check SystemParametersInfo
    # macOS: Check NSWorkspace.accessibilityDisplayShouldIncreaseContrast
    pass

if detect_high_contrast():
    # Use higher contrast colors:
    TEXT_PRIMARY = "#ffffff"
    BORDER_COLOR = "#ffffff"
    BG_DARK = "#000000"
```

---

## Implementation Notes

### For Implementation Team

#### Phase 1: Core Views (Week 1)
1. **Create view manager system**
   - ViewManager class to handle view switching
   - State management for configuration data
   - Navigation history

2. **Implement Progress Stepper component**
   - Reusable component for all views
   - State-aware (current step, completed steps)
   - Visual states (active, complete, inactive)

3. **Build View 1 (Configuration)**
   - Layout with grid system (no scrolling)
   - All form components
   - Validation logic
   - Save state to ViewManager

4. **Build View 2 (Size Calculation)**
   - Layout with centered content
   - Size calculation logic (async)
   - Results display
   - Navigation buttons

#### Phase 2: Progress & Polish (Week 2)
1. **Build View 3 (Download Progress)**
   - Two-column layout
   - Real-time progress updates
   - Log component
   - Pause/resume functionality

2. **Implement transitions**
   - Smooth view switching
   - Loading states
   - Error handling

3. **Add success/error states**
   - Completion screen
   - Error dialogs
   - Confirmation dialogs

#### Phase 3: Testing & Refinement (Week 3)
1. **Responsive behavior**
   - Test at different window sizes
   - Adjust layouts dynamically
   - Minimum size constraints

2. **Keyboard navigation**
   - Tab order verification
   - Shortcut keys
   - Focus indicators

3. **Polish & optimization**
   - Animation tuning
   - Performance optimization
   - Edge case handling

### Technical Considerations

**State Management:**
```python
class AppState:
    """
    Global application state shared across views

    Attributes:
    - output_dir: str
    - date_from: datetime
    - date_to: datetime
    - selected_tables: list[str]
    - remove_gz: bool
    - total_size: float
    - total_files: int
    - download_progress: dict
    """

    def __init__(self):
        self.output_dir = ""
        self.date_from = None
        self.date_to = None
        self.selected_tables = []
        self.remove_gz = False
        self.total_size = 0
        self.total_files = 0
        self.download_progress = {}

    def validate_configuration(self) -> tuple[bool, str]:
        """Validate configuration before proceeding to View 2"""
        if not self.output_dir:
            return False, "Please select an output directory"
        if not self.date_from or not self.date_to:
            return False, "Please select a date range"
        if not self.selected_tables:
            return False, "Please select at least one table"
        if self.date_from > self.date_to:
            return False, "Start date must be before end date"
        return True, ""
```

**View Manager:**
```python
class ViewManager:
    """
    Manages view transitions and state
    """

    def __init__(self, window, app_state):
        self.window = window
        self.app_state = app_state
        self.current_view = None
        self.views = {}

    def register_view(self, name: str, view_class):
        """Register a view class"""
        self.views[name] = view_class

    def show_view(self, name: str):
        """Transition to a specific view"""
        # Destroy current view
        if self.current_view:
            self.current_view.destroy()

        # Create and show new view
        view_class = self.views[name]
        self.current_view = view_class(self.window, self.app_state, self)
        self.current_view.pack(fill="both", expand=True)

    def next_view(self):
        """Navigate to next view in workflow"""
        if self.current_view.name == "configuration":
            # Validate before proceeding
            valid, error = self.app_state.validate_configuration()
            if not valid:
                show_error_dialog(error)
                return
            self.show_view("calculation")
        elif self.current_view.name == "calculation":
            self.show_view("progress")

    def previous_view(self):
        """Navigate to previous view"""
        if self.current_view.name == "calculation":
            self.show_view("configuration")
```

**Progress Updates:**
```python
# Use threading for background downloads
import threading
from queue import Queue

class DownloadManager:
    """
    Manages download operations and progress updates
    """

    def __init__(self, app_state, progress_callback):
        self.app_state = app_state
        self.progress_callback = progress_callback
        self.is_running = False
        self.is_paused = False
        self.download_thread = None
        self.progress_queue = Queue()

    def start_download(self):
        """Start download in background thread"""
        self.is_running = True
        self.download_thread = threading.Thread(target=self._download_worker)
        self.download_thread.daemon = True
        self.download_thread.start()

        # Start progress monitor
        self._monitor_progress()

    def _download_worker(self):
        """Background download worker"""
        # Existing download logic here
        # Push updates to progress_queue
        pass

    def _monitor_progress(self):
        """Monitor progress queue and update UI"""
        if not self.progress_queue.empty():
            progress_data = self.progress_queue.get()
            self.progress_callback(progress_data)

        # Schedule next check (every 100ms)
        if self.is_running:
            self.window.after(100, self._monitor_progress)
```

### Migration from Current UI

**Step 1: Extract existing logic**
- Keep all download logic intact
- Keep API calls and file handling
- Keep progress tracking

**Step 2: Refactor UI code**
- Replace CTkScrollableFrame with standard CTkFrame
- Reorganize components into 3 view classes
- Implement ViewManager

**Step 3: Connect new UI to existing logic**
- Wire up buttons to existing functions
- Connect progress callbacks
- Update state management

**Step 4: Test thoroughly**
- Verify all functionality works
- Test edge cases
- Validate with different configurations

---

## Design Rationale

### Why Multi-View Wizard?

**Problem with Single-View:**
- Cognitive overload - too many options at once
- Unclear workflow - user doesn't know what order to do things
- Scrolling required - poor UX, feels cramped
- Mixed concerns - configuration and progress on same screen

**Benefits of Wizard:**
- **Guided workflow** - Clear progression: Configure → Calculate → Download
- **No scrolling** - Each view fits on screen, better use of horizontal space
- **Focused tasks** - One goal per view reduces cognitive load
- **Natural progression** - Matches mental model: "set up → check → execute"
- **Better progress tracking** - Stepper shows where user is in process
- **Cleaner design** - Less clutter, more whitespace

### Why Horizontal Layouts?

**Vertical Stacking Problems:**
- Wastes horizontal space (especially on widescreen monitors)
- Requires scrolling even on large screens
- Creates long, cramped feeling

**Horizontal Layout Benefits:**
- **Better space utilization** - Date picker and presets side-by-side
- **Visual grouping** - Related items (like table cards) arranged horizontally
- **Easier scanning** - Eye naturally scans left-to-right
- **Modern aesthetic** - More contemporary design pattern
- **Scales better** - Adapts to different screen sizes

### Why This Specific Workflow?

**User Mental Model:**
1. "I need to configure what to download" → **View 1**
2. "Let me check how much space this will take" → **View 2**
3. "Okay, start the download and show me progress" → **View 3**

**Matches Real-World Download Tools:**
- Torrent clients (configure → preview → download)
- Package managers (select packages → review → install)
- Installation wizards (configure → confirm → progress)

**Prevents Errors:**
- Size calculation *before* download prevents "oops, not enough space"
- Configuration review in View 2 catches mistakes
- Can't accidentally start download without seeing size

---

## Conclusion

This design specification provides a complete redesign of the Blockchair Downloader UI from a single scrollable view to a modern, multi-view wizard interface. The key improvements are:

1. **No scrolling** - All content fits within 1000x800px window
2. **Horizontal layouts** - Efficient use of space, side-by-side arrangements
3. **Clear workflow** - 3-step wizard guides users through process
4. **Modern aesthetic** - Clean design with dark mode, generous whitespace
5. **Better UX** - Progress tracking, validation, error handling, success states

The implementation uses existing CustomTkinter components with a new ViewManager system to handle transitions. All existing download logic remains intact - only the UI layer is redesigned.

**Next Steps:**
1. Review and approve this design specification
2. Create mockups/prototypes (optional)
3. Begin Phase 1 implementation (Core Views)
4. Iterate based on user feedback

---

## Appendix: Component Library

### Custom Components to Build

1. **ProgressStepper** - Horizontal stepper with circles and connecting lines
2. **TableCard** - Card component for table selection with checkbox
3. **SizeDisplayCard** - Large centered card for size display
4. **TableProgressCard** - Progress card for individual table download progress
5. **StatItem** - Key-value stat display for stats panel

### Reusable Patterns

**Card Pattern:**
```python
card = ctk.CTkFrame(
    parent,
    fg_color=BG_ELEVATED,
    corner_radius=RADIUS_LG,
    border_width=BORDER_THIN,
    border_color=BORDER_COLOR
)
```

**Button Pattern:**
```python
button = ctk.CTkButton(
    parent,
    text="Button Text",
    fg_color=PRIMARY_BLUE,
    hover_color=PRIMARY_BLUE_HOVER,
    corner_radius=RADIUS_MD,
    height=BUTTON_HEIGHT,
    font=FONT_BODY
)
```

**Input Pattern:**
```python
input_field = ctk.CTkEntry(
    parent,
    placeholder_text="Enter value...",
    height=INPUT_HEIGHT,
    font=FONT_BODY,
    fg_color=BG_ELEVATED,
    border_color=BORDER_COLOR
)
```

---

**Document Version:** 1.0
**Date:** 2025-11-26
**Author:** UX Designer Agent
**Status:** Ready for Review
