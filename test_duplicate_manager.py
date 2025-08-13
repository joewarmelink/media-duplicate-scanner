#!/usr/bin/env python3
"""
Test script for duplicate manager logic.
"""

import json
from collections import defaultdict
from pathlib import Path

# Sample report data for testing
sample_report = {
    "scan_timestamp": "2024-12-08T14:30:22",
    "scan_stats": {
        "total_duplicates": 5,
        "movie_duplicate_groups": 2,
        "tv_duplicate_groups": 3
    },
    "duplicates": {
        "movies": {
            "the matrix (1999)": [
                {
                    "path": "/media/4TB-WD2/MOVIES/The Matrix (1999) [BluRay]/matrix.mkv",
                    "size": 8589934592,  # 8 GB
                    "extension": ".mkv"
                },
                {
                    "path": "/media/16TB-HM/MOVIES/The Matrix (1999)/matrix.mp4", 
                    "size": 4294967296,  # 4 GB
                    "extension": ".mp4"
                }
            ]
        },
        "tv_series": {
            "breaking bad S01E01": [
                {
                    "path": "/media/4TB-WD2/TV/Breaking Bad/Season 01/breaking.bad.s01e01.mkv",
                    "size": 2147483648,  # 2 GB
                    "extension": ".mkv"
                },
                {
                    "path": "/media/16TB-HM/TV/Breaking Bad/Season 1/breaking.bad.s01e01.mp4",
                    "size": 1073741824,  # 1 GB
                    "extension": ".mp4"
                }
            ],
            "breaking bad S01E02": [
                {
                    "path": "/media/4TB-WD2/TV/Breaking Bad/Season 01/breaking.bad.s01e02.mkv",
                    "size": 2147483648,  # 2 GB
                    "extension": ".mkv"
                },
                {
                    "path": "/media/16TB-HM/TV/Breaking Bad/Season 1/breaking.bad.s01e02.mp4",
                    "size": 1073741824,  # 1 GB
                    "extension": ".mp4"
                }
            ]
        }
    }
}

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def get_file_root(file_path: str) -> str:
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
        return str(Path(*parts[:2]))
    elif len(path.parts) >= 1:
        return str(path.parts[0])
    else:
        return "unknown"

def analyze_tv_series_distribution(report_data: dict) -> dict:
    """Analyze TV series distribution across roots."""
    series_analysis = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for episode_key, files in report_data['duplicates']['tv_series'].items():
        # Parse the episode key (e.g., "breaking bad S01E01")
        # Extract show name and season from the key
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
                    root = get_file_root(file_info['path'])
                    series_analysis[show_name][root][str(season)].append(episode_key)
    
    return series_analysis

def get_recommendation(files: list, series_analysis: dict, show_name: str, season: int) -> tuple:
    """Get recommendation for which file to keep."""
    if len(files) != 2:
        return 0, "No recommendation for more than 2 files"
    
    file1, file2 = files[0], files[1]
    root1, root2 = get_file_root(file1['path']), get_file_root(file2['path'])
    
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
    recommended_index = 0 if get_file_root(files[0]['path']) == preferred_root else 1
    
    # Check for quality conflict
    quality_conflict = False
    if preferred_root == root1 and file2['size'] > file1['size']:
        quality_conflict = True
    elif preferred_root == root2 and file1['size'] > file2['size']:
        quality_conflict = True
    
    if quality_conflict:
        reason += " ⚠️  WARNING: Preferred file may be of lesser quality than the others"
    
    return recommended_index, reason

def test_series_analysis():
    """Test the series analysis logic."""
    print("Testing TV Series Analysis:")
    print("=" * 50)
    
    series_analysis = analyze_tv_series_distribution(sample_report)
    
    for show_name in series_analysis:
        print(f"\n📺 {show_name}")
        for root in series_analysis[show_name]:
            print(f"  📁 {root}:")
            for season in series_analysis[show_name][root]:
                episodes = series_analysis[show_name][root][season]
                print(f"    Season {season}: {len(episodes)} episodes")

def test_recommendations():
    """Test the recommendation logic."""
    print("\n\nTesting Recommendations:")
    print("=" * 50)
    
    series_analysis = analyze_tv_series_distribution(sample_report)
    
    for episode_key, files in sample_report['duplicates']['tv_series'].items():
        # Parse the episode key
        parts = episode_key.split()
        if len(parts) >= 2:
            season_episode = parts[-1]
            show_name = " ".join(parts[:-1])
            
            if 'S' in season_episode and 'E' in season_episode:
                season_str = season_episode.split('S')[1].split('E')[0]
                season = int(season_str)
                
                print(f"\n🎬 {show_name} Season {season} Episode {episode_key}")
                print("-" * 40)
                
                for i, file_info in enumerate(files):
                    size_str = format_file_size(file_info['size'])
                    print(f"  {i+1}. {file_info['path']}")
                    print(f"     Size: {size_str}")
                
                recommended_index, reason = get_recommendation(files, series_analysis, show_name, season)
                print(f"\n  💡 Recommendation: Keep file {recommended_index + 1}")
                print(f"  📝 Reason: {reason}")

def test_movie_processing():
    """Test movie duplicate processing."""
    print("\n\nTesting Movie Processing:")
    print("=" * 50)
    
    for movie_title, files in sample_report['duplicates']['movies'].items():
        print(f"\n🎬 {movie_title}")
        print("-" * 40)
        
        # Sort files by size (largest first for quality preference)
        files_sorted = sorted(files, key=lambda x: x['size'], reverse=True)
        
        for i, file_info in enumerate(files_sorted):
            size_str = format_file_size(file_info['size'])
            marker = "⭐ HIGHEST QUALITY" if i == 0 else "   "
            print(f"  {marker}")
            print(f"  {i+1}. {file_info['path']}")
            print(f"     Size: {size_str}")

if __name__ == '__main__':
    test_series_analysis()
    test_recommendations()
    test_movie_processing()
