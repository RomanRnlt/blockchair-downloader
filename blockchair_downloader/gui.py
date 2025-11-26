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
    """Modern GUI for Bitcoin data downloader with pause/resume support."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Bitcoin Blockchain Data Downloader")
        self.root.geometry("1000x800")

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Variables
        self.output_dir = ctk.StringVar()
        self.start_date = ctk.StringVar(value="2021-01-01")
        self.end_date = ctk.StringVar(value="2021-12-31")
        self.remove_gz = ctk.BooleanVar(value=True)

        # Table selection
        self.table_blocks = ctk.BooleanVar(value=True)
        self.table_transactions = ctk.BooleanVar(value=True)
        self.table_outputs = ctk.BooleanVar(value=True)

        # Download state
        self.is_downloading = False
        self.downloader: Optional[BlockchairDownloader] = None
        self.download_thread = None
        self.log_queue = queue.Queue()

        self.setup_ui()
        self.process_log_queue()
        self.check_for_incomplete_downloads()

    def setup_ui(self):
        """Setup modern UI components."""
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

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

        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.root, corner_radius=10)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        main_frame.grid_columnconfigure(0, weight=1)

        # Output Directory Section
        dir_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        dir_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        dir_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dir_frame, text="📁 Output Directory", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 10)
        )

        self.dir_entry = ctk.CTkEntry(dir_frame, textvariable=self.output_dir, height=35)
        self.dir_entry.grid(row=1, column=0, sticky="ew", padx=(15, 10), pady=(0, 15))

        ctk.CTkButton(
            dir_frame, text="Browse", command=self.browse_directory,
            width=100, height=35
        ).grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        # Date Range Section
        date_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        date_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        date_frame.grid_columnconfigure((1, 2), weight=1)

        ctk.CTkLabel(date_frame, text="📅 Date Range", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(15, 10)
        )

        ctk.CTkLabel(date_frame, text="Start Date:").grid(row=1, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkEntry(date_frame, textvariable=self.start_date, height=35, width=150).grid(
            row=1, column=1, sticky="w", padx=10, pady=5
        )

        ctk.CTkLabel(date_frame, text="End Date:").grid(row=2, column=0, sticky="w", padx=15, pady=5)
        ctk.CTkEntry(date_frame, textvariable=self.end_date, height=35, width=150).grid(
            row=2, column=1, sticky="w", padx=10, pady=5
        )

        # Quick Presets
        preset_label = ctk.CTkLabel(date_frame, text="Quick Presets:", font=ctk.CTkFont(size=12, weight="bold"))
        preset_label.grid(row=1, column=2, sticky="w", padx=15)

        preset_buttons = ctk.CTkFrame(date_frame, fg_color="transparent")
        preset_buttons.grid(row=2, column=2, sticky="w", padx=15, pady=(0, 15))

        ctk.CTkButton(
            preset_buttons, text="Year 2021", width=100, height=28,
            command=lambda: self.set_preset("2021-01-01", "2021-12-31")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            preset_buttons, text="Q1 2021", width=100, height=28,
            command=lambda: self.set_preset("2021-01-01", "2021-03-31")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            preset_buttons, text="Jan 2021", width=100, height=28,
            command=lambda: self.set_preset("2021-01-01", "2021-01-31")
        ).pack(side="left", padx=5)

        # Tables Selection
        tables_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        tables_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(tables_frame, text="📊 Tables to Download", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 10)
        )

        ctk.CTkCheckBox(tables_frame, text="Blocks (~1 MB/day)", variable=self.table_blocks).pack(
            anchor="w", padx=15, pady=5
        )
        ctk.CTkCheckBox(tables_frame, text="Transactions (~150 MB/day)", variable=self.table_transactions).pack(
            anchor="w", padx=15, pady=5
        )
        ctk.CTkCheckBox(tables_frame, text="Outputs (~250 MB/day)", variable=self.table_outputs).pack(
            anchor="w", padx=15, pady=(5, 15)
        )

        # Options
        options_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        options_frame.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(options_frame, text="⚙️ Options", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 10)
        )

        ctk.CTkCheckBox(
            options_frame,
            text="Remove .gz files after extraction (saves ~70% disk space)",
            variable=self.remove_gz
        ).pack(anchor="w", padx=15, pady=(5, 15))

        # Size Estimate
        size_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        size_frame.grid(row=4, column=0, sticky="ew", pady=(0, 15))

        self.size_label = ctk.CTkLabel(
            size_frame, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1f538d", "#3b8ed0")
        )
        self.size_label.pack(pady=15)

        ctk.CTkButton(
            size_frame, text="Calculate Download Size",
            command=self.calculate_size, height=35
        ).pack(pady=(0, 15))

        # Control Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, sticky="ew", pady=(0, 15))

        self.start_button = ctk.CTkButton(
            button_frame, text="▶ Start Download",
            command=self.start_download,
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2CC985", "#2FA572"), hover_color=("#28B872", "#298F65")
        )
        self.start_button.pack(side="left", padx=5, expand=True, fill="x")

        self.pause_button = ctk.CTkButton(
            button_frame, text="⏸ Pause",
            command=self.pause_download, state="disabled",
            height=40, font=ctk.CTkFont(size=14),
            fg_color=("#FF9500", "#FF9500"), hover_color=("#E68600", "#E68600")
        )
        self.pause_button.pack(side="left", padx=5, expand=True, fill="x")

        self.cancel_button = ctk.CTkButton(
            button_frame, text="⏹ Cancel",
            command=self.cancel_download, state="disabled",
            height=40, font=ctk.CTkFont(size=14),
            fg_color=("#FF3B30", "#FF453A"), hover_color=("#E6352A", "#E63E34")
        )
        self.cancel_button.pack(side="left", padx=5, expand=True, fill="x")

        # Progress Section
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        progress_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 0))

        ctk.CTkLabel(progress_frame, text="📥 Download Progress", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 10)
        )

        # Overall Progress
        self.progress_var = ctk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(progress_frame, variable=self.progress_var, height=20)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready to download", anchor="w")
        self.progress_label.pack(fill="x", padx=15, pady=(0, 10))

        # File Progress
        self.file_progress_var = ctk.DoubleVar()
        self.file_progress_bar = ctk.CTkProgressBar(progress_frame, variable=self.file_progress_var, height=15)
        self.file_progress_bar.pack(fill="x", padx=15, pady=(0, 5))
        self.file_progress_bar.set(0)

        self.file_progress_label = ctk.CTkLabel(progress_frame, text="", anchor="w")
        self.file_progress_label.pack(fill="x", padx=15, pady=(0, 10))

        # Log Text
        self.log_text = ctk.CTkTextbox(progress_frame, height=200, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

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

                            # Set table checkboxes
                            self.table_blocks.set('blocks' in tables)
                            self.table_transactions.set('transactions' in tables)
                            self.table_outputs.set('outputs' in tables)

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

    def get_selected_tables(self) -> List[str]:
        """Get selected tables."""
        tables = []
        if self.table_blocks.get():
            tables.append("blocks")
        if self.table_transactions.get():
            tables.append("transactions")
        if self.table_outputs.get():
            tables.append("outputs")
        return tables

    def parse_date(self, date_str: str) -> datetime:
        """Parse date string."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")

    def calculate_size(self):
        """Calculate and display estimated size."""
        try:
            start = self.parse_date(self.start_date.get())
            end = self.parse_date(self.end_date.get())
            tables = self.get_selected_tables()

            if not tables:
                messagebox.showerror("Error", "Please select at least one table")
                return

            if start > end:
                messagebox.showerror("Error", "Start date must be before end date")
                return

            # Calculate
            downloader = BlockchairDownloader(self.output_dir.get() or "/tmp")
            compressed_gb, uncompressed_gb = downloader.estimate_size(start, end, tables)

            days = (end - start).days + 1

            # Display
            text = f"📊 Estimated Size for {days} days:\n"
            text += f"   Compressed (.gz): ~{compressed_gb:.1f} GB\n"
            text += f"   Uncompressed (.tsv): ~{uncompressed_gb:.1f} GB\n"

            if self.remove_gz.get():
                text += f"   Total (with --remove-gz): ~{uncompressed_gb:.1f} GB"
            else:
                text += f"   Total (keeping .gz): ~{compressed_gb + uncompressed_gb:.1f} GB"

            self.size_label.config(text=text)

        except Exception as e:
            messagebox.showerror("Error", str(e))

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

    def start_download(self):
        """Start download in background thread."""
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return

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
        if not tables:
            messagebox.showerror("Error", "Please select at least one table")
            return

        if start > end:
            messagebox.showerror("Error", "Start date must be before end date")
            return

        # Create output directory
        output_path = Path(self.output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)

        # Confirm
        days = (end - start).days + 1
        confirm = messagebox.askyesno(
            "Confirm Download",
            f"Download {days} days of data for {len(tables)} table(s)?\n\n"
            f"This may take several hours.\n"
            f"You can pause and resume anytime.\n"
            f"Already downloaded files will be skipped automatically."
        )

        if not confirm:
            return

        # Start download thread
        self.is_downloading = True
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="⏸ Pause")
        self.cancel_button.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.progress_var.set(0)
        self.file_progress_var.set(0)

        self.download_thread = threading.Thread(
            target=self.download_worker,
            args=(start, end, tables),
            daemon=True
        )
        self.download_thread.start()

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
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
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
