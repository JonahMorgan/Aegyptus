#!/usr/bin/env python3
"""
Download WikiHiero hieroglyph images from Wikimedia
"""
import os
import requests
import time
from pathlib import Path

# Create directory for hieroglyph images
HIERO_DIR = Path(__file__).parent / "hiero_images"
HIERO_DIR.mkdir(exist_ok=True)

# Base URL for WikiHiero images
BASE_URL = "https://upload.wikimedia.org/wikipedia/commons"

# All Gardiner codes we need to download
gardiner_codes = []

# A - Man and his Occupations (55 signs)
gardiner_codes.extend([f"A{i}" for i in range(1, 61)])

# B - Woman and her Occupations (7 signs)
gardiner_codes.extend([f"B{i}" for i in range(1, 21)])

# C - Anthropomorphic Deities (9 signs)
gardiner_codes.extend([f"C{i}" for i in range(1, 31)])

# D - Parts of the Human Body (63 signs)
gardiner_codes.extend([f"D{i}" for i in range(1, 71)])

# E - Mammals (34 signs)
gardiner_codes.extend([f"E{i}" for i in range(1, 41)])

# F - Parts of Mammals (52 signs)
gardiner_codes.extend([f"F{i}" for i in range(1, 61)])

# G - Birds (54 signs)
gardiner_codes.extend([f"G{i}" for i in range(1, 61)])

# H - Parts of Birds (8 signs)
gardiner_codes.extend([f"H{i}" for i in range(1, 11)])

# I - Amphibious Animals, Reptiles, etc. (15 signs)
gardiner_codes.extend([f"I{i}" for i in range(1, 21)])

# K - Fish and Parts of Fish (7 signs)
gardiner_codes.extend([f"K{i}" for i in range(1, 11)])

# L - Invertebrates and Lesser Animals (7 signs)
gardiner_codes.extend([f"L{i}" for i in range(1, 11)])

# M - Trees and Plants (44 signs)
gardiner_codes.extend([f"M{i}" for i in range(1, 51)])

# N - Sky, Earth, Water (42 signs)
gardiner_codes.extend([f"N{i}" for i in range(1, 51)])
gardiner_codes.append("N35A")

# O - Buildings, Parts of Buildings, etc. (51 signs)
gardiner_codes.extend([f"O{i}" for i in range(1, 61)])

# P - Ships and Parts of Ships (11 signs)
gardiner_codes.extend([f"P{i}" for i in range(1, 21)])

# Q - Domestics and Funerary Furniture (7 signs)
gardiner_codes.extend([f"Q{i}" for i in range(1, 11)])

# R - Temple Furniture and Sacred Emblems (25 signs)
gardiner_codes.extend([f"R{i}" for i in range(1, 31)])

# S - Crowns, Dress, Staves, etc. (45 signs)
gardiner_codes.extend([f"S{i}" for i in range(1, 51)])

# T - Warfare, Hunting, Butchery (35 signs)
gardiner_codes.extend([f"T{i}" for i in range(1, 41)])

# U - Agriculture, Crafts, and Professions (42 signs)
gardiner_codes.extend([f"U{i}" for i in range(1, 51)])

# V - Rope, Fiber, Baskets, Bags, etc. (38 signs)
gardiner_codes.extend([f"V{i}" for i in range(1, 41)])

# W - Vessels of Stone and Earthenware (25 signs)
gardiner_codes.extend([f"W{i}" for i in range(1, 31)])

# X - Loaves and Cakes (8 signs)
gardiner_codes.extend([f"X{i}" for i in range(1, 11)])

# Y - Writings, Games, Music (8 signs)
gardiner_codes.extend([f"Y{i}" for i in range(1, 11)])

# Z - Strokes, Signs derived from Hieratic, Geometrical Figures (11 signs)
gardiner_codes.extend([f"Z{i}" for i in range(1, 21)])

# Aa - Unclassified (31 signs)
gardiner_codes.extend([f"Aa{i}" for i in range(1, 51)])

print(f"Total codes to download: {len(gardiner_codes)}")

# The WikiHiero images follow a pattern
# https://upload.wikimedia.org/wikipedia/commons/thumb/X/XX/hiero_CODE.png/
# We need to find the actual hash path for each image

def download_hieroglyph(code):
    """Download a single hieroglyph image"""
    filename = f"hiero_{code}.png"
    output_path = HIERO_DIR / filename
    
    # Skip if already downloaded
    if output_path.exists():
        print(f"✓ {code} (cached)")
        return True
    
    # Try the direct extension path
    url = f"https://en.wikipedia.org/w/extensions/wikihiero/img/{filename}"
    
    # Headers to avoid 403 errors (matching wiktionary_get.py)
    headers = {
        "User-Agent": "EgyptianLemmasScraper/1.0 (user@email.com)",
        "Accept": "*/*",
        "Referer": "https://en.wikipedia.org/wiki/Help:WikiHiero_syntax"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ {code}")
            return True
        else:
            print(f"✗ {code} (status {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ {code} (error: {e})")
        return False

# Download all images
success_count = 0
fail_count = 0

for code in gardiner_codes:
    if download_hieroglyph(code):
        success_count += 1
    else:
        fail_count += 1
    
    # Be nice to the server
    time.sleep(0.1)

print(f"\nDownload complete!")
print(f"Success: {success_count}")
print(f"Failed: {fail_count}")
print(f"Images saved to: {HIERO_DIR}")
