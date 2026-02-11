# SmartShop - Azure Deployment Guide

## Prerequisites

Before starting, ensure you have:
- ✅ Active Azure subscription
- ✅ Azure CLI installed ([Download](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows))
- ✅ Git installed
- ✅ OpenAI API Key (for AI features)

---

## PHASE 1: Initial Setup & Configuration

### Step 1.1: Install Azure CLI

```powershell
# Download and install from: https://aka.ms/installazurecliwindows
# Or use winget:
winget install -e --id Microsoft.AzureCLI
```

### Step 1.2: Login to Azure

```powershell
az login
```

This will open your browser for authentication.

### Step 1.3: Set Your Subscription (if you have multiple)

```powershell
# List available subscriptions
az account list --output table

# Set the subscription you want to use
az account set --subscription "YOUR_SUBSCRIPTION_NAME_OR_ID"
```

---

## PHASE 2: Create Azure Resources

### Step 2.1: Define Variables

```powershell
# Set these variables according to your preferences
$RESOURCE_GROUP = "smartshop-rg"
$LOCATION = "eastus"  # or your preferred region
$APP_NAME = "smartshop-app-$(Get-Random -Maximum 9999)"  # Must be globally unique
$DB_SERVER_NAME = "smartshop-mysql-$(Get-Random -Maximum 9999)"  # Must be globally unique
$DB_NAME = "smartshop_db"
$DB_ADMIN_USER = "smartshopadmin"
$DB_ADMIN_PASSWORD = "SmartShop@2026$(Get-Random -Maximum 999)"  # Change this!
$STORAGE_ACCOUNT = "smartshopstorage$(Get-Random -Maximum 999999)"
$APP_SERVICE_PLAN = "smartshop-plan"

# Display the values
Write-Host "Resource Group: $RESOURCE_GROUP"
Write-Host "Location: $LOCATION"
Write-Host "App Name: $APP_NAME"
Write-Host "Database Server: $DB_SERVER_NAME"
Write-Host "Database Name: $DB_NAME"
Write-Host "Database Admin User: $DB_ADMIN_USER"
Write-Host "Database Admin Password: $DB_ADMIN_PASSWORD"
Write-Host "Storage Account: $STORAGE_ACCOUNT"
Write-Host "App Service Plan: $APP_SERVICE_PLAN"

# IMPORTANT: Save these values! You'll need them later.
```

### Step 2.2: Create Resource Group

```powershell
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 2.3: Create MySQL Flexible Server

```powershell
# Create MySQL server (this takes 5-10 minutes)
az mysql flexible-server create `
  --resource-group $RESOURCE_GROUP `
  --name $DB_SERVER_NAME `
  --location $LOCATION `
  --admin-user $DB_ADMIN_USER `
  --admin-password $DB_ADMIN_PASSWORD `
  --sku-name Standard_B1ms `
  --tier Burstable `
  --storage-size 32 `
  --version 8.0.21 `
  --public-access 0.0.0.0-255.255.255.255

# Create database
az mysql flexible-server db create `
  --resource-group $RESOURCE_GROUP `
  --server-name $DB_SERVER_NAME `
  --database-name $DB_NAME
```

### Step 2.4: Create App Service Plan

```powershell
az appservice plan create `
  --name $APP_SERVICE_PLAN `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --is-linux `
  --sku B1
```

### Step 2.5: Create Web App

```powershell
az webapp create `
  --resource-group $RESOURCE_GROUP `
  --plan $APP_SERVICE_PLAN `
  --name $APP_NAME `
  --runtime "PYTHON:3.11"
```

### Step 2.6: Create Storage Account (for static/media files)

```powershell
# Create storage account
az storage account create `
  --name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku Standard_LRS

# Get storage account key
$STORAGE_KEY = az storage account keys list `
  --resource-group $RESOURCE_GROUP `
  --account-name $STORAGE_ACCOUNT `
  --query "[0].value" `
  --output tsv

# Create containers for static and media files
az storage container create `
  --name static `
  --account-name $STORAGE_ACCOUNT `
  --account-key $STORAGE_KEY `
  --public-access blob

az storage container create `
  --name media `
  --account-name $STORAGE_ACCOUNT `
  --account-key $STORAGE_KEY `
  --public-access blob
```

---

## PHASE 3: Configure Application Settings

### Step 3.1: Configure Database Connection

```powershell
# Build database connection string
$DB_HOST = "$DB_SERVER_NAME.mysql.database.azure.com"

# Set environment variables in App Service
az webapp config appsettings set `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --settings `
    SECRET_KEY="$(New-Guid)-$(New-Guid)" `
    DEBUG="False" `
    DB_NAME="$DB_NAME" `
    DB_USER="$DB_ADMIN_USER" `
    DB_PASSWORD="$DB_ADMIN_PASSWORD" `
    DB_HOST="$DB_HOST" `
    DB_PORT="3306" `
    OPENAI_API_KEY="your-openai-api-key-here" `
    OPENAI_MODEL="gpt-4o-mini" `
    AZURE_STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT" `
    AZURE_STORAGE_ACCOUNT_KEY="$STORAGE_KEY" `
    ALLOWED_HOSTS="$APP_NAME.azurewebsites.net"
```

### Step 3.2: Configure Startup Command

```powershell
az webapp config set `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --startup-file "startup.sh"
```

---

## PHASE 4: Deploy Application

### Step 4.1: Configure Deployment

```powershell
# Enable local Git deployment
az webapp deployment source config-local-git `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME

# Get deployment credentials
az webapp deployment list-publishing-credentials `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --query "{username:publishingUserName, password:publishingPassword}" `
  --output table
```

### Step 4.2: Deploy via Git

```powershell
# Navigate to your project directory
cd C:\Users\gajc\OneDrive\Lithan\gas-smartshop

# Initialize git (if not already)
git init

# Add Azure as remote
$DEPLOY_URL = az webapp deployment source config-local-git `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --query url `
  --output tsv

git remote add azure $DEPLOY_URL

# Commit all changes
git add .
git commit -m "Initial Azure deployment"

# Push to Azure (you'll be prompted for credentials)
git push azure master
```

### Alternative: Deploy via ZIP

```powershell
# Create deployment package (excluding unnecessary files)
$exclude = @('.venv', '__pycache__', '*.pyc', '.env', 'db.sqlite3', '.git')
Compress-Archive -Path * -DestinationPath deploy.zip -Force

# Deploy the ZIP file
az webapp deployment source config-zip `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --src deploy.zip
```

---

## PHASE 5: Post-Deployment Configuration

### Step 5.1: Run Database Migrations

```powershell
# SSH into the web app
az webapp ssh --resource-group $RESOURCE_GROUP --name $APP_NAME

# Once connected, run:
# cd /home/site/wwwroot
# python manage.py migrate
# python manage.py populate_categories
# python manage.py createsuperuser
# exit
```

### Step 5.2: Configure Custom Domain (Optional)

```powershell
# Add your custom domain
az webapp config hostname add `
  --resource-group $RESOURCE_GROUP `
  --webapp-name $APP_NAME `
  --hostname "www.yourdomain.com"

# Enable HTTPS
az webapp update `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --https-only true
```

### Step 5.3: Enable Application Insights (Monitoring)

```powershell
# Create Application Insights
az monitor app-insights component create `
  --app smartshop-insights `
  --location $LOCATION `
  --resource-group $RESOURCE_GROUP `
  --application-type web

# Get instrumentation key
$INSIGHTS_KEY = az monitor app-insights component show `
  --app smartshop-insights `
  --resource-group $RESOURCE_GROUP `
  --query instrumentationKey `
  --output tsv

# Configure App Service to use it
az webapp config appsettings set `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME `
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$INSIGHTS_KEY"
```

---

## PHASE 6: Verification & Testing

### Step 6.1: Check Application Logs

```powershell
# Stream logs
az webapp log tail `
  --resource-group $RESOURCE_GROUP `
  --name $APP_NAME
```

### Step 6.2: Open Your Application

```powershell
# Open in browser
az webapp browse --resource-group $RESOURCE_GROUP --name $APP_NAME
```

### Step 6.3: Verify Database Connection

Visit: `https://$APP_NAME.azurewebsites.net/admin/`

---

## Troubleshooting

### View Logs
```powershell
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME
```

### Restart App
```powershell
az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME
```

### Check Configuration
```powershell
az webapp config appsettings list --resource-group $RESOURCE_GROUP --name $APP_NAME
```

### SSH into App
```powershell
az webapp ssh --resource-group $RESOURCE_GROUP --name $APP_NAME
```

---

## Cost Optimization

### Stop Resources When Not Needed
```powershell
# Stop web app
az webapp stop --resource-group $RESOURCE_GROUP --name $APP_NAME

# Stop database server
az mysql flexible-server stop --resource-group $RESOURCE_GROUP --name $DB_SERVER_NAME
```

### Delete Resources
```powershell
# Delete entire resource group (CAUTION: This deletes everything!)
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

---

## Security Checklist

- [ ] Change default admin password
- [ ] Set DEBUG=False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure database firewall rules
- [ ] Enable HTTPS only
- [ ] Set up application insights for monitoring
- [ ] Configure backup for database
- [ ] Implement rate limiting
- [ ] Review ALLOWED_HOSTS setting

---

## Next Steps

1. Add products via admin panel
2. Test checkout process
3. Configure email settings
4. Set up continuous deployment
5. Configure domain and SSL
6. Set up automated backups
7. Monitor application performance

---

## Useful Commands

```powershell
# View all resources in resource group
az resource list --resource-group $RESOURCE_GROUP --output table

# Get web app URL
az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query defaultHostName --output tsv

# Scale up/down
az appservice plan update --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B2

# Enable/disable debug mode
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings DEBUG="True"
```

---

## Support Resources

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Django on Azure**: https://docs.microsoft.com/azure/app-service/quickstart-python
- **Azure MySQL**: https://docs.microsoft.com/azure/mysql/flexible-server/
- **Azure CLI Reference**: https://docs.microsoft.com/cli/azure/

---

**Estimated Monthly Cost (B1 tier):**
- App Service Plan (B1): ~$13/month
- MySQL Flexible Server (Burstable B1ms): ~$12/month  
- Storage Account: ~$2/month
- **Total**: ~$27/month

*Note: Prices are approximate and may vary by region*
