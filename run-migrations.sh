#!/bin/bash
# One-time migration script for SmartShop
# Run this in Azure Portal Console or Kudu Console

echo "========================================"
echo "SmartShop - Database Migration Script"
echo "========================================"

cd /home/site/wwwroot

echo "Step 1: Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "Step 2: Running database migrations..."
python manage.py migrate

echo "Step 3: Creating initial categories..."
python manage.py populate_categories

echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput

echo "Step 5: Creating superuser..."
echo "Please enter the following information:"
python manage.py createsuperuser

echo "========================================"
echo "Migration Complete!"
echo "========================================"
echo "You can now access your app at:"
echo "https://smartshop-gas-3922.azurewebsites.net"
echo ""
echo "Admin panel:"
echo "https://smartshop-gas-3922.azurewebsites.net/admin/"
