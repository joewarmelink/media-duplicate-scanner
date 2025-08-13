#!/usr/bin/env python3
"""
Media Duplicate Scanner

A Python utility to scan multiple media roots and report duplicate movies and TV episodes.
Uses content-based matching (title/year for movies, show/season/episode for TV series).
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
from typing import Dict, List, Set, Tuple, Optional


class MediaDuplicateScanner:
    """Scans media directories for duplicate content based on metadata."""
    
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
        
        # Storage for content-based duplicates
        self.movie_groups = defaultdict(list)  # (title, year) -> [files]
        self.tv_groups = defaultdict(list)     # (show, season, episode) -> [files]
        
        self.scan_stats = {
            'total_files': 0,
            'video_files': 0,
            'audio_files': 0,
            'movie_files': 0,
            'tv_files': 0,
            'movie_duplicate_groups': 0,
            'tv_duplicate_groups': 0,
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
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for case-insensitive comparison."""
        # Remove special characters and extra whitespace, convert to lowercase
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _extract_year_from_path(self, path: Path) -> Optional[str]:
        """Extract year from path components."""
        # Look for year patterns in folder names
        year_pattern = r'\((\d{4})\)|\.(\d{4})\.|\[(\d{4})\]'
        
        # Check each component of the path
        for component in path.parts:
            match = re.search(year_pattern, component)
            if match:
                return match.group(1) or match.group(2) or match.group(3)
        
        return None
    
    def _extract_tv_episode_info(self, path: Path) -> Optional[Tuple[str, int, int]]:
        """Extract TV show, season, and episode information from path."""
        # Common TV episode patterns
        episode_patterns = [
            r'[Ss](\d{1,2})[Ee](\d{1,2})',  # S01E06, S1E6
            r'(\d{1,2})x(\d{1,2})',         # 1x06, 01x06
            r'Season\s*(\d{1,2})\s*Episode\s*(\d{1,2})',  # Season 1 Episode 6
        ]
        
        path_str = str(path)
        
        for pattern in episode_patterns:
            match = re.search(pattern, path_str, re.IGNORECASE)
            if match:
                season_num = int(match.group(1))
                episode_num = int(match.group(2))
                
                # Extract show name from the path
                show_name = self._extract_show_name(path)
                if show_name:
                    return (show_name, season_num, episode_num)
        
        return None
    
    def _extract_show_name(self, path: Path) -> Optional[str]:
        """Extract TV show name from path."""
        # Look for show name in folder structure
        # Usually it's the parent folder of the season folder
        
        path_parts = list(path.parts)
        
        # Find season folder and get its parent
        for i, part in enumerate(path_parts):
            if re.search(r'[Ss]eason|S\d{1,2}', part, re.IGNORECASE):
                if i > 0:
                    return self._normalize_title(path_parts[i-1])
        
        # If no season folder found, try to extract from filename
        filename = path.name
        # Remove episode info from filename
        clean_name = re.sub(r'[Ss]\d{1,2}[Ee]\d{1,2}|\d{1,2}x\d{1,2}', '', filename)
        clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()
        
        if clean_name:
            return self._normalize_title(clean_name)
        
        return None
    
    def _extract_movie_info(self, path: Path) -> Optional[Tuple[str, str]]:
        """Extract movie title and year from path."""
        # Look for movie folder (usually contains the movie title)
        path_parts = list(path.parts)
        
        # Try to find the movie folder (usually the parent of the file)
        for i, part in enumerate(path_parts):
            # Skip if it's a file extension
            if '.' in part and part.split('.')[-1].lower() in self.VIDEO_EXTENSIONS:
                continue
            
            # Check if this part looks like a movie title (contains year or is not a common folder name)
            if re.search(r'\(\d{4}\)|\[\d{4}\]', part) or (
                len(part) > 3 and 
                not part.lower() in ['movies', 'movie', 'films', 'film', 'videos', 'video']
            ):
                title = self._normalize_title(part)
                year = self._extract_year_from_path(path)
                if title and year:
                    return (title, year)
        
        # Fallback: try to extract from filename
        filename = path.stem
        title = self._normalize_title(filename)
        year = self._extract_year_from_path(path)
        
        if title and year:
            return (title, year)
        
        return None
    
    def _extract_media_info(self, file_path: Path) -> Dict:
        """Extract media information from file path."""
        info = {
            'filename': file_path.name,
            'extension': file_path.suffix.lower(),
            'size': file_path.stat().st_size,
            'path': str(file_path),
            'type': 'video' if file_path.suffix.lower() in self.VIDEO_EXTENSIONS else 'audio'
        }
        
        # Try to extract TV episode info first
        tv_info = self._extract_tv_episode_info(file_path)
        if tv_info:
            show_name, season, episode = tv_info
            info.update({
                'media_type': 'tv',
                'show_name': show_name,
                'season': season,
                'episode': episode,
                'title': f"{show_name} S{season:02d}E{episode:02d}"
            })
            return info
        
        # Try to extract movie info
        movie_info = self._extract_movie_info(file_path)
        if movie_info:
            title, year = movie_info
            info.update({
                'media_type': 'movie',
                'title': title,
                'year': year
            })
            return info
        
        # If we can't determine type, mark as unknown
        info['media_type'] = 'unknown'
        return info
    
    def scan_directory(self, directory: Path) -> None:
        """Scan a directory for media files and group by content."""
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
                
                # Extract media information
                media_info = self._extract_media_info(file_path)
                
                if media_info['media_type'] == 'movie':
                    self.scan_stats['movie_files'] += 1
                    # Group by title and year
                    key = (media_info['title'], media_info['year'])
                    self.movie_groups[key].append(media_info)
                    self.logger.debug(f"Movie found: {media_info['title']} ({media_info['year']})")
                
                elif media_info['media_type'] == 'tv':
                    self.scan_stats['tv_files'] += 1
                    # Group by show, season, and episode
                    key = (media_info['show_name'], media_info['season'], media_info['episode'])
                    self.tv_groups[key].append(media_info)
                    self.logger.debug(f"TV found: {media_info['show_name']} S{media_info['season']:02d}E{media_info['episode']:02d}")
                
                else:
                    self.logger.debug(f"Unknown media type: {file_path}")
    
    def find_duplicates(self) -> Dict:
        """Find and organize duplicate content."""
        duplicates = {
            'movies': {},
            'tv_series': {}
        }
        
        # Find movie duplicates
        for (title, year), files in self.movie_groups.items():
            if len(files) > 1:
                duplicates['movies'][f"{title} ({year})"] = files
                self.scan_stats['movie_duplicate_groups'] += 1
                self.scan_stats['total_duplicates'] += len(files)
        
        # Find TV duplicates
        for (show, season, episode), files in self.tv_groups.items():
            if len(files) > 1:
                key = f"{show} S{season:02d}E{episode:02d}"
                duplicates['tv_series'][key] = files
                self.scan_stats['tv_duplicate_groups'] += 1
                self.scan_stats['total_duplicates'] += len(files)
        
        return duplicates
    
    def generate_report(self, duplicates: Dict) -> None:
        """Generate detailed report of duplicates."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f'duplicate_report_{timestamp}.json'
        summary_file = self.output_dir / f'summary_{timestamp}.txt'
        
        # Generate JSON report
        report_data = {
            'scan_timestamp': datetime.now().isoformat(),
            'scan_stats': self.scan_stats,
            'duplicates': duplicates
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
            f.write(f"Movie files: {self.scan_stats['movie_files']}\n")
            f.write(f"TV files: {self.scan_stats['tv_files']}\n")
            f.write(f"Movie duplicate groups: {self.scan_stats['movie_duplicate_groups']}\n")
            f.write(f"TV duplicate groups: {self.scan_stats['tv_duplicate_groups']}\n")
            f.write(f"Total duplicate files: {self.scan_stats['total_duplicates']}\n\n")
            
            # Movie duplicates
            if duplicates['movies']:
                f.write("MOVIE DUPLICATES:\n")
                f.write("-" * 20 + "\n\n")
                
                for i, (title, files) in enumerate(duplicates['movies'].items(), 1):
                    f.write(f"Movie Group {i}: {title}\n")
                    f.write(f"Files ({len(files)}):\n")
                    
                    for j, file_info in enumerate(files, 1):
                        f.write(f"  {j}. {file_info['filename']}\n")
                        f.write(f"     Path: {file_info['path']}\n")
                        f.write(f"     Size: {file_info['size']:,} bytes\n")
                        f.write(f"     Format: {file_info['extension']}\n\n")
            
            # TV duplicates
            if duplicates['tv_series']:
                f.write("TV SERIES DUPLICATES:\n")
                f.write("-" * 20 + "\n\n")
                
                for i, (episode, files) in enumerate(duplicates['tv_series'].items(), 1):
                    f.write(f"TV Group {i}: {episode}\n")
                    f.write(f"Files ({len(files)}):\n")
                    
                    for j, file_info in enumerate(files, 1):
                        f.write(f"  {j}. {file_info['filename']}\n")
                        f.write(f"     Path: {file_info['path']}\n")
                        f.write(f"     Size: {file_info['size']:,} bytes\n")
                        f.write(f"     Format: {file_info['extension']}\n\n")
            
            if not duplicates['movies'] and not duplicates['tv_series']:
                f.write("No duplicates found!\n")
        
        self.logger.info(f"Report generated: {report_file}")
        self.logger.info(f"Summary generated: {summary_file}")
        
        # Print summary to console
        print(f"\nScan completed!")
        print(f"Total files: {self.scan_stats['total_files']}")
        print(f"Movie duplicate groups: {self.scan_stats['movie_duplicate_groups']}")
        print(f"TV duplicate groups: {self.scan_stats['tv_duplicate_groups']}")
        print(f"Total duplicates: {self.scan_stats['total_duplicates']}")
        print(f"Reports saved to: {self.output_dir}")


def main():
    """Main entry point for the media duplicate scanner."""
    parser = argparse.ArgumentParser(
        description='Scan media directories for duplicate content based on metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python media_duplicate_scanner.py /media/4TB-WD2/MOVIES /media/16TB-HM/MOVIES
  python media_duplicate_scanner.py --log-level DEBUG --output-dir ./reports /path/to/media
  python media_duplicate_scanner.py --log-level INFO --output-dir ./media-dup-reports --log-dir ./media-dup-reports/logs /media/4TB-WD2/MOVIES /media/16TB-HM/MOVIES
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
