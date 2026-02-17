<div align="center">
  <h1>Blockchair Downloader</h1>
  <h3>Desktop GUI for Bitcoin Blockchain Data Dumps</h3>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.9-blue" alt="Python">
    <img src="https://img.shields.io/badge/gui-CustomTkinter-orange" alt="GUI">
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

**Blockchair Downloader** is a cross-platform desktop app that downloads Bitcoin blockchain data from [Blockchair](https://gz.blockchair.com/bitcoin/) public dumps. 3-step wizard: configure dates, preview sizes, download with pause/resume. Downloads all four core tables — blocks, transactions, inputs, and outputs.

## Key Features

- **Pause / Resume / Cancel** — Pause mid-download and pick up where you left off. Cancel preserves partial progress.
- **Auto-Resume on Restart** — Saves state to `.download_state.json`. Detects incomplete downloads on launch and offers to continue.
- **Skip Already Downloaded** — Checks for existing `.tsv` files before downloading. Re-running is safe.
- **Size Preview** — Fetches actual file sizes from Blockchair before downloading. Shows compressed + estimated uncompressed totals.
- **Smart Extraction** — Downloads `.tsv.gz`, extracts to `.tsv`, optionally deletes compressed files to save ~60–70% disk space.
- **Date Presets** — Quick buttons for 1 week, 1 month, quarter, or full year ranges.

## 3-Step Wizard

| Step | What happens |
|---|---|
| **1. Configure** | Set output directory, date range, and options |
| **2. Calculate Size** | Preview download size per table + total |
| **3. Download** | Live progress bars, speed indicator, activity log |

## Output Structure

```
output_dir/
└── bitcoin_blockchain_2024-01-01_to_2024-01-31/
    ├── raw/
    │   ├── blocks/          .tsv.gz (deleted if remove_gz enabled)
    │   ├── transactions/
    │   ├── inputs/
    │   └── outputs/
    └── extracted/
        ├── blocks/          .tsv files ready to use
        ├── transactions/
        ├── inputs/
        └── outputs/
```

## Download Size Reference

| Period | Compressed | Uncompressed |
|---|---|---|
| 1 day | ~250 MB | ~650 MB |
| 1 week | ~1.5 GB | ~4 GB |
| 1 month | ~7 GB | ~18 GB |
| 1 quarter | ~20 GB | ~50 GB |
| 1 year | ~80 GB | ~200 GB |

## Quick Start

```bash
pip install blockchair-downloader
blockchair-downloader
```

### From Source

```bash
git clone https://github.com/RomanRnlt/blockchair-downloader.git
cd blockchair-downloader
pip install -e .
blockchair-downloader
```

### Platform Prerequisites (tkinter)

| Platform | Command |
|---|---|
| macOS | `brew install python-tk` |
| Ubuntu/Debian | `sudo apt-get install python3-tk` |
| Windows | Included with python.org installer |

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| GUI | CustomTkinter (dark-mode tkinter wrapper) |
| Downloads | urllib (stdlib) |
| Extraction | gzip + shutil (stdlib) |
| State | JSON file persistence |
| Threading | Background downloads, responsive UI |

## Use Cases

- **Research** — Academic analysis of Bitcoin transaction patterns
- **Machine Learning** — Training data for blockchain entity resolution
- **Entity Clustering** — Feed into whale detection pipelines (see [Bitcoin Whale Intelligence](https://github.com/RomanRnlt/bitcoin-whale-intelligence))
- **Data Archival** — Local backup of blockchain history

## Troubleshooting

### "No module named '_tkinter'"

| Platform | Fix |
|---|---|
| macOS | `brew install python-tk` |
| Windows | Reinstall Python from python.org, check "tcl/tk" option |
| Linux | `sudo apt-get install python3-tk` |

## License

MIT — see [LICENSE](LICENSE)
