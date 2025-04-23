import csv
import requests
import urllib.parse
import webbrowser
import xml.etree.ElementTree as ET
import argparse

# Function to read Bluetooth CSV file
def read_bluetooth_csv(file_path):
    bluetooth_data = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bluetooth_data.append({
                'trilat': float(row['trilat']),
                'trilong': float(row['trilong']),
                'ssid': row['ssid'],
                'qos': int(row['qos']),
                'transid': row['transid'],
                'firsttime': row['firsttime'],
                'lasttime': row['lasttime'],
                'lastupdt': row['lastupdt'],
                'netid': row['netid'],
                'type': row['type'],
                'capabilities': row['capabilities'],
                'userfound': row['userfound'],
                'device': row['device'],
                'mfgrId': row['mfgrId'],
                'name': row['name'],
                'country': row['country'],
                'region': row['region'],
                'road': row['road'],
                'city': row['city'],
                'housenumber': row['housenumber'],
                'postalcode': row['postalcode']
            })
    return bluetooth_data

# Function to get Overpass Turbo link
def get_overpass_turbo_link(conflicting_node_ids):
    ids_query = "".join([f"node({node_id});" for node_id in conflicting_node_ids])
    query = f"""
    [out:json];
    (
      {ids_query}
    );
    out body;
    """
    encoded_query = urllib.parse.quote(query)
    return f"https://overpass-turbo.eu/?Q={encoded_query}&R"

# Function to get bounding box for nodes
def get_bounding_box_for_nodes(nodes):
    min_lat = 90
    max_lat = -90
    min_lon = 180
    max_lon = -180

    for node in nodes:
        min_lat = min(min_lat, node['trilat'])
        max_lat = max(max_lat, node['trilat'])
        min_lon = min(min_lon, node['trilong'])
        max_lon = max(max_lon, node['trilong'])

    return (min_lat, min_lon, max_lat, max_lon)

# Function to make Overpass API request
def overpass_request(query):
    url = "http://overpass-api.de/api/interpreter"
    try:
        response = requests.get(
            url, params={"data": query}, headers={"User-Agent": "DeFlock/1.0"}
        )
        response.raise_for_status()
        return response.json()["elements"]
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return []

# Function to get ALPR nodes in bounding box
def get_alprs_in_bounding_box(bbox):
    min_lat, min_lon, max_lat, max_lon = bbox
    query = f"""
    [out:json][bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
    node["man_made"="surveillance"]["surveillance:type"="ALPR"];
    out body;
    """
    return overpass_request(query)

# Function to detect duplicates based on radius
def detect_duplicates(nodes, radius):
    conflicting_node_ids = set()
    conflicting_imported_names = set()

    bbox = get_bounding_box_for_nodes(nodes)
    alprs = get_alprs_in_bounding_box(bbox)

    for node in nodes:
        for alpr in alprs:
            if (
                abs(node['trilat'] - alpr['lat']) < radius and
                abs(node['trilong'] - alpr['lon']) < radius
            ):
                conflicting_node_ids.add(alpr['id'])
                conflicting_imported_names.add(node['name'])

    print(f"\033[1m\033[91mFound {len(conflicting_imported_names)} conflicts with existing nodes in OSM.\033[0m")
    print(f"Detected as Duplicates:")
    for name in conflicting_imported_names:
        print(f"  - {name}")
    
    input("\033[1mPress Enter to view potential duplicates in OSM...\033[0m")
    webbrowser.open(get_overpass_turbo_link(conflicting_node_ids))

    return conflicting_node_ids, conflicting_imported_names

# Function to filter out duplicates based on detected conflicts
def filter_duplicates(bluetooth_data, conflicting_imported_names):
    filtered_data = []
    for entry in bluetooth_data:
        if entry['name'] not in conflicting_imported_names:
            filtered_data.append(entry)
    return filtered_data

# Function to save filtered data to a new CSV file
def save_filtered_data(filtered_data, output_file):
    fieldnames = [
        'trilat', 'trilong', 'ssid', 'qos', 'transid', 'firsttime', 'lasttime',
        'lastupdt', 'netid', 'type', 'capabilities', 'userfound', 'device',
        'mfgrId', 'name', 'country', 'region', 'road', 'city', 'housenumber', 'postalcode'
    ]
    with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in filtered_data:
            writer.writerow(entry)

# Main function
def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process Bluetooth data and filter out duplicates based on Overpass API.")
    parser.add_argument("bluetooth_file", type=str, help="Path to the Bluetooth CSV file")
    parser.add_argument("--radius", type=float, default=0.0001, help="Radius for duplicate detection in degrees (default: 0.0001)")
    parser.add_argument("--output", type=str, default='filtered_bluetooth_data.csv', help="Path to save the filtered data (default: filtered_bluetooth_data.csv)")
    args = parser.parse_args()

    bluetooth_file = args.bluetooth_file
    output_file = args.output  # Path to save the filtered data
    radius = args.radius  # Radius for duplicate detection

    # Read Bluetooth data
    bluetooth_data = read_bluetooth_csv(bluetooth_file)
    
    # Detect duplicates
    conflicting_node_ids, conflicting_imported_names = detect_duplicates(bluetooth_data, radius)
    
    # Filter out duplicates
    filtered_data = filter_duplicates(bluetooth_data, conflicting_imported_names)
    
    # Save filtered data
    save_filtered_data(filtered_data, output_file)

if __name__ == "__main__":
    main()