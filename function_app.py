import azure.functions as func
import logging
import json
import os
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp()

@app.route(route="sales_analytics", auth_level=func.AuthLevel.ANONYMOUS)
def sales_analytics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Sales Analytics API triggered.')

    # Configuration
    CONTAINER_NAME = 'sales-data'
    BLOB_NAME = 'aggregated_sales.json'
    # In Azure, this env var is usually set automatically or via App Settings
    STORAGE_ACCOUNT_URL = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")

    if not STORAGE_ACCOUNT_URL:
        return func.HttpResponse(
            json.dumps({"error": "AZURE_STORAGE_ACCOUNT_URL not configured"}),
            status_code=500,
            mimetype="application/json"
        )

    try:
        # Use Managed Identity in cloud, or CLI credential locally
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(BLOB_NAME)

        # Download blob content
        download_stream = blob_client.download_blob()
        blob_data = download_stream.readall()
        
        # Parse JSON to ensure it's valid before returning (optional, but good practice)
        sales_data = json.loads(blob_data)

        return func.HttpResponse(
            json.dumps(sales_data),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
