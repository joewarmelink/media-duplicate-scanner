# Media Duplicate Scanner

A Python utility to scan multiple media roots and report duplicate movies and TV episodes. The scanner uses SHA-256 hashing to identify exact duplicates and provides detailed reporting with logging.

## Features

- **Multi-directory scanning**: Scan multiple media directories in a single run
- **Comprehensive file support**: Supports common video (mp4, avi, mkv, mov, etc.) and audio (mp3, wav, flac, etc.) formats
- **Exact duplicate detection**: Uses SHA-256 hashing for precise duplicate identification
- **Detailed reporting**: Generates both JSON and text reports with file information
- **Metadata extraction**: Automatically extracts year and quality information from filenames
- **Comprehensive logging**: File and console logging with configurable levels
- **Performance tracking**: Tracks scan statistics and timing

## Installation

No external dependencies required! This tool uses only Python standard library modules.

```bash
# Clone or download the project
# No pip install needed
```

## Usage

### Basic Usage

```bash
# Scan a single directory
python media_duplicate_scanner.py /path/to/media

# Scan multiple directories
python media_duplicate_scanner.py /path/to/media1 /path/to/media2 /path/to/media3
```

### Advanced Usage

```bash
# With custom logging level and output directory
python media_duplicate_scanner.py --log-level DEBUG --output-dir ./reports /path/to/media

# Full example with all options
python media_duplicate_scanner.py --log-level INFO --output-dir ./media-dup-reports --log-dir ./media-dup-reports/logs /path/to/media1 /path/to/media2
```

### Background Execution

```bash
# Run in background (Linux/Mac)
nohup python media_duplicate_scanner.py --log-level INFO --output-dir ./media-dup-reports --log-dir ./media-dup-reports/logs /path/to/media > /dev/null 2>&1 &

# Windows background execution
start /B python media_duplicate_scanner.py --log-level INFO --output-dir ./media-dup-reports --log-dir ./media-dup-reports/logs /path/to/media
```

## Command Line Options

- `directories`: One or more directories to scan (required)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
- `--output-dir`: Directory for output reports - default: ./media-dup-reports
- `--log-dir`: Directory for log files - default: ./media-dup-reports/logs

## Output

The scanner generates several output files:

### Reports Directory (`./media-dup-reports/`)
- `duplicate_report_YYYYMMDD_HHMMSS.json`: Detailed JSON report with all scan data
- `summary_YYYYMMDD_HHMMSS.txt`: Human-readable text summary

### Logs Directory (`./media-dup-reports/logs/`)
- `scanner_YYYYMMDD_HHMMSS.log`: Detailed scan log with timestamps

## Report Contents

### JSON Report
- Scan timestamp and statistics
- Complete file information for each duplicate group
- File paths, sizes, and extracted metadata

### Text Summary
- Scan overview and statistics
- List of duplicate groups with file details
- File paths, sizes, years, and quality information

## Supported File Formats

### Video Files
- MP4, AVI, MKV, MOV, WMV, FLV, WebM
- M4V, 3GP, OGV, TS, MTS, M2TS

### Audio Files
- MP3, WAV, FLAC, AAC, OGG, WMA, M4A

## Performance

- Uses efficient chunked reading for large files
- SHA-256 hashing ensures accurate duplicate detection
- Progress logging for long scans
- Memory-efficient processing

## Debugging

For debugging, use the DEBUG log level:

```bash
python media_duplicate_scanner.py --log-level DEBUG /path/to/media
```

This will provide detailed information about each file being processed and any issues encountered.

## Example Output

```
Scan completed!
Total files: 1,234
Duplicate groups: 5
Total duplicates: 12
Reports saved to: ./media-dup-reports
```

## License

This project is open source and available under the MIT License.
