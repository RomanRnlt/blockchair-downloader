# Blockchair Downloader

Modern GUI tool to download Bitcoin blockchain data from Blockchair dumps.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)

## ✨ Features

- **Modern Dark Mode UI** - Clean, professional interface built with CustomTkinter
- **Pause/Resume** - Pause downloads anytime, resume later (even after closing the app)
- **Auto-Resume** - Automatically detects incomplete downloads on restart
- **Progress Tracking** - Real-time progress bars with ETA calculation
- **Failsafe** - Already downloaded files are automatically skipped
- **Cross-Platform** - Works on macOS, Windows, and Linux

## 🚀 Quick Start

### Installation

```bash
pip install blockchair-downloader
```

### Usage

```bash
blockchair-downloader
```

That's it! The GUI will open automatically.

## 📋 Requirements

**macOS:**
```bash
brew install python-tk@3.13
```

**Windows:**
- Python 3.9+ from [python.org](https://python.org) (includes tkinter)

**Linux:**
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
```

## 🎯 How to Use

1. **Select Output Directory** - Choose where to save downloaded data
2. **Choose Date Range** - Use presets (Year 2021, Q1 2021) or custom dates
3. **Select Tables** - Blocks, Transactions, and/or Outputs
4. **Calculate Size** - See estimated download size before starting
5. **Start Download** - Click and relax! Pause/resume anytime

## 💾 Download Size Estimates

| Period | Size (uncompressed) |
|--------|---------------------|
| 1 Day | ~1.3 GB |
| 1 Week | ~9 GB |
| 1 Month | ~40 GB |
| Q1 2021 | ~120 GB |
| Year 2021 | ~480 GB |

*Note: .gz files are automatically deleted after extraction (saves ~70% disk space)*

## 🔧 Troubleshooting

### "No module named '_tkinter'"

**macOS:**
```bash
brew install python-tk@3.13
```

**Windows:**
Reinstall Python from [python.org](https://python.org) and check the "tcl/tk" option

**Linux:**
```bash
sudo apt-get install python3-tk
```

### "No module named 'customtkinter'"

```bash
pip install --upgrade blockchair-downloader
```

## 📖 About

This tool downloads Bitcoin blockchain data from [Blockchair](https://blockchair.com) dumps in TSV format. Perfect for:

- Blockchain research and analysis
- Machine learning on Bitcoin data
- Entity resolution and clustering
- Academic projects and theses

Data is downloaded from: `https://gz.blockchair.com/bitcoin/`

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/RomanRnlt/blockchair-downloader
cd blockchair-downloader

# Install in development mode
pip install -e .

# Run
blockchair-downloader
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Credits

- Data source: [Blockchair](https://blockchair.com)
- UI framework: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- Built for the [Bitcoin Whale Intelligence](https://github.com/RomanRnlt/bitcoin-whale-intelligence) project

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/RomanRnlt/blockchair-downloader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RomanRnlt/blockchair-downloader/discussions)

---

Made with ❤️ for Bitcoin blockchain researchers
