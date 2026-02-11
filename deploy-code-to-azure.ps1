# SmartShop - Code Deployment to Azure Script
# Run this after you've created Azure resources using deploy-to-azure.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          SmartShop - Deploy Code to Azure                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verify we're in the right directory
if (!(Test-Path "manage.py")) {
    Write-Host "❌ Error: manage.py not found. Please run this from the project root directory." -ForegroundColor Red
    exit 1
}

Write-Host "Preparing deployment..." -ForegroundColor Yellow

# Create .deployment file if it doesn't exist
if (!(Test-Path ".deployment")) {
    "[config]`nSCM_DO_BUILD_DURING_DEPLOYMENT=true" | Out-File -FilePath ".deployment" -Encoding UTF8
    Write-Host "✓ Created .deployment file" -ForegroundColor Green
}

# Create a .zip file excluding unnecessary files
Write-Host "`nCreating deployment package..." -ForegroundColor Yellow

# Files/folders to exclude
$excludeItems = @('.venv', 'venv', '__pycache__', '.git', '.env', '*.pyc', 'db.sqlite3', 
                  'deployment-info.txt', 'deploy.zip', '.vscode', '.idea', '*.log')

# Get all files
$files = Get-ChildItem -Recurse -File | Where-Object {
    $file = $_
    $shouldInclude = $true
    foreach ($exclude in $excludeItems) {
        if ($file.FullName -like "*$exclude*") {
            $shouldInclude = $false
            break
        }
    }
    $shouldInclude
}

# Create ZIP
Write-Host "Compressing files..." -ForegroundColor Yellow
$zipPath = "deploy.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Use System.IO.Compression for better control
Add-Type -Assembly System.IO.Compression.FileSystem
$compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
$zip = [System.IO.Compression.ZipFile]::Open($zipPath, 'Create')

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($PWD.Path.Length + 1)
    Write-Host "  Adding: $relativePath" -ForegroundColor Gray
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $file.FullName, $relativePath, $compressionLevel) | Out-Null
}

$zip.Dispose()
Write-Host "✓ Deployment package created: deploy.zip" -ForegroundColor Green

# Deploy to Azure
Write-Host "`nDeploying to Azure..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow

az webapp deployment source config-zip `
    --resource-group $ResourceGroup `
    --name $AppName `
    --src $zipPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Code deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Wait for deployment to complete
Write-Host "`nWaiting for deployment to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run post-deployment tasks
Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              Post-Deployment Configuration                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`nYou need to SSH into your app to complete the setup:" -ForegroundColor Yellow
Write-Host "`n1. Open SSH session:" -ForegroundColor White
Write-Host "   az webapp ssh --resource-group $ResourceGroup --name $AppName" -ForegroundColor Cyan

Write-Host "`n2. Once connected, run these commands:" -ForegroundColor White
Write-Host "   cd /home/site/wwwroot" -ForegroundColor Cyan
Write-Host "   pip install -r requirements.txt" -ForegroundColor Cyan
Write-Host "   python manage.py migrate" -ForegroundColor Cyan
Write-Host "   python manage.py populate_categories" -ForegroundColor Cyan
Write-Host "   python manage.py collectstatic --noinput" -ForegroundColor Cyan
Write-Host "   python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host "   exit" -ForegroundColor Cyan

Write-Host "`n3. Restart the app:" -ForegroundColor White
Write-Host "   az webapp restart --resource-group $ResourceGroup --name $AppName" -ForegroundColor Cyan

Write-Host "`nYour app will be available at:" -ForegroundColor White
Write-Host "https://$AppName.azurewebsites.net" -ForegroundColor Green

$openBrowser = Read-Host "`nOpen app in browser? (yes/no)"
if ($openBrowser -eq "yes") {
    az webapp browse --resource-group $ResourceGroup --name $AppName
}

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "Check logs with: az webapp log tail --resource-group $ResourceGroup --name $AppName" -ForegroundColor Yellow
