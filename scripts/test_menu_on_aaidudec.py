import paramiko
import sys
import subprocess
import urllib.request
import ssl
import re

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

test_cmd = """
# 1. Add Brands parent item to menu 6
PARENT_ID=$(wp menu item add-custom 6 "Brands" "#" --porcelain --path=/www/wwwroot/aaidudec.org --allow-root)
echo "Added Brands parent ID: $PARENT_ID"

# 2. Add BU88 and VB88 child items
C1=$(wp menu item add-custom 6 "BU88" "https://bu88.com" --parent-id=$PARENT_ID --target=_blank --porcelain --path=/www/wwwroot/aaidudec.org --allow-root)
C2=$(wp menu item add-custom 6 "VB88" "https://vb88.com" --parent-id=$PARENT_ID --target=_blank --porcelain --path=/www/wwwroot/aaidudec.org --allow-root)
echo "Added BU88 ID: $C1, VB88 ID: $C2"

# 3. Purge cache for aaidudec.org and LSWS
rm -rf /www/wwwroot/aaidudec.org/wp-content/cache/*
rm -rf /usr/local/lsws/cachedata/priv/*
/usr/local/lsws/bin/lswsctrl restart
"""

stdin, stdout, stderr = ssh.exec_command(test_cmd)
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

