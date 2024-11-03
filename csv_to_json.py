import csv
import json

# Specify the file paths
csv_file_path = 'data/simulated_health_data_adjusted.csv'
json_file_path = 'data/health.json'

# Initialize an empty list to store the data
data = []

# Open the CSV file and read its contents
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        data.append(row)  # Add each row as a dictionary to the list

# Write the data to a JSON file
with open(json_file_path, mode='w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4)
