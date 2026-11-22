import os
import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8')

HOST = '103.106.105.77'
USER = 'root'
PASSWORD = 'q9icdLH1!*0B'
REMOTE_DIR = '/www/wwwroot/phn-manage.sites'
LOCAL_DIR = r'g:\ProjectDemo\manage-pbn-sites\PBN-Dashboard'

def print_step(msg):
    print(f"\n======================================================\n>> {msg}\n======================================================")

def upload_dir(sftp, local_path, remote_path, ignores=None):
    if ignores is None:
        ignores = ['node_modules', '.git', '.vite', '__pycache__', '.DS_Store']

    # Ensure remote directory exists
    try:
        sftp.stat(remote_path)
    except IOError:
        sftp.mkdir(remote_path)

    for item in os.listdir(local_path):
        if item in ignores:
            continue

        local_item = os.path.join(local_path, item)
        remote_item = f"{remote_path}/{item}"

        if os.path.isdir(local_item):
            upload_dir(sftp, local_item, remote_item, ignores)
        else:
            print(f"Uploading: {item}")
            sftp.put(local_item, remote_item)

def run_ssh_command(ssh, cmd):
    print(f"Exec: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line, end='')
    err = stderr.read().decode('utf-8', errors='ignore')
    if err:
        print(f"[STDERR] {err}")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        print(f"[WARNING] Command exited with status {status}")
    return status

def main():
    print_step("1. Kết nối tới VPS qua SSH & SFTP")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    sftp = ssh.open_sftp()
    print("SSH & SFTP kết nối thành công!")

    print_step("2. Upload source code PBN-Dashboard lên VPS")
    upload_dir(sftp, LOCAL_DIR, REMOTE_DIR)
    
    # Upload mu-plugins/pbn-manager.php
    local_plugin = r"g:\ProjectDemo\manage-pbn-sites\mu-plugins\pbn-manager.php"
    if os.path.exists(local_plugin):
        try:
            sftp.mkdir(f"{REMOTE_DIR}/mu-plugins")
        except:
            pass
        sftp.put(local_plugin, f"{REMOTE_DIR}/mu-plugins/pbn-manager.php")
        sftp.put(local_plugin, f"{REMOTE_DIR}/server/pbn-manager.php")
        print("Uploaded pbn-manager.php to mu-plugins and server directory!")
        
    print("Upload source code hoàn tất!")

    print_step("3. Cài đặt dependencies Backend và Frontend")
    run_ssh_command(ssh, "python3 -c 'import paramiko' 2>/dev/null || apt-get install -y python3-paramiko python3-requests")
    run_ssh_command(ssh, f"cd {REMOTE_DIR}/server && npm install --production=false")
    run_ssh_command(ssh, f"cd {REMOTE_DIR}/server && npm rebuild sqlite3 2>/dev/null || true")
    run_ssh_command(ssh, f"cd {REMOTE_DIR}/client && npm install && npm run build")

    print_step("4. Thiết lập OpenLiteSpeed Reverse Proxy cho phn-manage.sites (pbn.keodinh.net)")
    proxy_dir = "/www/server/panel/vhost/openlitespeed/proxy/phn-manage.sites"
    urlrewrite_dir = f"{proxy_dir}/urlrewrite"
    run_ssh_command(ssh, f"mkdir -p {urlrewrite_dir}")

    # Tạo extprocessor cho Node.js port 3000
    ext_conf = """extprocessor pbn_dashboard {
  type                    proxy
  address                 http://127.0.0.1:3000/
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
"""
    rewrite_conf = """RewriteRule ^/(.*)$ http://pbn_dashboard/$1 [P,E=Proxy-Host:$host]
"""
    with sftp.file(f"{proxy_dir}/pbn_dashboard.conf", "w") as f:
        f.write(ext_conf)
    with sftp.file(f"{urlrewrite_dir}/pbn_dashboard.conf", "w") as f:
        f.write(rewrite_conf)
    print("Đã tạo file cấu hình Reverse Proxy OpenLiteSpeed!")

    print_step("5. Khởi chạy / Restart PM2 Process")
    run_ssh_command(ssh, "which python || ln -sf /usr/bin/python3 /usr/bin/python")
    run_ssh_command(ssh, "pm2 delete pbn-dashboard 2>/dev/null || true")
    run_ssh_command(ssh, "fuser -k 3000/tcp 2>/dev/null || true")
    run_ssh_command(ssh, "fuser -k 9090/tcp 2>/dev/null || true")
    run_ssh_command(ssh, f"cd {REMOTE_DIR} && pm2 start server/index.js --name pbn-dashboard")
    run_ssh_command(ssh, "pm2 save")

    print_step("6. Khởi động lại OpenLiteSpeed")
    run_ssh_command(ssh, "/usr/local/lsws/bin/lswsctrl restart || /etc/init.d/lsws restart")

    print_step("7. Kiểm tra trạng thái dịch vụ trên VPS")
    run_ssh_command(ssh, "pm2 list")
    run_ssh_command(ssh, "curl -I http://127.0.0.1:3000/api/stats")
    run_ssh_command(ssh, "curl -I -k https://pbn.keodinh.net/api/stats")
    run_ssh_command(ssh, "curl -s -k https://pbn.keodinh.net/api/stats")

    sftp.close()
    ssh.close()
    print_step("HOÀN TẤT DEPLOYMENT THÀNH CÔNG!")

if __name__ == '__main__':
    main()
