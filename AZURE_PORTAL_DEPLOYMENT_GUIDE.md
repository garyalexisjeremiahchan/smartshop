# SmartShop - Complete Azure Portal Deployment Guide

**Step-by-Step Instructions Using Azure Portal (No CLI Required)**

Follow these instructions to deploy SmartShop using only the Azure Portal web interface.

---

## PHASE 1: CREATE RESOURCE GROUP
### Step 1.1: Navigate to Resource Groups

1. Go to **https://portal.azure.com**
2. In the search bar at the top, type: **Resource groups**
3. Click on **Resource groups** in the results

### Step 1.2: Create Resource Group

1. Click **+ Create** button (top left)
2. Fill in the form:
   - **Subscription**: Select "Azure subscription 1"
   - **Resource group**: Type `smartshop-rg`
   - **Region**: Select **(US) East US**
3. Click **Review + create** button (bottom)
4. Click **Create** button
5. Wait for "Deployment complete" message
6. Click **Go to resource group**

✅ **Verify**: You should now see `smartshop-rg` in your resource groups list!

---

## PHASE 2: CREATE MYSQL DATABASE

### Step 2.1: Navigate to Create MySQL Database

1. In Azure Portal, search bar at top: **Azure Database for MySQL flexible servers**
2. Click **Azure Database for MySQL flexible servers**
3. Click **+ Create** button

### Step 2.2: Configure Basics Tab

Fill in the form:

**Project Details:**
- **Subscription**: Select "Azure subscription 1"
- **Resource group**: Select `smartshop-rg` (from dropdown)

**Server Details:**
- **Server name**: `smartshop-mysql-server` (must be globally unique - add numbers if needed, e.g., `smartshop-mysql-3922`)
- **Region**: **(US) East US**
- **MySQL version**: **8.0.21** (or latest 8.0)
- **Workload type**: Select **For development or hobby projects**

**Computer + Storage:**
- Click **Configure server**
- **Compute tier**: Select **Burstable**
- **Compute size**: Select **Standard_B1ms (1 vCore, 2 GiB memory)**
- **Storage size**: **32 GiB** (minimum)
- Click **Save**

**Authentication:**
- **Authentication method**: Select **MySQL authentication only**
- **Admin username**: `smartshopadmin`
- **Password**: Create a strong password (e.g., `SmartShop2026!@#`)
- **Confirm password**: (repeat the same password)

**📝 IMPORTANT**: Write down your password! You'll need it later.

Click **Next: Networking >** button (bottom)

### Step 2.3: Configure Networking Tab

**Connectivity method:**
- Select **Public access (allowed IP addresses)**

**Firewall rules:**
- Check the box: ☑ **Allow public access from any Azure service within Azure to this server**
- Click **+ Add 0.0.0.0 - 255.255.255.255** (for initial setup)

Click **Next: Security >** button

### Step 2.4: Configure Security Tab

- Leave defaults (disabled for cost savings)

Click **Next: Tags >** button

### Step 2.5: Tags Tab

- Skip this (click **Next: Review + create >**)

### Step 2.6: Review and Create

1. Review your settings
2. Click **Create** button
3. **⏰ Wait 5-10 minutes** for deployment to complete
4. You'll see "Your deployment is complete"
5. Click **Go to resource**

✅ **Verify**: MySQL server is created and you can see the overview page

### Step 2.7: Create Database

1. In your MySQL server page, click **Databases** (left menu)
2. Click **+ Add** button (top)
3. **Database name**: `smartshop_db`
4. **Charset**: `utf8mb4`
5. **Collation**: `utf8mb4_unicode_ci`
6. Click **Save**

✅ **Verify**: Database `smartshop_db` appears in the list

---

## PHASE 3: CREATE APP SERVICE

### Step 3.1: Navigate to Create App Service

1. In Azure Portal search bar: **App Services**
2. Click **App Services**
3. Click **+ Create** button

### Step 3.2: Configure Basics Tab

**Project Details:**
- **Subscription**: Select "Azure subscription 1"
- **Resource group**: Select `smartshop-rg`

**Instance Details:**
- **Name**: `smartshop-app` (add numbers if taken, e.g., `smartshop-app-2026`)
- **Publish**: Select **Code**
- **Runtime stack**: Select **Python 3.11**
- **Operating System**: Select **Linux**
- **Region**: **(US) East US**

**Pricing plans:**
- **Linux Plan (East US)**: Click **Create new**
  - Name: `smartshop-plan`
  - Click **OK**
- **Pricing plan**: Click **Explore pricing plans**
  - Select **Basic B1** tab
  - Click **Select** button

Click **Next: Database >** button

### Step 3.3: Database Tab

- **Skip this** - Click **Next: Deployment >**

### Step 3.4: Deployment Tab

**GitHub Actions settings:**
- **Continuous deployment**: Leave **Disable** selected

Click **Next: Networking >**

### Step 3.5: Networking Tab

- Leave defaults (Public access enabled)

Click **Next: Monitoring >**

### Step 3.6: Monitoring Tab

**Application Insights:**
- **Enable Application Insights**: Select **No** (to save costs)

Click **Next: Tags >**

### Step 3.7: Tags Tab

- Skip this (click **Next: Review + create >**)

### Step 3.8: Review and Create

1. Review your settings
2. Click **Create** button
3. Wait 1-2 minutes for deployment
4. Click **Go to resource**

✅ **Verify**: App Service is created, you see the overview page

---

## PHASE 4: CONFIGURE APP SERVICE

### Step 4.1: Configure App Settings (Environment Variables)

1. In your App Service page (smartshop-app), click **Configuration** (left menu under Settings)
2. Click **Application settings** tab
3. Click **+ New application setting** and add each of these:

**Add these settings one by one:**

| Name | Value |
|------|-------|
| `SECRET_KEY` | (Generate random: use https://djecrety.ir/) |
| `DEBUG` | `False` |
| `DB_NAME` | `smartshop_db` |
| `DB_USER` | `smartshopadmin` |
| `DB_PASSWORD` | (your MySQL password from Step 2.2) |
| `DB_HOST` | `<your-mysql-server-name>.mysql.database.azure.com` (must match the server name you created in Phase 2) |
| `DB_PORT` | `3306` |
| `ALLOWED_HOSTS` | `smartshop-app.azurewebsites.net` (or your actual app name) |
| `OPENAI_API_KEY` | (leave empty for now, or add your key) |
| `OPENAI_MODEL` | `gpt-4o-mini` |

**To add each setting:**
- Click **+ New application setting**
- Enter Name and Value
- Click **OK**
- Repeat for all settings above

4. Click **Save** button (top)
5. Click **Continue** when prompted

✅ **Verify**: All environment variables are saved

📝 **Important**: Your MySQL server name must be globally unique. If you created a server like `smartshop-mysql-3922`, then `DB_HOST` must be `smartshop-mysql-3922.mysql.database.azure.com`.

### Step 4.2: Configure Startup Command

1. Still in **Configuration** page
2. Click **General settings** tab
3. Scroll down to **Startup Command**
4. Enter: `bash startup.sh`
5. Click **Save** button (top)
6. Click **Continue** when prompted

### Step 4.3: Increase Container Startup Time Limit (Important)

If the container is doing a first-time dependency install, Azure may stop it with a message like:
**"site startup probe failed after ~230 seconds"**.

To prevent that:

1. Go to **Configuration** → **Application settings**
2. Click **+ New application setting**
3. Add:
   - **Name**: `WEBSITES_CONTAINER_START_TIME_LIMIT`
   - **Value**: `1800`
4. Click **OK**, then **Save**
5. Restart the App Service

📝 **Python version note:** If you accidentally created the App Service with Python 3.13, installs can be slower because some packages may not have wheels yet. Prefer **Python 3.11** (Configuration → General settings → Stack settings).

---

## PHASE 5: DEPLOY CODE

🛑 **Do not upload `.env` files to Azure**

- For Azure, store secrets in **App Service → Configuration → Application settings**.
- If you upload a `.env` file into `/home/site/wwwroot`, `python-decouple` may read it and you can accidentally point the app at the wrong database.

### Step 5.1: Install FileZilla (if needed)

Download FileZilla Client: https://filezilla-project.org/download.php?type=client

### Step 5.2: Get FTP Credentials

1. In your App Service (smartshop-app), click **Deployment Center** (left menu)
2. Click **FTPS credentials** tab
3. Under **Application scope**:
   - Copy **Username** (something like `smartshop-app\$smartshop-app`)
   - Copy **Password** (long string)
4. Also note the **FTPS endpoint** (something like `ftps://waws-prod-xxx.ftp.azurewebsites.windows.net`)

### Step 5.3: Connect with FileZilla

1. Open FileZilla
2. File > Site Manager
3. Click **New site**, name it "SmartShop Azure"
4. Fill in:
   - **Protocol**: FTPS - FTP over explicit TLS/SSL
   - **Host**: (your FTPS endpoint without ftps://)
   - **Port**: 21
   - **Logon Type**: Normal
   - **User**: (your username from Step 5.2)
   - **Password**: (your password from Step 5.2)
5. Click **Connect**
6. Accept certificate if prompted

### Step 5.4: Upload Files

1. In FileZilla:
   - **Left side**: Navigate to `C:\Users\gajc\OneDrive\Lithan\gas-smartshop`
   - **Right side**: Navigate to `/site/wwwroot`

2. **Delete everything** in `/site/wwwroot` folder first

3. **Select and upload these folders/files** from your local project:
   - `accounts/` folder
   - `assistant/` folder  
   - `media/` folder
   - `smartshop/` folder
   - `static/` folder
   - `store/` folder
   - `templates/` folder
   - `manage.py`
   - `requirements.txt`
   - `startup.sh`
   - `.deployment`

4. **Do NOT upload**:
   - `.venv/` folder
   - `antenv/` folder (Azure will build its own environment; uploading one from your PC often breaks)
   - `output.tar.gz` and `oryx-manifest.toml` (Oryx build artifacts; uploading stale ones can make Azure run old code)
   - `__pycache__/` folders
   - `.git/` folder
   - `*.pyc` files
   - `deploy.zip`

5. Wait for upload to complete (may take 5-10 minutes)

✅ **Verify**: Files are visible in `/site/wwwroot` on Azure

---

## ALTERNATIVE TO FILEZILLA: Use Kudu

If FileZilla doesn't work:

1. Go to your App Service
2. Click **Advanced Tools** (left menu under Development Tools)
3. Click **Go** button
4. In Kudu, click **Debug console** > **CMD**
5. Navigate through folders to: site > wwwroot
6. Drag and drop files directly into the browser window

---

## PHASE 6: RUN DATABASE MIGRATIONS

### Step 6.1: Open Console

1. In your App Service (smartshop-app)
2. Click **Console** (left menu under Development Tools)
3. Wait for console to load (you'll see a command prompt)

⚠️ **Note:** If your prompt looks like `kudu_ssh_user@...:/site/wwwroot$`, you are in the Kudu/SCM environment.
That environment may not include the App Service Python runtime (so `python`/`pip` may be missing and `/opt/python` may not exist).
If that happens, skip manual Step 6.2 and rely on `startup.sh` (it runs migrations automatically on app start), then restart the App Service and watch **Log stream**.

### Step 6.2: Run Migration Commands

Copy and paste these commands **ONE BY ONE** into the console:

```bash
cd /home/site/wwwroot
```

⚠️ **Important (pip error fix):** In App Service SSH/Console, use `python` (the App Service runtime) and avoid `python3`.
If you see `/usr/bin/python3: No module named pip`, you ran the system Python.

Optional quick check:

```bash
which python
python -V
python -m pip -V
```

If `python` is **not found** (common in the Kudu/SCM console prompt like `kudu_ssh_user@...`), use the app virtual environment interpreter instead:

```bash
./antenv/bin/python -V
./antenv/bin/python -m pip -V
```

If `python` is **not found** and `./antenv/bin/python` is missing/broken, you’re likely in Kudu/SCM without a usable Python runtime.

Options:
- Preferred: Restart the App Service and let `bash startup.sh` run migrations automatically (check **Log stream**).
- If you can use CLI: run `az webapp ssh ...` and execute the migration commands there.

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -r requirements.txt
```

Kudu/SCM fallback equivalents (if needed):

```bash
./antenv/bin/python -m pip install --upgrade pip
./antenv/bin/python -m pip install -r requirements.txt
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

When creating superuser:
- Username: `admin`
- Email: `admin@smartshop.com`
- Password: (choose a strong password)

✅ **Verify**: All commands complete without errors

---

## PHASE 7: RESTART & TEST

### Step 7.1: Restart App Service

1. In your App Service overview page
2. Click **Restart** button (top toolbar)
3. Click **Yes** to confirm
4. Wait 30-60 seconds

### Step 7.2: Test Your Application

1. Click **Browse** button (top toolbar)
   - OR visit: `https://smartshop-app.azurewebsites.net` (or your app name)

2. You should see the SmartShop homepage!

3. Test admin panel:
   - Visit: `https://smartshop-app.azurewebsites.net/admin/`
   - Login with your superuser credentials
   - Add some products

✅ **SUCCESS**: Your app is live!

---

## TROUBLESHOOTING

### App shows "Application Error"

1. Check logs:
   - App Service > **Log stream** (left menu)
   - Look for error messages

2. Check environment variables:
   - Configuration > Application settings
   - Verify DB_HOST, DB_USER, DB_PASSWORD are correct

3. Restart the app

### Database connection errors

1. Verify MySQL firewall:
   - MySQL server > **Networking** (left menu)
   - Ensure "Allow public access from any Azure service within Azure to this server" is checked
   - Or add a firewall rule for your App Service outbound IPs:
     - App Service → **Properties** → **Outbound IP addresses**
     - Add those IPs as firewall rules on the MySQL server

2. If your error is a **timeout** (not "access denied"), it usually means the MySQL server is not reachable:
   - MySQL server is set to **Private access** but the App Service is not using **VNet integration**
   - Or MySQL **public access** is disabled / firewall doesn’t allow the App Service IPs

3. Test connection string in Console:
   ```bash
   python manage.py check --database default
   ```

### Static files not loading

1. In Console, run:
   ```bash
   python manage.py collectstatic --noinput --clear
   ```

2. Restart app

### `/usr/bin/python3: No module named pip`

This happens when you run the system `python3` in the SSH/Console.

Use these instead:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `python -m pip` also fails, run:

```bash
python -m ensurepip --upgrade || true
python -m pip install --upgrade pip
```

### `./antenv/bin/python: error while loading shared libraries: libpython...`

This usually means `antenv/` was uploaded from another machine/Python version (e.g. Python 3.13) and can’t run on Azure.

Fix (run in **App Service SSH** / webssh, not the `.scm` Kudu console):

```bash
cd /home/site/wwwroot || cd /site/wwwroot
rm -rf antenv

# Use the App Service runtime Python (usually available as `python`)
python -V
python -m venv antenv

./antenv/bin/python -m pip install --upgrade pip
./antenv/bin/python -m pip install -r requirements.txt

./antenv/bin/python manage.py migrate
./antenv/bin/python manage.py collectstatic --noinput
```

### App keeps running old code / ignores updated `startup.sh`

If Log stream shows Oryx extracting `output.tar.gz` and reading `oryx-manifest.toml`, Azure may be running a previously-built artifact.

Fix (via Kudu):

1. App Service > **Advanced Tools** > **Go**
2. **Debug console** > **Bash**
3. Run:

```bash
cd /site/wwwroot
rm -f output.tar.gz oryx-manifest.toml
rm -rf antenv
```

4. Restart the App Service and re-check **Log stream**.

---

## COST SUMMARY

**Monthly costs (~$27/month):**
- App Service Basic B1: ~$13/month
- MySQL Flexible Server B1ms: ~$12/month
- Storage: ~$2/month

**To stop resources when not in use:**
1. App Service > Click **Stop** button
2. MySQL server > Click **Stop** button

---

## CHECKLIST

Use this checklist as you go through the steps:

- [ ] ✓ Resource Group created (`smartshop-rg`)
- [ ] ✓ MySQL Server created
- [ ] ✓ Database created (`smartshop_db`)
- [ ] ✓ App Service created
- [ ] ✓ Environment variables configured
- [ ] ✓ Startup command set
- [ ] ✓ Code uploaded via FTP/Kudu
- [ ] ✓ Migrations run successfully
- [ ] ✓ Superuser created
- [ ] ✓ App restarted
- [ ] ✓ Homepage loads correctly
- [ ] ✓ Admin panel accessible

---

## NEED HELP?

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Django on Azure**: https://docs.microsoft.com/azure/app-service/quickstart-python
- **Azure Portal**: https://portal.azure.com

---

**🎯 This portal-based approach is more reliable because you can see each step completing visually!**

**Estimated time**: 30-45 minutes total (including MySQL creation wait time)
