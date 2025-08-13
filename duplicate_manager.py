#!/usr/bin/env python3
"""
Duplicate Manager

An interactive tool to process duplicate media files found by the media duplicate scanner.
Provides smart recommendations based on series distribution and file quality.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class DuplicateManager:
    """Interactive manager for processing duplicate media files."""
    
    def __init__(self, report_file: str):
        """Initialize the duplicate manager with a report file."""
        self.report_file = Path(report_file)
        self.report_data = None
        self.load_report()
    
    def load_report(self):
        """Load and validate the report file."""
        if not self.report_file.exists():
            print(f"Error: Report file not found: {self.report_file}")
            sys.exit(1)
        
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                self.report_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in report file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading report file: {e}")
            sys.exit(1)
        
        # Validate report structure
        required_keys = ['scan_timestamp', 'scan_stats', 'duplicates']
        if not all(key in self.report_data for key in required_keys):
            print("Error: Invalid report format - missing required fields")
            sys.exit(1)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def get_file_root(self, file_path: str) -> str:
        """Extract the media root directory from a file path."""
        path = Path(file_path)
        
        # Look for common media root patterns in the path
        path_str = str(path)
        
        # Check for movie roots
        if '/media/' in path_str or '\\media\\' in path_str:
            # Extract the media root (e.g., /media/4TB-WD2/MOVIES -> /media/4TB-WD2)
            parts = path.parts
            for i, part in enumerate(parts):
                if part in ['MOVIES', 'TV'] and i > 0:
                    # Return the parent directory of MOVIES/TV
                    return str(Path(*parts[:i]))
        
        # Fallback: return the first two parts of the path (e.g., /media/4TB-WD2)
        if len(path.parts) >= 2:
            return str(Path(*path.parts[:2]))
        elif len(path.parts) >= 1:
            return str(path.parts[0])
        else:
            return "unknown"
    
    def analyze_tv_series_distribution(self) -> Dict:
        """Analyze TV series distribution across roots."""
        series_analysis = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        # First pass: collect all TV files (not just duplicates)
        for episode_key, files in self.report_data['duplicates']['tv_series'].items():
            # Parse the episode key (e.g., "breaking bad S01E01")
            parts = episode_key.split()
            if len(parts) >= 2:
                # Find the season/episode part (e.g., "S01E01")
                season_episode = parts[-1]
                show_name = " ".join(parts[:-1])
                
                # Extract season number from "S01E01" format
                if 'S' in season_episode and 'E' in season_episode:
                    season_str = season_episode.split('S')[1].split('E')[0]
                    season = int(season_str)
                    
                    for file_info in files:
                        root = self.get_file_root(file_info['path'])
                        series_analysis[show_name][root][str(season)].append(episode_key)
        
        return series_analysis
    
    def display_series_overview(self, series_analysis: Dict):
        """Display overview of TV series distribution."""
        print("\n" + "="*80)
        print("TV SERIES DISTRIBUTION OVERVIEW")
        print("="*80)
        
        for show_name in sorted(series_analysis.keys()):
            print(f"\n📺 {show_name}")
            print("-" * 60)
            
            total_episodes = 0
            for root in sorted(series_analysis[show_name].keys()):
                root_episodes = 0
                print(f"  📁 {root}:")
                
                for season in sorted(series_analysis[show_name][root].keys(), key=int):
                    episodes = series_analysis[show_name][root][season]
                    episode_count = len(episodes)
                    root_episodes += episode_count
                    print(f"    Season {season}: {episode_count} episodes")
                
                total_episodes += root_episodes
                print(f"    Total: {root_episodes} episodes")
            
            print(f"  📊 Total episodes across all roots: {total_episodes}")
    
    def get_recommendation(self, files: List[Dict], series_analysis: Dict, show_name: str, season: int) -> Tuple[int, str]:
        """Get recommendation for which file to keep."""
        if len(files) != 2:  # Only handle pairs for now
            return 0, "No recommendation for more than 2 files"
        
        file1, file2 = files[0], files[1]
        root1, root2 = self.get_file_root(file1['path']), self.get_file_root(file2['path'])
        
        # Get episode counts for this season on each root
        season_episodes_root1 = len(series_analysis[show_name][root1].get(str(season), []))
        season_episodes_root2 = len(series_analysis[show_name][root2].get(str(season), []))
        
        # Get total episode counts for the series on each root
        total_episodes_root1 = sum(len(episodes) for episodes in series_analysis[show_name][root1].values())
        total_episodes_root2 = sum(len(episodes) for episodes in series_analysis[show_name][root2].values())
        
        # Determine preferred root based on episode counts
        preferred_root = None
        reason = ""
        
        if season_episodes_root1 > season_episodes_root2:
            preferred_root = root1
            reason = f"Root {root1} has more episodes in Season {season} ({season_episodes_root1} vs {season_episodes_root2})"
        elif season_episodes_root2 > season_episodes_root1:
            preferred_root = root2
            reason = f"Root {root2} has more episodes in Season {season} ({season_episodes_root2} vs {season_episodes_root1})"
        else:
            # Season counts are equal, check total series episodes
            if total_episodes_root1 > total_episodes_root2:
                preferred_root = root1
                reason = f"Root {root1} has more total episodes of {show_name} ({total_episodes_root1} vs {total_episodes_root2})"
            elif total_episodes_root2 > total_episodes_root1:
                preferred_root = root2
                reason = f"Root {root2} has more total episodes of {show_name} ({total_episodes_root2} vs {total_episodes_root1})"
            else:
                # All counts are equal, prefer larger file
                if file1['size'] > file2['size']:
                    preferred_root = root1
                    reason = f"File on {root1} is larger (higher quality)"
                else:
                    preferred_root = root2
                    reason = f"File on {root2} is larger (higher quality)"
        
        # Determine which file index corresponds to the preferred root
        recommended_index = 0 if self.get_file_root(files[0]['path']) == preferred_root else 1
        
        # Check for quality conflict
        quality_conflict = False
        if preferred_root == root1 and file2['size'] > file1['size']:
            quality_conflict = True
        elif preferred_root == root2 and file1['size'] > file2['size']:
            quality_conflict = True
        
        if quality_conflict:
            reason += " ⚠️  WARNING: Preferred file may be of lesser quality than the others"
        
        return recommended_index, reason
    
    def verify_files_exist(self, files: List[Dict]) -> bool:
        """Verify all files in a duplicate group still exist."""
        for file_info in files:
            if not Path(file_info['path']).exists():
                return False
        return True
    
    def process_tv_duplicates(self):
        """Process TV series duplicates with recommendations."""
        if not self.report_data['duplicates']['tv_series']:
            print("No TV series duplicates found.")
            return
        
        # Analyze series distribution
        series_analysis = self.analyze_tv_series_distribution()
        
        # Display overview
        self.display_series_overview(series_analysis)
        
        print("\n" + "="*80)
        print("PROCESSING TV DUPLICATES")
        print("="*80)
        
        # Group duplicates by show and sort by season/episode
        show_episodes = defaultdict(list)
        for episode_key, files in self.report_data['duplicates']['tv_series'].items():
            # Parse the episode key
            parts = episode_key.split()
            if len(parts) >= 2:
                season_episode = parts[-1]
                show_name = " ".join(parts[:-1])
                
                if 'S' in season_episode and 'E' in season_episode:
                    season_str = season_episode.split('S')[1].split('E')[0]
                    episode_str = season_episode.split('E')[1]
                    season = int(season_str)
                    episode = int(episode_str)
                    
                    show_episodes[show_name].append((season, episode, files, episode_key))
        
        # Sort episodes within each show
        for show in show_episodes:
            show_episodes[show].sort(key=lambda x: (x[0], x[1]))  # Sort by season, then episode
        
        # Process each show
        for show_name in sorted(show_episodes.keys()):
            print(f"\n🎬 Processing: {show_name}")
            print("-" * 60)
            
            for season, episode, files, episode_key in show_episodes[show_name]:
                # Verify files still exist
                if not self.verify_files_exist(files):
                    print(f"  ⚠️  Season {season} Episode {episode}: Files no longer exist, skipping...")
                    continue
                
                print(f"\n  📺 Season {season} Episode {episode}")
                print(f"  {'='*50}")
                
                # Get recommendation
                recommended_index, reason = self.get_recommendation(files, series_analysis, show_name, season)
                
                # Display files
                for i, file_info in enumerate(files):
                    size_str = self.format_file_size(file_info['size'])
                    marker = "⭐ RECOMMENDED" if i == recommended_index else "   "
                    print(f"  {marker}")
                    print(f"  {i+1}. {file_info['path']}")
                    print(f"     Size: {size_str}")
                    print(f"     Format: {file_info['extension']}")
                    print()
                
                # Show recommendation reason
                print(f"  💡 Recommendation: {reason}")
                print()
                
                # Get user choice
                while True:
                    try:
                        choice = input("  Choose file to KEEP (1-2), 's' to skip, or 'q' to quit: ").strip().lower()
                        
                        if choice == 'q':
                            print("Exiting...")
                            return
                        elif choice == 's':
                            print("  ⏭️  Skipping this duplicate...")
                            break
                        elif choice in ['1', '2']:
                            keep_index = int(choice) - 1
                            file_to_delete = files[1] if keep_index == 0 else files[0]
                            
                            # Confirm deletion
                            confirm = input(f"  🗑️  Delete: {file_to_delete['path']}? (y/N): ").strip().lower()
                            if confirm == 'y':
                                try:
                                    Path(file_to_delete['path']).unlink()
                                    print(f"  ✅ Deleted: {file_to_delete['path']}")
                                except Exception as e:
                                    print(f"  ❌ Error deleting file: {e}")
                            else:
                                print("  ⏭️  Deletion cancelled")
                            break
                        else:
                            print("  ❌ Invalid choice. Please enter 1, 2, 's', or 'q'")
                    except KeyboardInterrupt:
                        print("\nExiting...")
                        return
    
    def process_movie_duplicates(self):
        """Process movie duplicates."""
        if not self.report_data['duplicates']['movies']:
            print("No movie duplicates found.")
            return
        
        print("\n" + "="*80)
        print("PROCESSING MOVIE DUPLICATES")
        print("="*80)
        
        for movie_title, files in self.report_data['duplicates']['movies'].items():
            # Verify files still exist
            if not self.verify_files_exist(files):
                print(f"⚠️  {movie_title}: Files no longer exist, skipping...")
                continue
            
            print(f"\n🎬 {movie_title}")
            print(f"{'='*60}")
            
            # Sort files by size (largest first for quality preference)
            files_sorted = sorted(files, key=lambda x: x['size'], reverse=True)
            
            # Display files
            for i, file_info in enumerate(files_sorted):
                size_str = self.format_file_size(file_info['size'])
                marker = "⭐ HIGHEST QUALITY" if i == 0 else "   "
                print(f"  {marker}")
                print(f"  {i+1}. {file_info['path']}")
                print(f"     Size: {size_str}")
                print(f"     Format: {file_info['extension']}")
                print()
            
            # Get user choice
            while True:
                try:
                    choice = input(f"  Choose file to KEEP (1-{len(files)}), 's' to skip, or 'q' to quit: ").strip().lower()
                    
                    if choice == 'q':
                        print("Exiting...")
                        return
                    elif choice == 's':
                        print("  ⏭️  Skipping this duplicate...")
                        break
                    elif choice.isdigit() and 1 <= int(choice) <= len(files):
                        keep_index = int(choice) - 1
                        file_to_keep = files_sorted[keep_index]
                        
                        # Delete all other files
                        files_to_delete = [f for f in files_sorted if f != file_to_keep]
                        
                        print(f"  🗑️  Will delete {len(files_to_delete)} files:")
                        for file_info in files_to_delete:
                            print(f"     {file_info['path']}")
                        
                        confirm = input("  Confirm deletion? (y/N): ").strip().lower()
                        if confirm == 'y':
                            for file_info in files_to_delete:
                                try:
                                    Path(file_info['path']).unlink()
                                    print(f"  ✅ Deleted: {file_info['path']}")
                                except Exception as e:
                                    print(f"  ❌ Error deleting file: {e}")
                        else:
                            print("  ⏭️  Deletion cancelled")
                        break
                    else:
                        print(f"  ❌ Invalid choice. Please enter 1-{len(files)}, 's', or 'q'")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    return
    
    def run(self):
        """Run the duplicate manager."""
        print("🎬 MEDIA DUPLICATE MANAGER")
        print("="*50)
        print(f"Report: {self.report_file}")
        print(f"Scan completed: {self.report_data['scan_timestamp']}")
        print(f"Total duplicates: {self.report_data['scan_stats']['total_duplicates']}")
        
        # Process TV duplicates first (more complex logic)
        self.process_tv_duplicates()
        
        # Process movie duplicates
        self.process_movie_duplicates()
        
        print("\n✅ Duplicate processing completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Interactive duplicate media file manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python duplicate_manager.py duplicate_report_20241208_143022.json
  python duplicate_manager.py ./media-dup-reports/duplicate_report_*.json
        """
    )
    
    parser.add_argument(
        'report_file',
        help='Path to the duplicate report JSON file'
    )
    
    args = parser.parse_args()
    
    # Initialize and run the duplicate manager
    manager = DuplicateManager(args.report_file)
    manager.run()


if __name__ == '__main__':
    main()
