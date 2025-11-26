#!/usr/bin/env python3
"""
Bitcoin Blockchain Data Downloader (Blockchair)
Modern GUI tool for downloading Bitcoin blockchain dumps.

Features:
- Modern, clean UI with dark mode
- Pause/Resume functionality
- State persistence (remembers settings and progress)
- Auto-resume on restart
- Detailed progress tracking

Works on: macOS, Windows, Linux
"""

import os
import sys
import gzip
import shutil
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List, Optional
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import queue
import time

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"


class DownloadState:
    """Manages download state persistence."""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.state = self.load()

    def load(self) -> dict:
        """Load state from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self, state: dict):
        """Save state to file."""
        self.state = state
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(state, f, indent=2)

    def get(self, key: str, default=None):
        """Get state value."""
        return self.state.get(key, default)

    def set(self, key: str, value):
        """Set state value."""
        self.state[key] = value
        self.save(self.state)


class BlockchairDownloader:
    """Handles Blockchair data downloads with pause/resume support."""

    BASE_URL = "https://gz.blockchair.com/bitcoin/"
    TABLES = {
        "blocks": 0.8,        # MB per day (approximate)
        "transactions": 150,   # MB per day
        "outputs": 250        # MB per day
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.extracted_dir = self.output_dir / "extracted"
        self.state_file = self.output_dir / ".download_state.json"

        self.state = DownloadState(self.state_file)
        self.paused = False
        self.cancelled = False

    def estimate_size(self, start_date: datetime, end_date: datetime,
                     tables: List[str]) -> Tuple[float, float]:
        """
        Estimates download size.

        Returns:
            (compressed_gb, uncompressed_gb)
        """
        days = (end - start_date).days + 1

        total_mb_compressed = 0
        for table in tables:
            total_mb_compressed += self.TABLES[table] * days

        compressed_gb = total_mb_compressed / 1024
        uncompressed_gb = compressed_gb / 0.3  # .gz compression ratio ~30%

        return compressed_gb, uncompressed_gb

    def get_date_range(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate list of dates between start and end."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    def build_url(self, table: str, date: datetime) -> str:
        """Build download URL for specific table and date."""
        date_str = date.strftime("%Y-%m-%d")
        filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
        return self.BASE_URL + f"{table}/{filename}"

    def download_file(self, url: str, output_path: Path,
                     progress_callback=None) -> bool:
        """Download single file with progress tracking and pause support."""
        try:
            # Use urllib instead of requests
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=60)

            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                while True:
                    # Check for pause/cancel
                    if self.cancelled:
                        return False

                    while self.paused and not self.cancelled:
                        time.sleep(0.1)

                    if self.cancelled:
                        return False

                    # Read chunk
                    chunk = response.read(8192)
                    if not chunk:
                        break

                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress, downloaded, total_size)

            return True

        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False  # File doesn't exist (normal)
            raise
        except Exception as e:
            if self.cancelled:
                return False
            raise Exception(f"Download failed: {str(e)}")

    def extract_gz(self, gz_path: Path, output_path: Path) -> bool:
        """Extract .gz file."""
        try:
            with gzip.open(gz_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")

    def pause(self):
        """Pause download."""
        self.paused = True

    def resume(self):
        """Resume download."""
        self.paused = False

    def cancel(self):
        """Cancel download."""
        self.cancelled = True
        self.paused = False

    def download_and_extract(self, start_date: datetime, end_date: datetime,
                           tables: List[str], remove_gz: bool = True,
                           progress_callback=None, log_callback=None,
                           file_progress_callback=None) -> dict:
        """
        Download and extract data for date range.

        Returns:
            dict with statistics
        """
        # Reset state
        self.paused = False
        self.cancelled = False

        # Save download config to state
        self.state.set('output_dir', str(self.output_dir))
        self.state.set('start_date', start_date.strftime("%Y-%m-%d"))
        self.state.set('end_date', end_date.strftime("%Y-%m-%d"))
        self.state.set('tables', tables)
        self.state.set('remove_gz', remove_gz)

        # Create directories
        for table in tables:
            (self.raw_dir / table).mkdir(parents=True, exist_ok=True)
            (self.extracted_dir / table).mkdir(parents=True, exist_ok=True)

        dates = self.get_date_range(start_date, end_date)

        stats = {
            'total': len(dates) * len(tables),
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'downloaded_mb': 0
        }

        current_task = 0
        start_time = time.time()

        for date in dates:
            for table in tables:
                if self.cancelled:
                    if log_callback:
                        log_callback("\n⏸ Download cancelled by user")
                    return stats

                current_task += 1
                date_str = date.strftime("%Y-%m-%d")

                # File paths
                gz_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv.gz"
                tsv_filename = f"blockchair_bitcoin_{table}_{date_str}.tsv"

                gz_path = self.raw_dir / table / gz_filename
                tsv_path = self.extracted_dir / table / tsv_filename

                # Calculate ETA
                elapsed = time.time() - start_time
                if current_task > 1:
                    avg_time_per_file = elapsed / (current_task - 1)
                    remaining_files = stats['total'] - current_task + 1
                    eta_seconds = avg_time_per_file * remaining_files
                    eta_minutes = int(eta_seconds / 60)
                    eta_hours = eta_minutes // 60
                    eta_mins = eta_minutes % 60
                    eta_str = f"{eta_hours}h {eta_mins}m" if eta_hours > 0 else f"{eta_mins}m"
                else:
                    eta_str = "calculating..."

                # Log progress
                if log_callback:
                    log_callback(f"[{current_task}/{stats['total']}] {table} {date_str} (ETA: {eta_str})")

                # Skip if already extracted
                if tsv_path.exists():
                    if log_callback:
                        log_callback(f"  → Already exists, skipping")
                    stats['skipped'] += 1
                    if progress_callback:
                        progress_callback(current_task, stats['total'])
                    continue

                # Download
                url = self.build_url(table, date)

                try:
                    if log_callback:
                        log_callback(f"  → Downloading...")

                    def download_progress(pct, downloaded, total):
                        if file_progress_callback:
                            file_progress_callback(pct, downloaded, total, current_task, stats['total'])

                    success = self.download_file(url, gz_path, download_progress)

                    if not success:
                        if self.cancelled:
                            return stats
                        if log_callback:
                            log_callback(f"  → Not found (404), skipping")
                        stats['skipped'] += 1
                        if progress_callback:
                            progress_callback(current_task, stats['total'])
                        continue

                    # Track size
                    file_size_mb = gz_path.stat().st_size / 1024 / 1024
                    stats['downloaded_mb'] += file_size_mb

                    # Extract
                    if log_callback:
                        log_callback(f"  → Extracting...")

                    self.extract_gz(gz_path, tsv_path)

                    # Remove .gz if requested
                    if remove_gz:
                        gz_path.unlink()
                        if log_callback:
                            log_callback(f"  → Removed .gz file")

                    stats['successful'] += 1
                    if log_callback:
                        log_callback(f"  ✓ Complete ({file_size_mb:.1f} MB)")

                except Exception as e:
                    if self.cancelled:
                        return stats
                    stats['failed'] += 1
                    if log_callback:
                        log_callback(f"  ✗ Error: {str(e)}")

                # Update overall progress
                if progress_callback:
                    progress_callback(current_task, stats['total'])

        return stats


class DownloaderGUI:
    """Modern GUI for Bitcoin data downloader with 3-view wizard system."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Bitcoin Blockchain Data Downloader")
        self.root.geometry("900x750")
        self.root.resizable(False, False)

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Variables
        self.output_dir = ctk.StringVar()
        self.start_date = ctk.StringVar()
        self.end_date = ctk.StringVar()
        self.remove_gz = ctk.BooleanVar(value=True)

        # Download state
        self.is_downloading = False
        self.downloader: Optional[BlockchairDownloader] = None
        self.download_thread = None
        self.log_queue = queue.Queue()

        # View management
        self.current_view = None
        self.current_step = 1
        self.calculated_size_compressed = 0
        self.calculated_size_uncompressed = 0

        self.setup_ui()
        self.process_log_queue()
        self.check_for_incomplete_downloads()

    def setup_ui(self):
        """Setup modern UI with 3-view wizard system."""
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="🐋 Bitcoin Blockchain Downloader",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(pady=(0, 5))

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Download Blockchair dumps locally • Pause & Resume anytime",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        subtitle.pack()

        # Progress Stepper (Frame-based, not buttons)
        self.stepper_frame = ctk.CTkFrame(self.root, corner_radius=10, fg_color="transparent")
        self.stepper_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=(0, 15))
        self.stepper_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Step 1: Configure
        self.step1_container = ctk.CTkFrame(
            self.stepper_frame, corner_radius=8,
            border_width=2, border_color=("#ffb74d", "#ff9800")  # Orange for active
        )
        self.step1_container.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.step1_label = ctk.CTkLabel(
            self.step1_container, text="1. Configure",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=35
        )
        self.step1_label.pack(pady=8)

        # Step 2: Calculate Size
        self.step2_container = ctk.CTkFrame(
            self.stepper_frame, corner_radius=8,
            border_width=2, border_color=("gray70", "gray25")  # Gray for upcoming
        )
        self.step2_container.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.step2_label = ctk.CTkLabel(
            self.step2_container, text="2. Calculate Size",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray50"),  # Muted
            height=35
        )
        self.step2_label.pack(pady=8)

        # Step 3: Download
        self.step3_container = ctk.CTkFrame(
            self.stepper_frame, corner_radius=8,
            border_width=2, border_color=("gray70", "gray25")  # Gray for upcoming
        )
        self.step3_container.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.step3_label = ctk.CTkLabel(
            self.step3_container, text="3. Download",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray50"),  # Muted
            height=35
        )
        self.step3_label.pack(pady=8)

        # Main content frame (will hold different views)
        self.content_frame = ctk.CTkFrame(self.root, corner_radius=10, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Show first view
        self.show_config_view()

    def clear_content(self):
        """Clear current content view."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def update_stepper(self, step: int):
        """Update stepper UI to highlight current step."""
        self.current_step = step

        # Colors
        completed_border = ("#66bb6a", "#4caf50")  # Green
        active_border = ("#ffb74d", "#ff9800")      # Orange
        upcoming_border = ("gray70", "gray25")      # Gray

        # Step 1
        if step > 1:  # Completed
            self.step1_container.configure(border_color=completed_border)
            self.step1_label.configure(
                text="✓ Configure",
                font=ctk.CTkFont(size=13),
                text_color=("#66bb6a", "#4caf50")
            )
        elif step == 1:  # Active
            self.step1_container.configure(border_color=active_border)
            self.step1_label.configure(
                text="1. Configure",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("gray10", "gray90")
            )
        else:  # Upcoming
            self.step1_container.configure(border_color=upcoming_border)
            self.step1_label.configure(
                text="1. Configure",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray50")
            )

        # Step 2
        if step > 2:  # Completed
            self.step2_container.configure(border_color=completed_border)
            self.step2_label.configure(
                text="✓ Calculate Size",
                font=ctk.CTkFont(size=13),
                text_color=("#66bb6a", "#4caf50")
            )
        elif step == 2:  # Active
            self.step2_container.configure(border_color=active_border)
            self.step2_label.configure(
                text="2. Calculate Size",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("gray10", "gray90")
            )
        else:  # Upcoming
            self.step2_container.configure(border_color=upcoming_border)
            self.step2_label.configure(
                text="2. Calculate Size",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray50")
            )

        # Step 3
        if step > 3:  # Completed
            self.step3_container.configure(border_color=completed_border)
            self.step3_label.configure(
                text="✓ Download",
                font=ctk.CTkFont(size=13),
                text_color=("#66bb6a", "#4caf50")
            )
        elif step == 3:  # Active
            self.step3_container.configure(border_color=active_border)
            self.step3_label.configure(
                text="3. Download",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("gray10", "gray90")
            )
        else:  # Upcoming
            self.step3_container.configure(border_color=upcoming_border)
            self.step3_label.configure(
                text="3. Download",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray50")
            )

    def show_config_view(self):
        """Show View 1: Configuration."""
        self.clear_content()
        self.update_stepper(1)

        view = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        view.grid(row=0, column=0, sticky="nsew")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(0, weight=1)

        # Main Column (centered, max width)
        main_col = ctk.CTkFrame(view, corner_radius=10)
        main_col.grid(row=0, column=0, sticky="nsew", padx=80)

        # Output Directory
        ctk.CTkLabel(
            main_col, text="📁 Output Directory",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        dir_container = ctk.CTkFrame(main_col, fg_color="transparent")
        dir_container.pack(fill="x", padx=20, pady=(0, 20))
        dir_container.grid_columnconfigure(0, weight=1)

        self.dir_entry = ctk.CTkEntry(dir_container, textvariable=self.output_dir, height=38)
        self.dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            dir_container, text="Browse",
            command=self.browse_directory,
            width=100, height=38
        ).grid(row=0, column=1)

        # Date Range
        ctk.CTkLabel(
            main_col, text="📅 Date Range",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 10))

        date_container = ctk.CTkFrame(main_col, fg_color="transparent")
        date_container.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(date_container, text="Start Date:").grid(row=0, column=0, sticky="w", pady=5)
        start_entry = ctk.CTkEntry(
            date_container, textvariable=self.start_date, height=35, width=150,
            placeholder_text="YYYY-MM-DD",
            placeholder_text_color=("gray50", "gray60")  # Lighter for dark mode
        )
        start_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(date_container, text="End Date:").grid(row=1, column=0, sticky="w", pady=5)
        end_entry = ctk.CTkEntry(
            date_container, textvariable=self.end_date, height=35, width=150,
            placeholder_text="YYYY-MM-DD",
            placeholder_text_color=("gray50", "gray60")  # Lighter for dark mode
        )
        end_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Presets
        ctk.CTkLabel(
            main_col, text="Quick Presets:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        # First row of presets (short periods from 2025)
        preset_row1 = ctk.CTkFrame(main_col, fg_color="transparent")
        preset_row1.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkButton(
            preset_row1, text="1 Week (2025)", height=32,
            command=lambda: self.set_preset("2025-01-01", "2025-01-07")
        ).pack(side="left", padx=(0, 5), expand=True, fill="x")

        ctk.CTkButton(
            preset_row1, text="1 Month (2025)", height=32,
            command=lambda: self.set_preset("2025-01-01", "2025-01-31")
        ).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            preset_row1, text="Q1 2025", height=32,
            command=lambda: self.set_preset("2025-01-01", "2025-03-31")
        ).pack(side="left", padx=(5, 0), expand=True, fill="x")

        # Second row of presets (full years)
        preset_row2 = ctk.CTkFrame(main_col, fg_color="transparent")
        preset_row2.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            preset_row2, text="Year 2021", height=32,
            command=lambda: self.set_preset("2021-01-01", "2021-12-31")
        ).pack(side="left", padx=(0, 5), expand=True, fill="x")

        ctk.CTkButton(
            preset_row2, text="Year 2024", height=32,
            command=lambda: self.set_preset("2024-01-01", "2024-12-31")
        ).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(
            preset_row2, text="Year 2025", height=32,
            command=lambda: self.set_preset("2025-01-01", "2025-12-31")
        ).pack(side="left", padx=(5, 0), expand=True, fill="x")

        # Options
        ctk.CTkLabel(
            main_col, text="⚙️ Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 10))

        ctk.CTkCheckBox(
            main_col,
            text="Remove .gz files after extraction (saves ~70% disk space)",
            variable=self.remove_gz
        ).pack(anchor="w", padx=20, pady=(0, 20))

        # Bottom Navigation
        nav_frame = ctk.CTkFrame(view, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0))
        nav_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            nav_frame, text="Next: Calculate Size →",
            command=self.goto_calculate_view,
            height=45, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2CC985", "#2FA572"), hover_color=("#28B872", "#298F65")
        ).grid(row=0, column=1, sticky="e")

    def show_calculate_view(self):
        """Show View 2: Size Calculation."""
        self.clear_content()
        self.update_stepper(2)

        view = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        view.grid(row=0, column=0, sticky="nsew")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        # Title
        title_frame = ctk.CTkFrame(view, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            title_frame, text="📊 Download Size Calculation",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack()

        # Main content area
        content = ctk.CTkFrame(view, corner_radius=10)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Size display area
        size_area = ctk.CTkFrame(content, fg_color="transparent")
        size_area.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)

        # Configuration Summary
        summary_frame = ctk.CTkFrame(size_area, corner_radius=8, fg_color=("#D0D0D0", "#333333"))
        summary_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            summary_frame, text="Configuration Summary",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # Container for grid layout
        self.summary_container = ctk.CTkFrame(summary_frame, fg_color="transparent")
        self.summary_container.pack(fill="x", padx=20, pady=(0, 15))

        # Size Result
        self.size_result_frame = ctk.CTkFrame(size_area, corner_radius=8, fg_color=("#E8F4FD", "#1a3a4a"))
        self.size_result_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.size_result_label = ctk.CTkLabel(
            self.size_result_frame, text="Click 'Calculate' to see download size",
            font=ctk.CTkFont(size=16), text_color="gray"
        )
        self.size_result_label.pack(expand=True, pady=40)

        # Calculate Button
        calc_btn_frame = ctk.CTkFrame(size_area, fg_color="transparent")
        calc_btn_frame.pack(fill="x")

        ctk.CTkButton(
            calc_btn_frame, text="🔄 Calculate Size",
            command=self.calculate_size_new,
            height=45, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#1f538d", "#3b8ed0")
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.start_download_btn = ctk.CTkButton(
            calc_btn_frame, text="Start Download →",
            command=self.goto_download_view,
            height=45, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2CC985", "#2FA572"), hover_color=("#28B872", "#298F65"),
            state="disabled"
        )
        self.start_download_btn.pack(side="left", expand=True, fill="x", padx=(10, 0))

        # Bottom Navigation
        nav_frame = ctk.CTkFrame(view, fg_color="transparent")
        nav_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        ctk.CTkButton(
            nav_frame, text="← Back to Configure",
            command=self.show_config_view,
            height=40, font=ctk.CTkFont(size=13),
            fg_color=("#505050", "#404040")
        ).pack(side="left")

        # Auto-populate summary
        self.update_config_summary()

    def show_download_view(self):
        """Show View 3: Download Progress."""
        self.clear_content()
        self.update_stepper(3)

        view = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        view.grid(row=0, column=0, sticky="nsew")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        # Overall Progress Bar (Top)
        progress_top = ctk.CTkFrame(view, corner_radius=10)
        progress_top.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            progress_top, text="📥 Overall Progress",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(progress_top, variable=self.progress_var, height=25)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 5))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_top, text="Ready to start download...",
            font=ctk.CTkFont(size=13), anchor="w"
        )
        self.progress_label.pack(fill="x", padx=20, pady=(0, 15))

        # Main Content Area
        main_content = ctk.CTkFrame(view, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_columnconfigure(1, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        # Left: Stats Panel
        stats_panel = ctk.CTkFrame(main_content, corner_radius=10, width=300)
        stats_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        stats_panel.grid_propagate(False)

        ctk.CTkLabel(
            stats_panel, text="📊 Statistics",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 15))

        # File Progress
        file_prog_container = ctk.CTkFrame(stats_panel, fg_color=("#D0D0D0", "#333333"), corner_radius=8)
        file_prog_container.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            file_prog_container, text="Current File",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.file_progress_var = ctk.DoubleVar()
        self.file_progress_bar = ctk.CTkProgressBar(
            file_prog_container, variable=self.file_progress_var, height=18
        )
        self.file_progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.file_progress_bar.set(0)

        self.file_progress_label = ctk.CTkLabel(
            file_prog_container, text="Waiting...",
            font=ctk.CTkFont(size=11), anchor="w"
        )
        self.file_progress_label.pack(fill="x", padx=15, pady=(0, 10))

        # Control Buttons
        button_container = ctk.CTkFrame(stats_panel, fg_color="transparent")
        button_container.pack(fill="x", padx=15, pady=(20, 0))

        self.pause_button = ctk.CTkButton(
            button_container, text="⏸ Pause",
            command=self.pause_download,
            height=38, font=ctk.CTkFont(size=13),
            fg_color=("#FF9500", "#FF9500"), hover_color=("#E68600", "#E68600")
        )
        self.pause_button.pack(fill="x", pady=(0, 8))

        self.cancel_button = ctk.CTkButton(
            button_container, text="⏹ Cancel",
            command=self.cancel_download,
            height=38, font=ctk.CTkFont(size=13),
            fg_color=("#FF3B30", "#FF453A"), hover_color=("#E6352A", "#E63E34")
        )
        self.cancel_button.pack(fill="x")

        # Right: Activity Log
        log_panel = ctk.CTkFrame(main_content, corner_radius=10)
        log_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            log_panel, text="📋 Activity Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.log_text = ctk.CTkTextbox(log_panel, wrap="word", font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # Navigation functions
    def goto_calculate_view(self):
        """Navigate to calculate view with validation."""
        # Validate inputs
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory")
            return

        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        tables = self.get_selected_tables()

        if start > end:
            messagebox.showerror("Error", "Start date must be before end date")
            return

        # Navigate to calculate view
        self.show_calculate_view()

    def goto_download_view(self):
        """Navigate to download view and start download."""
        self.show_download_view()
        # Auto-start download
        self.root.after(500, self.start_download_internal)

    def update_config_summary(self):
        """Update configuration summary in calculate view."""
        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
            days = (end - start).days + 1
            tables = self.get_selected_tables()

            # Clear old summary
            for widget in self.summary_container.winfo_children():
                widget.destroy()

            # Create grid layout for summary
            items = [
                ("📁", "Directory:", self.output_dir.get() or 'Not set'),
                ("📅", "Period:", f"{self.start_date.get()} to {self.end_date.get()} ({days} days)"),
                ("📊", "Tables:", f"{', '.join(tables) if tables else 'None selected'}"),
                ("⚙️", "Remove .gz:", 'Yes' if self.remove_gz.get() else 'No')
            ]

            for i, (icon, label, value) in enumerate(items):
                # Icon
                ctk.CTkLabel(
                    self.summary_container, text=icon,
                    font=ctk.CTkFont(size=14)
                ).grid(row=i, column=0, sticky="w", padx=(15, 5), pady=8)

                # Label
                ctk.CTkLabel(
                    self.summary_container, text=label,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    anchor="w"
                ).grid(row=i, column=1, sticky="w", padx=5, pady=8)

                # Value
                ctk.CTkLabel(
                    self.summary_container, text=value,
                    font=ctk.CTkFont(size=13),
                    anchor="w", text_color=("gray30", "gray70")
                ).grid(row=i, column=2, sticky="w", padx=(5, 15), pady=8)

            self.summary_container.grid_columnconfigure(2, weight=1)

        except:
            # Fallback for errors
            ctk.CTkLabel(
                self.summary_container, text="Invalid configuration",
                font=ctk.CTkFont(size=13), text_color="red"
            ).grid(row=0, column=0, padx=15, pady=15)

    def calculate_size_new(self):
        """Calculate and display download size."""
        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
            tables = self.get_selected_tables()

            if start > end:
                messagebox.showerror("Error", "Start date must be before end date")
                return

            # Calculate
            downloader = BlockchairDownloader(self.output_dir.get() or "/tmp")
            compressed_gb, uncompressed_gb = downloader.estimate_size(start, end, tables)

            self.calculated_size_compressed = compressed_gb
            self.calculated_size_uncompressed = uncompressed_gb

            days = (end - start).days + 1

            # Clear old result
            for widget in self.size_result_frame.winfo_children():
                widget.destroy()

            # Display result
            result_container = ctk.CTkFrame(self.size_result_frame, fg_color="transparent")
            result_container.pack(expand=True, pady=30)

            ctk.CTkLabel(
                result_container, text="💾 Estimated Download Size",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(0, 15))

            size_text = f"📦 Compressed (.gz): ~{compressed_gb:.1f} GB\n"
            size_text += f"📂 Uncompressed (.tsv): ~{uncompressed_gb:.1f} GB\n\n"

            if self.remove_gz.get():
                size_text += f"💿 Total disk space needed: ~{uncompressed_gb:.1f} GB"
            else:
                size_text += f"💿 Total disk space needed: ~{compressed_gb + uncompressed_gb:.1f} GB"

            ctk.CTkLabel(
                result_container, text=size_text,
                font=ctk.CTkFont(size=14), justify="left"
            ).pack()

            # Enable start button
            self.start_download_btn.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def check_for_incomplete_downloads(self):
        """Check for incomplete downloads and offer to resume."""
        # Will check all common locations for state files
        common_paths = [
            Path.home() / "bitcoin_data",
            Path("/Volumes/MySSD/bitcoin_data"),
            Path("/Volumes/ExternalSSD/bitcoin_data"),
            Path("D:/bitcoin_data"),
            Path("E:/bitcoin_data"),
        ]

        for path in common_paths:
            state_file = path / ".download_state.json"
            if state_file.exists():
                try:
                    state = DownloadState(state_file)

                    # Check if we should offer to resume
                    output_dir = state.get('output_dir')
                    start_date = state.get('start_date')
                    end_date = state.get('end_date')
                    tables = state.get('tables')
                    remove_gz = state.get('remove_gz', True)  # Default True

                    if output_dir and start_date and end_date and tables:
                        answer = messagebox.askyesno(
                            "Resume Download?",
                            f"Found incomplete download:\n\n"
                            f"Location: {output_dir}\n"
                            f"Period: {start_date} to {end_date}\n"
                            f"Tables: {', '.join(tables)}\n"
                            f"Remove .gz: {remove_gz}\n\n"
                            f"Resume this download?"
                        )

                        if answer:
                            self.output_dir.set(output_dir)
                            self.start_date.set(start_date)
                            self.end_date.set(end_date)

                            # Set remove_gz option
                            self.remove_gz.set(remove_gz)

                            self.log(f"✓ Loaded previous download configuration")
                            self.log(f"  Period: {start_date} to {end_date}")
                            self.log(f"  Tables: {', '.join(tables)}")
                            self.log(f"  Remove .gz: {remove_gz}")
                            self.log(f"  Files that already exist will be skipped automatically")
                            return
                except:
                    pass

    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)

    def set_preset(self, start: str, end: str):
        """Set date preset."""
        self.start_date.set(start)
        self.end_date.set(end)

    def set_preset_relative(self, days: int):
        """Set date preset relative to today (last N days)."""
        from datetime import datetime, timedelta
        end = datetime.now()
        start = end - timedelta(days=days - 1)  # -1 because we include today
        self.start_date.set(start.strftime("%Y-%m-%d"))
        self.end_date.set(end.strftime("%Y-%m-%d"))

    def get_selected_tables(self) -> List[str]:
        """Get all tables (always downloads all 3)."""
        return ["blocks", "transactions", "outputs"]

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    def log(self, message: str):
        """Add message to log."""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Process log messages from queue."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_log_queue)

    def start_download_internal(self):
        """Start download in background thread (called from download view)."""
        if self.is_downloading:
            return

        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
            tables = self.get_selected_tables()

            # Create output directory
            output_path = Path(self.output_dir.get())
            output_path.mkdir(parents=True, exist_ok=True)

            # Start download thread
            self.is_downloading = True
            self.log_text.delete("1.0", "end")
            self.progress_var.set(0)
            self.file_progress_var.set(0)

            self.download_thread = threading.Thread(
                target=self.download_worker,
                args=(start, end, tables),
                daemon=True
            )
            self.download_thread.start()

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.is_downloading = False

    def pause_download(self):
        """Pause/resume download."""
        if not self.downloader:
            return

        if self.downloader.paused:
            # Resume
            self.downloader.resume()
            self.pause_button.configure(text="⏸ Pause")
            self.log("▶ Download resumed")
        else:
            # Pause
            self.downloader.pause()
            self.pause_button.configure(text="▶ Resume")
            self.log("⏸ Download paused (you can close and resume later)")

    def cancel_download(self):
        """Cancel download."""
        if not self.downloader:
            return

        answer = messagebox.askyesno(
            "Cancel Download",
            "Are you sure you want to cancel?\n\n"
            "You can resume later - already downloaded files will be kept."
        )

        if answer:
            self.downloader.cancel()
            self.log("⏹ Cancelling download...")

    def download_worker(self, start: datetime, end: datetime, tables: List[str]):
        """Worker thread for downloading."""
        try:
            self.downloader = BlockchairDownloader(self.output_dir.get())

            def progress_callback(current, total):
                pct = (current / total) * 100
                self.progress_var.set(pct)
                self.progress_label.config(text=f"Overall: {current}/{total} files ({pct:.1f}%)")

            def file_progress_callback(pct, downloaded, total, current_file, total_files):
                self.file_progress_var.set(pct)
                mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                self.file_progress_label.config(
                    text=f"Current file: {pct:.1f}% ({mb:.1f}/{total_mb:.1f} MB) • File {current_file}/{total_files}"
                )

            def log_callback(message):
                self.log(message)

            self.log("="*60)
            self.log("BITCOIN BLOCKCHAIN DATA DOWNLOAD")
            self.log("="*60)
            self.log(f"Period: {start.date()} to {end.date()}")
            self.log(f"Tables: {', '.join(tables)}")
            self.log(f"Output: {self.output_dir.get()}")
            self.log(f"Remove .gz: {self.remove_gz.get()}")
            self.log("="*60)
            self.log("")
            self.log("⚠️  Downloads are sequential (Blockchair limitation)")
            self.log("   You can pause/resume anytime using the buttons.")
            self.log("   Already downloaded files will be skipped automatically.")
            self.log("")

            stats = self.downloader.download_and_extract(
                start, end, tables,
                remove_gz=self.remove_gz.get(),
                progress_callback=progress_callback,
                log_callback=log_callback,
                file_progress_callback=file_progress_callback
            )

            if not self.downloader.cancelled:
                self.log("")
                self.log("="*60)
                self.log("DOWNLOAD COMPLETE")
                self.log("="*60)
                self.log(f"Total files: {stats['total']}")
                self.log(f"✓ Successful: {stats['successful']}")
                self.log(f"⏭ Skipped: {stats['skipped']}")
                self.log(f"✗ Failed: {stats['failed']}")
                self.log(f"📦 Downloaded: {stats['downloaded_mb']:.1f} MB")
                self.log("="*60)
                self.log("")
                self.log(f"Data saved to: {self.output_dir.get()}/extracted")
                self.log("")
                self.log("Next steps:")
                self.log("1. Open Jupyter: ./start_project.sh")
                self.log("2. Open: notebooks/01_data_exploration.ipynb")
                self.log("3. Set: config = DataConfig(source='local')")

                messagebox.showinfo("Success",
                                  f"Download complete!\n\n"
                                  f"Successful: {stats['successful']}\n"
                                  f"Skipped: {stats['skipped']}\n"
                                  f"Failed: {stats['failed']}")

        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}")
            messagebox.showerror("Download Failed", str(e))

        finally:
            self.is_downloading = False
            self.downloader = None

    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Entry point for CLI command."""
    app = DownloaderGUI()
    app.run()


if __name__ == "__main__":
    main()
