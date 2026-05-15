import json
import os

input_path = 'frontend/public/galaxy_points.json'
output_path = 'frontend/public/galaxy_points.json'

if os.path.exists(input_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Round coordinates to 6 decimal places
    for point in data:
        if 'x' in point: point['x'] = round(float(point['x']), 6)
        if 'y' in point: point['y'] = round(float(point['y']), 6)
        if 'z' in point: point['z'] = round(float(point['z']), 6)
    
    # Write back minified
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

    print(f"Compressed {input_path}")
    print(f"New size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
