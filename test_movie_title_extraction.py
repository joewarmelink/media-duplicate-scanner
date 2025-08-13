#!/usr/bin/env python3
"""
Test script for movie title extraction logic.
"""

import re

def extract_movie_title_from_folder(folder_name: str) -> str:
    """Extract movie title from folder name, stopping at the year in parentheses."""
    # Pattern to match year in parentheses: (YYYY)
    year_pattern = r'\s*\(\d{4}\)'
    
    # Find the year pattern and extract everything before it
    match = re.search(year_pattern, folder_name)
    if match:
        # Extract everything before the year pattern
        title = folder_name[:match.start()].strip()
    else:
        # If no year found, use the entire folder name
        title = folder_name.strip()
    
    # Clean up the title: remove special characters but keep spaces
    # This preserves the original title structure while removing brackets, etc.
    cleaned_title = re.sub(r'[\[\]{}()]', '', title)  # Remove brackets and parentheses
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()  # Normalize whitespace
    
    return cleaned_title

def normalize_title(title: str) -> str:
    """Normalize title for case-insensitive comparison."""
    # Remove special characters and extra whitespace, convert to lowercase
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

# Test cases
test_cases = [
    "10 Cloverfield Lane (2016) [1080p]",
    "100 Girls (2000)",
    "The Oath (2018)",
    "The Matrix (1999) [BluRay]",
    "Inception (2010) 1080p",
    "Pulp Fiction (1994)",
    "The Shawshank Redemption (1994) [Extended]",
    "Fight Club (1999) [Director's Cut]",
    "Goodfellas (1990) [Remastered]",
    "The Godfather (1972) [4K]"
]

print("Testing movie title extraction:")
print("=" * 50)

for folder_name in test_cases:
    extracted_title = extract_movie_title_from_folder(folder_name)
    normalized_title = normalize_title(extracted_title)
    
    print(f"Folder: {folder_name}")
    print(f"Extracted: {extracted_title}")
    print(f"Normalized: {normalized_title}")
    print("-" * 30)
