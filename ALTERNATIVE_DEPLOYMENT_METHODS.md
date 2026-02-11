# SmartShop - Alternative Deployment Methods (No SSH Required)

**Problem**: SSH command requires work account authentication which is unavailable.

**Solution**: Use Azure Portal Console or Kudu Console instead!

---

## ✅ METHOD 1: Azure Portal Console (RECOMMENDED - EASIEST)

This method works directly in your web browser with no authentication issues!

### Step-by-Step Instructions:

**1. Open Azure Portal**
   - Go to: https://portal.azure.com
   - Login with your Azure account (gary.chan@freecomchurch.org)

**2. Navigate to Your Web App**
   - Click: **All resources** or **Resource groups**
   - Click: **smartshop-rg**
   - Click: **smartshop-gas-3922** (your web app)

**3. Open the Console**
   - In the left sidebar, scroll down to **Development Tools**
   - Click: **Console**
   - A console window will open at the bottom of the screen

**4. Run Migration Commands**

Copy and paste these commands **ONE BY ONE** into the console:

```bash
cd /home/site/wwwroot
```

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py populate_categories
```

```bash
python manage.py collectstatic --noinput
```

```bash
python manage.py createsuperuser
```

**5. Create Superuser**

When prompted, enter:
- **Username**: `admin`
- **Email**: `admin@smartshop.com`
- **Password**: (Choose a strong password - you'll need this to login)
- **Password (again)**: (Repeat the same password)

**6. Restart Your App**

Back in PowerShell, run:
```powershell
az webapp restart --resource-group smartshop-rg --name smartshop-gas-3922
```

**7. Test Your Application**
- Open: https://smartshop-gas-3922.azurewebsites.net
- Login to admin: https://smartshop-gas-3922.azurewebsites.net/admin/

---

## ✅ METHOD 2: Kudu Advanced Console

If Azure Portal Console doesn't work, use Kudu:

**1. Open Kudu Console**
   - Direct URL: https://smartshop-gas-3922.scm.azurewebsites.net/DebugConsole
   - Login with your Azure credentials

**2. Navigate to Application Directory**
   - In the file browser at the top, click through: **site** > **wwwroot**
   - The console at the bottom will automatically be in this directory

**3. Run the Same Commands**

Use the same commands from Method 1:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py populate_categories
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

**4. Restart the app**
```powershell
az webapp restart --resource-group smartshop-rg --name smartshop-gas-3922
```

---

## ✅ METHOD 3: Azure Cloud Shell

**1. Open Cloud Shell**
   - Go to: https://shell.azure.com
   - Or click the Cloud Shell icon (>_) in Azure Portal top bar

**2. Run These Commands**

```bash
# Connect to your web app
az webapp ssh --resource-group smartshop-rg --name smartshop-gas-3922

# If that works, run migrations:
cd /home/site/wwwroot
python manage.py migrate
python manage.py populate_categories
python manage.py collectstatic --noinput
python manage.py createsuperuser
exit
```

---

## ✅ METHOD 4: Upload Migration Script via Portal

**1. Download run-migrations.sh**
   - The file is in your project folder: `C:\Users\gajc\OneDrive\Lithan\gas-smartshop\run-migrations.sh`

**2. Upload via Azure Portal**
   - In Azure Portal, go to your Web App
   - Development Tools > **Advanced Tools** > **Go**
   - This opens Kudu
   - Click **Debug console** > **CMD** or **PowerShell**
   - Navigate to: site > wwwroot
   - Drag and drop `run-migrations.sh` file to upload
   - In the console, run: `bash run-migrations.sh`

---

## 📝 QUICK REFERENCE - Commands to Run

```bash
# Navigate to app directory
cd /home/site/wwwroot

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create initial categories
python manage.py populate_categories

# Collect static files
python manage.py collectstatic --noinput

# Create admin user (interactive)
python manage.py createsuperuser
```

---

## 🎯 AFTER COMPLETING MIGRATIONS

**1. Restart the App**
```powershell
az webapp restart --resource-group smartshop-rg --name smartshop-gas-3922
```

**2. Test Your Application**
- Visit: https://smartshop-gas-3922.azurewebsites.net
- Should see the SmartShop homepage

**3. Login to Admin**
- Visit: https://smartshop-gas-3922.azurewebsites.net/admin/
- Login with the superuser credentials you created

**4. Add Products**
- In admin panel, go to Products
- Click "Add Product"
- Fill in details and add images

---

## ❌ TROUBLESHOOTING

### Console Not Working
- Try **SSH** instead of **Console** in the Development Tools menu
- Try **Advanced Tools** > **Go** to open Kudu
- Use Method 2 (Kudu) directly

### Commands Not Found
```bash
# Make sure you're in the right directory
pwd
cd /home/site/wwwroot
```

### Permission Denied
- The Azure Portal Console runs with the correct permissions automatically
- If using Kudu, make sure you're logged in

### Python Not Found
```bash
# Check Python location
which python
python --version

# If not found, try:
python3 manage.py migrate
```

### Migration Errors
```bash
# View detailed errors
python manage.py migrate --verbosity 2

# Check database connection
python manage.py check --database default
```

### Static Files Not Loading
```bash
# Re-run collectstatic
python manage.py collectstatic --noinput --clear
```

---

## 🔗 USEFUL LINKS

- **Azure Portal**: https://portal.azure.com
- **Your Web App**: https://smartshop-gas-3922.azurewebsites.net
- **Kudu Console**: https://smartshop-gas-3922.scm.azurewebsites.net/DebugConsole
- **Azure Cloud Shell**: https://shell.azure.com

---

## 💡 TIP: Automated Migrations (Future)

I've created an improved `startup.sh` script that automatically runs migrations when the app starts. To use it:

1. Upload the new `startup.sh` to your app (via Kudu file browser)
2. Restart the app
3. Migrations will run automatically on every app restart

The improved script:
- ✅ Runs migrations automatically
- ✅ Creates categories automatically
- ✅ Collects static files automatically
- ✅ Creates a default admin user (username: admin, password: SmartShop2026!)

---

**RECOMMENDATION**: Use **Method 1 (Azure Portal Console)** - it's the easiest and most reliable!
