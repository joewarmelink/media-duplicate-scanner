#!/usr/bin/env python3
"""
Media Duplicate Scanner

A Python utility to scan multiple media roots and report duplicate movies and TV episodes.
Supports various file formats and provides detailed reporting with logging.
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class MediaDuplicateScanner:
    """Scans media directories for duplicate content."""
    
    # Common video file extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', 
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.m2ts'
    }
    
    # Common audio file extensions
    AUDIO_EXTENSIONS = {
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'
    }
    
    def __init__(self, log_level: str = 'INFO', output_dir: str = './media-dup-reports', log_dir: str = './media-dup-reports/logs'):
        """Initialize the scanner with configuration."""
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir)
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging(log_level)
        
        # Storage for duplicates
        self.duplicates = defaultdict(list)
        self.file_hashes = {}
        self.scan_stats = {
            'total_files': 0,
            'video_files': 0,
            'audio_files': 0,
            'duplicate_groups': 0,
            'total_duplicates': 0,
            'scan_time': 0
        }
    
    def _setup_logging(self, log_level: str):
        """Configure logging with file and console handlers."""
        log_level = getattr(logging, log_level.upper())
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'scanner_{timestamp}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Setup logger
        self.logger = logging.getLogger('MediaDuplicateScanner')
        self.logger.setLevel(log_level)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized. Log file: {log_file}")
    
    def _is_media_file(self, file_path: Path) -> bool:
        """Check if file is a media file based on extension."""
        return file_path.suffix.lower() in (self.VIDEO_EXTENSIONS | self.AUDIO_EXTENSIONS)
    
    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def _extract_media_info(self, file_path: Path) -> Dict:
        """Extract basic media information from filename."""
        filename = file_path.stem
        extension = file_path.suffix.lower()
        
        # Try to extract title, year, and quality from filename
        info = {
            'filename': file_path.name,
            'extension': extension,
            'size': file_path.stat().st_size,
            'path': str(file_path),
            'title': filename,
            'year': None,
            'quality': None,
            'type': 'video' if extension in self.VIDEO_EXTENSIONS else 'audio'
        }
        
        # Common patterns for extracting year and quality
        year_pattern = r'\((\d{4})\)|\.(\d{4})\.'
        quality_pattern = r'(1080p|720p|480p|4K|HDRip|BRRip|WEBRip|BluRay|DVD)'
        
        # Extract year
        year_match = re.search(year_pattern, filename)
        if year_match:
            info['year'] = year_match.group(1) or year_match.group(2)
        
        # Extract quality
        quality_match = re.search(quality_pattern, filename, re.IGNORECASE)
        if quality_match:
            info['quality'] = quality_match.group(1)
        
        return info
    
    def scan_directory(self, directory: Path) -> None:
        """Scan a directory for media files and calculate hashes."""
        self.logger.info(f"Scanning directory: {directory}")
        
        if not directory.exists():
            self.logger.error(f"Directory does not exist: {directory}")
            return
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and self._is_media_file(file_path):
                self.scan_stats['total_files'] += 1
                
                if file_path.suffix.lower() in self.VIDEO_EXTENSIONS:
                    self.scan_stats['video_files'] += 1
                else:
                    self.scan_stats['audio_files'] += 1
                
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    media_info = self._extract_media_info(file_path)
                    
                    if file_hash in self.file_hashes:
                        # Duplicate found
                        self.duplicates[file_hash].append(media_info)
                        self.scan_stats['total_duplicates'] += 1
                        self.logger.debug(f"Duplicate found: {file_path.name}")
                    else:
                        # First occurrence
                        self.file_hashes[file_hash] = media_info
                        self.duplicates[file_hash] = [media_info]
    
    def find_duplicates(self) -> Dict:
        """Find and organize duplicate files."""
        duplicate_groups = {}
        
        for file_hash, files in self.duplicates.items():
            if len(files) > 1:
                duplicate_groups[file_hash] = files
                self.scan_stats['duplicate_groups'] += 1
        
        return duplicate_groups
    
    def generate_report(self, duplicate_groups: Dict) -> None:
        """Generate detailed report of duplicates."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f'duplicate_report_{timestamp}.json'
        summary_file = self.output_dir / f'summary_{timestamp}.txt'
        
        # Generate JSON report
        report_data = {
            'scan_timestamp': datetime.now().isoformat(),
            'scan_stats': self.scan_stats,
            'duplicate_groups': duplicate_groups
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Generate text summary
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("MEDIA DUPLICATE SCANNER REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Scan completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total files scanned: {self.scan_stats['total_files']}\n")
            f.write(f"Video files: {self.scan_stats['video_files']}\n")
            f.write(f"Audio files: {self.scan_stats['audio_files']}\n")
            f.write(f"Duplicate groups found: {self.scan_stats['duplicate_groups']}\n")
            f.write(f"Total duplicate files: {self.scan_stats['total_duplicates']}\n\n")
            
            if duplicate_groups:
                f.write("DUPLICATE GROUPS:\n")
                f.write("-" * 20 + "\n\n")
                
                for i, (file_hash, files) in enumerate(duplicate_groups.items(), 1):
                    f.write(f"Group {i} (Hash: {file_hash[:16]}...)\n")
                    f.write(f"Files ({len(files)}):\n")
                    
                    for j, file_info in enumerate(files, 1):
                        f.write(f"  {j}. {file_info['filename']}\n")
                        f.write(f"     Path: {file_info['path']}\n")
                        f.write(f"     Size: {file_info['size']:,} bytes\n")
                        if file_info['year']:
                            f.write(f"     Year: {file_info['year']}\n")
                        if file_info['quality']:
                            f.write(f"     Quality: {file_info['quality']}\n")
                        f.write("\n")
            else:
                f.write("No duplicates found!\n")
        
        self.logger.info(f"Report generated: {report_file}")
        self.logger.info(f"Summary generated: {summary_file}")
        
        # Print summary to console
        print(f"\nScan completed!")
        print(f"Total files: {self.scan_stats['total_files']}")
        print(f"Duplicate groups: {self.scan_stats['duplicate_groups']}")
        print(f"Total duplicates: {self.scan_stats['total_duplicates']}")
        print(f"Reports saved to: {self.output_dir}")


def main():
    """Main entry point for the media duplicate scanner."""
    parser = argparse.ArgumentParser(
        description='Scan media directories for duplicate content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python media_duplicate_scanner.py /path/to/media1 /path/to/media2
  python media_duplicate_scanner.py --log-level DEBUG --output-dir ./reports /path/to/media
  python media_duplicate_scanner.py --log-level INFO --output-dir ./media-dup-reports --log-dir ./media-dup-reports/logs /path/to/media1 /path/to/media2
        """
    )
    
    parser.add_argument(
        'directories',
        nargs='+',
        help='Directories to scan for media files'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./media-dup-reports',
        help='Directory for output reports (default: ./media-dup-reports)'
    )
    
    parser.add_argument(
        '--log-dir',
        default='./media-dup-reports/logs',
        help='Directory for log files (default: ./media-dup-reports/logs)'
    )
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = MediaDuplicateScanner(
        log_level=args.log_level,
        output_dir=args.output_dir,
        log_dir=args.log_dir
    )
    
    start_time = datetime.now()
    
    try:
        # Scan each directory
        for directory in args.directories:
            scanner.scan_directory(Path(directory))
        
        # Find duplicates
        duplicate_groups = scanner.find_duplicates()
        
        # Calculate scan time
        scanner.scan_stats['scan_time'] = (datetime.now() - start_time).total_seconds()
        
        # Generate report
        scanner.generate_report(duplicate_groups)
        
    except KeyboardInterrupt:
        scanner.logger.info("Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        scanner.logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
