from google.cloud import bigquery
import pandas as pd
from config import PROJECT_ID, DATASET_ID,TABLE_ID

# Set your Google Cloud project ID

def upload_data(data):

    project_id = PROJECT_ID
    # Set your BigQuery dataset and table name
    dataset_id = DATASET_ID
    table_id = TABLE_ID

    # Create a BigQuery client
    client = bigquery.Client(project=project_id)

    # Example DataFrame
   

    # Define the table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # Upload the DataFrame to BigQuery
    job = client.load_table_from_dataframe(data, table_ref)
    job.result()  # Wait for the job to complete

    print("Upload complete!")
