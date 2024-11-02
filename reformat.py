# pip install ics

from ics import Calendar
import pandas as pd

# Specify paths for input and output files
input_path = 'data/calendar.ics'  
output_path = 'data/calendar.json' 

# Load the .ics file
with open(input_path, 'r') as f:
    calendar_data = f.read()

# Parse the .ics data
calendar = Calendar(calendar_data)

# Extract event details into a list
events_list = []
for event in calendar.events:
    event_details = {
        'Name': event.name,
        'Start': event.begin.datetime,
        'End': event.end.datetime,
        'Location': event.location,
        'Description': event.description,
        'Duration': event.duration,
        # Use getattr to safely check for RRULE or any other extra attributes
        'Recurring': getattr(event, 'rrule', None)
    }
    events_list.append(event_details)

# Convert the list of events to a DataFrame
events_df = pd.DataFrame(events_list)

# Save the DataFrame as a JSON file
events_df.to_json(output_path, orient="records")

print(f"JSON file saved to {output_path}")
