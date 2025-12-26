import pandas as pd
import json
import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

# Configuration
INPUT_FILE = 'Dataset/Amazon Sale Report.csv'
OUTPUT_FILE = 'aggregated_sales.json'
CONTAINER_NAME = 'sales-data'
STORAGE_ACCOUNT_URL = os.getenv("AZURE_STORAGE_ACCOUNT_URL") # e.g., https://<account_name>.blob.core.windows.net

def load_and_clean_data(filepath):
    """Loads CSV and performs basic cleaning."""
    print(f"Loading data from {filepath}...")
    try:
        # Attempt to read with different encodings if default utf-8 fails, though csv usually works
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    # Drop rows where Amount is missing (assuming we only care about completed sales with value)
    # or fill with 0 depending on logic. Let's drop for accurate revenue.
    df = df.dropna(subset=['Amount'])
    
    # Convert Date to datetime
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df

def calculate_kpis(df):
    """Calculates KPIs from the dataframe."""
    print("Calculating KPIs...")
    
    total_revenue = float(df['Amount'].sum())
    total_orders = int(df['Order ID'].nunique())
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Top Region (State)
    if 'ship-state' in df.columns:
        top_state = df['ship-state'].mode()[0]
    else:
        top_state = "Unknown"

    # Sales by Category
    sales_by_category = df.groupby('Category')['Amount'].sum().to_dict()
    
    # Recent Trends (Last 5 days in dataset)
    # Assuming dataset is static, we take the latest dates in the file
    latest_date = df['Date'].max()
    start_date = latest_date - pd.Timedelta(days=30) # Last 30 days window
    recent_sales = df[df['Date'] > start_date]['Amount'].sum()

    kpis = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "average_order_value": avg_order_value,
        "top_region": top_state,
        "sales_by_category": sales_by_category,
        "recent_sales_30_days": float(recent_sales),
        "generated_at": pd.Timestamp.now().isoformat()
    }
    
    return kpis

def save_local(data, filename):
    """Saves data to a local JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Aggregated data saved locally to {filename}")

def upload_to_blob(filename, container_name, account_url):
    """Uploads the file to Azure Blob Storage."""
    if not account_url:
        print("Skipping Azure upload: AZURE_STORAGE_ACCOUNT_URL not set.")
        return

    print(f"Uploading {filename} to Azure Blob Storage...")
    try:
        # Use DefaultAzureCredential (supports CLI login, Environment vars, Managed Identity)
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
        
        # Create container if not exists
        try:
            container_client = blob_service_client.create_container(container_name)
        except Exception:
            container_client = blob_service_client.get_container_client(container_name)

        # Upload blob
        blob_client = container_client.get_blob_client(blob=filename)
        with open(filename, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print("Upload successful!")
        
    except Exception as e:
        print(f"Failed to upload to Azure: {e}")

def main():
    df = load_and_clean_data(INPUT_FILE)
    if df is not None:
        kpis = calculate_kpis(df)
        save_local(kpis, OUTPUT_FILE)
        upload_to_blob(OUTPUT_FILE, CONTAINER_NAME, STORAGE_ACCOUNT_URL)

if __name__ == "__main__":
    main()
