import paramiko
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

# Wait for download to finish
print("Waiting for download process to complete...")
while True:
    stdin, stdout, stderr = ssh.exec_command('ps aux | grep [r]emote_download ; ls -lh /tmp/web_kqsx* 2>/dev/null')
    out = stdout.read().decode()
    if 'remote_download_kqsx.py' not in out:
        print("Download process completed!")
        print(out)
        break
    else:
        # print current size
        for line in out.splitlines():
            if 'web_kqsx' in line:
                print(f"Current download state: {line.strip()}")
        time.sleep(10)

# Check size
stdin, stdout, stderr = ssh.exec_command('ls -lh /tmp/web_kqsx*')
print("Downloaded archive:", stdout.read().decode())

# Step 2: Extract wp-optimize and wp-optimize-premium
print("\nExtracting wp-optimize plugins from archive...")
cmd = """
mkdir -p /tmp/kqsx_restore
tar -xzf /tmp/web_kqsxmientrung.com_20261031_003951_A0bIHr.tar.gz -C /tmp/kqsx_restore --wildcards 'kqsxmientrung.com/wp-content/plugins/wp-optimize*'
ls -la /tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/
ls -la /tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/cache/ 2>/dev/null
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("Tar stderr:", err)

# Step 3: Restore missing cache folders
print("\nRestoring missing cache folders...")
cmd_restore = """
# Copy cache folders specifically
if [ -d "/tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/cache" ]; then
    cp -rn /tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/cache /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/
    echo "Restored wp-optimize-premium/cache"
fi

if [ -d "/tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/wp-optimize/cache" ]; then
    cp -rn /tmp/kqsx_restore/kqsxmientrung.com/wp-content/plugins/wp-optimize/cache /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize/
    echo "Restored wp-optimize/cache"
fi

chown -R www:www /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize*
chmod -R 755 /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize*

# Verify files present
ls -la /www/wwwroot/kqsxmientrung.com/wp-content/plugins/wp-optimize-premium/cache/
"""
stdin, stdout, stderr = ssh.exec_command(cmd_restore)
print(stdout.read().decode())

# Step 4: Restart LSWS & test PHP
print("\nTesting PHP execution and web response...")
cmd_test = """
/usr/local/lsws/bin/lswsctrl restart
sleep 2

# Test PHP CLI on kqxs
cd /www/wwwroot/kqsxmientrung.com
php -r "require 'wp-load.php'; echo 'WP_LOAD_SUCCESS! Blog: ' . get_bloginfo('name') . PHP_EOL;" 2>&1

# Test HTTP via curl
curl -s -k -I -H "Host: kqxs24h.top" https://127.0.0.1/ | head -n 10
curl -s -k -I https://kqxs24h.top/ | head -n 10
"""
stdin, stdout, stderr = ssh.exec_command(cmd_test)
print(stdout.read().decode())

ssh.close()

