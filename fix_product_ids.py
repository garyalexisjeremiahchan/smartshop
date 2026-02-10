#!/usr/bin/env python
# Quick script to replace 'product_id' with 'id' in tools.py

with open('assistant/tools.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the field name
content = content.replace("'product_id': product.id,", "'id': product.id,")

with open('assistant/tools.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced all instances of 'product_id': product.id, with 'id': product.id,")
