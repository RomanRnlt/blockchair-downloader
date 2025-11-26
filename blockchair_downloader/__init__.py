"""
Blockchair Downloader - Modern GUI for Bitcoin blockchain data downloads.

A cross-platform desktop application to download Bitcoin blockchain data
from Blockchair dumps with pause/resume support and modern UI.
"""

__version__ = "1.0.0"
__author__ = "Roman Rinelt"

from .gui import main

__all__ = ["main"]
