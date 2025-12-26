#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="rg-sales-etl-demo"
LOCATION="eastus"
STORAGE_ACCOUNT_NAME="stsalesetl$RANDOM" # Random suffix for uniqueness
FUNCTION_APP_NAME="func-sales-etl-$RANDOM"
CONTAINER_NAME="sales-data"

echo "Starting deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"

# 1. Create Resource Group
echo "Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Create Storage Account
echo "Creating Storage Account ($STORAGE_ACCOUNT_NAME)..."
az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS

# Get Storage Account URL
STORAGE_ACCOUNT_URL=$(az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --query "primaryEndpoints.blob" --output tsv)
echo "Storage Account URL: $STORAGE_ACCOUNT_URL"

# 3. Create Blob Container
echo "Creating Blob Container ($CONTAINER_NAME)..."
az storage container create \
    --name $CONTAINER_NAME \
    --account-name $STORAGE_ACCOUNT_NAME \
    --auth-mode login

# 4. Create Function App
echo "Creating Function App ($FUNCTION_APP_NAME)..."
az functionapp create \
    --resource-group $RESOURCE_GROUP \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.10 \
    --functions-version 4 \
    --name $FUNCTION_APP_NAME \
    --os-type Linux \
    --storage-account $STORAGE_ACCOUNT_NAME

# 5. Configure App Settings
echo "Configuring App Settings..."
az functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings AZURE_STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true

# 6. Enable Managed Identity (System Assigned)
echo "Enabling Managed Identity..."
az functionapp identity assign --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP

# 7. Grant Storage Blob Data Contributor to the Function App
echo "Granting permissions..."
PRINCIPAL_ID=$(az functionapp identity show --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --query principalId --output tsv)
SUBSCRIPTION_ID=$(az account show --query id --output tsv)

az role assignment create \
    --assignee $PRINCIPAL_ID \
    --role "Storage Blob Data Contributor" \
    --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"

echo "Deployment infrastructure ready!"
echo "To deploy the code, run: func azure functionapp publish $FUNCTION_APP_NAME"
echo "Or zip and deploy via az CLI."

# Optional: Upload the local aggregated data if it exists
if [ -f "aggregated_sales.json" ]; then
    echo "Uploading initial data..."
    az storage blob upload \
        --account-name $STORAGE_ACCOUNT_NAME \
        --container-name $CONTAINER_NAME \
        --name aggregated_sales.json \
        --file aggregated_sales.json \
        --auth-mode login
fi

echo "Done! Function App URL: https://$FUNCTION_APP_NAME.azurewebsites.net"
