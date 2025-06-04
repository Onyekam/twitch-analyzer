import json

# Load your array of JSON objects (from API or file)
with open("streams-2025-06-04 15:05:56.541689.csv") as f:
    data = json.load(f)  # This should be a list of dicts

# Write to NDJSON format
with open("streams_data.ndjson", "w") as f:
    for record in data:
        f.write(json.dumps(record) + "\n")