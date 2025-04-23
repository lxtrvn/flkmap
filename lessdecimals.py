import csv
import requests
import xml.etree.ElementTree as ET

# Function to read Bluetooth CSV file
def read_bluetooth_csv(file_path):
    bluetooth_data = []
    with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bluetooth_data.append({
                'trilat': round(float(row['trilat']), 5),
                'trilong': round(float(row['trilong']), 5),
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

# Function to fetch and parse Overpass API response for ALPR nodes
def fetch_overpass_data(bbox):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:xml];
    node["man_made"="surveillance"]["surveillance:type"="ALPR"]({bbox});
    out;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    
    # Save the Overpass API response to a file
    with open('overpass_response.xml', 'wb') as xmlfile:
        xmlfile.write(response.content)
    
    root = ET.fromstring(response.content)
    overpass_nodes = []
    for node in root.findall('node'):
        lat = round(float(node.attrib['lat']), 5)
        lon = round(float(node.attrib['lon']), 5)
        overpass_nodes.append((lat, lon))
    return overpass_nodes

# Function to filter out duplicates
def filter_duplicates(bluetooth_data, overpass_nodes):
    filtered_data = []
    overpass_set = set(overpass_nodes)
    for entry in bluetooth_data:
        if (entry['trilat'], entry['trilong']) not in overpass_set:
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
    bluetooth_file = 'bluetooth2.csv'  # Path to your Bluetooth CSV file
    output_file = 'filtered_bluetooth_data.csv'  # Path to save the filtered data
    bbox = "25.44, -80.48, 46.45, -123.47"  # Example bounding box: lat_min-south, lon_min-west, lat_max-north, lon_max-east

    bluetooth_data = read_bluetooth_csv(bluetooth_file)
    overpass_nodes = fetch_overpass_data(bbox)
    filtered_data = filter_duplicates(bluetooth_data, overpass_nodes)
    save_filtered_data(filtered_data, output_file)

if __name__ == "__main__":
    main()