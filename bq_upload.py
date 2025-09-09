from google.cloud import bigquery
import pandas as pd
from config import PROJECT_ID, DATASET_ID,TABLE_ID,GOOGLE_APPLICATION_CREDENTIALS
import os
# Set your Google Cloud project ID
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

def upload_data(data):

    project_id = PROJECT_ID
    # Set your BigQuery dataset and table name
    dataset_id = DATASET_ID
    table_id = TABLE_ID

    # Create a BigQuery client
    client = bigquery.Client(project=project_id)

    # Example DataFrame
   
    # Add created_ts column with the current UTC timestamp for this upload
    try:
        # Ensure we don't overwrite if the column already exists
        if "created_ts" not in data.columns:
            data["created_ts"] = pd.Timestamp.now(tz="UTC")
    except Exception:
        # As a fallback, attempt to assign even if data isn't a standard DataFrame
        data.loc[:, "created_ts"] = pd.Timestamp.now(tz="UTC")

    # Define the table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Upload the DataFrame to BigQuery
    job = client.load_table_from_dataframe(data, table_ref)
    job.result()  # Wait for the job to complete

    print("Upload complete!")
