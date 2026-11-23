import paramiko
import sqlite3
import time

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    script = """
import os, sys, sqlite3, shutil

site_name = "team.kiencanh.com"
site_dir = f"/www/wwwroot/{site_name}"
ols_dir = "/www/server/panel/vhost/openlitespeed"
db_path = "/www/server/panel/data/default.db"

os.makedirs(site_dir, exist_ok=True)
os.system(f"chown -R www:www {site_dir}")

# 1. Update Database
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id FROM sites WHERE name=?", (site_name,))
row = cur.fetchone()
if not row:
    cur.execute('''
        INSERT INTO sites (name, path, status, [index], ps, addtime, type_id, edate, project_type, project_config, parent_id)
        VALUES (?, ?, '1', '', ?, datetime('now', 'localtime'), 0, '0000-00-00', 'PHP', '{}', 0)
    ''', (site_name, site_dir, "Mausbot Kiencanh"))
    site_id = cur.lastrowid
    cur.execute("INSERT INTO domain (pid, name, port, addtime) VALUES (?, ?, 80, datetime('now', 'localtime'))", (site_id, site_name))
    conn.commit()
    print(f"Added site {site_name} (ID {site_id}) to database.")
else:
    site_id = row[0]
    print(f"Site {site_name} already in database (ID {site_id}).")
conn.close()

# 2. OpenLiteSpeed VHost
vh_conf = f'''#VHOST {site_name} START
virtualhost {site_name} {{
vhRoot {site_dir}
configFile {ols_dir}/detail/{site_name}.conf
allowSymbolLink 1
enableScript 1
restrained 1
setUIDMode 0
}}
#VHOST {site_name} END
'''
with open(f"{ols_dir}/{site_name}.conf", "w") as f:
    f.write(vh_conf)

detail_conf = f'''docRoot                   $VH_ROOT
vhDomain                  $VH_NAME
adminEmails               example@example.com
enableGzip                1
enableIpGeo               1

index  {{
  useServer               0
  indexFiles index.html,index.php
}}

errorlog /www/wwwlogs/$VH_NAME_ols.error_log {{
  useServer               0
  logLevel                ERROR
  rollingSize             10M
}}

accesslog /www/wwwlogs/$VH_NAME_ols.access_log {{
  useServer               0
  logFormat               '%{{X-Forwarded-For}}i %h %l %u %t "%r" %>s %b "%{{Referer}}i" "%{{User-Agent}}i"'
  logHeaders              5
  rollingSize             10M
  keepDays                10  compressArchive         1
}}

rewrite  {{
  enable                  1
  autoLoadHtaccess        1
  include {ols_dir}/proxy/{site_name}/urlrewrite/*.conf
}}
include {ols_dir}/proxy/{site_name}/*.conf
'''
with open(f"{ols_dir}/detail/{site_name}.conf", "w") as f:
    f.write(detail_conf)

# 3. Proxy config
proxy_dir = f"{ols_dir}/proxy/{site_name}"
urlrewrite_dir = f"{proxy_dir}/urlrewrite"
os.makedirs(urlrewrite_dir, exist_ok=True)

proxy_conf = '''extprocessor proxy_mausbot {
  type                    proxy
  address                 http://127.0.0.1:8799/
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
'''
with open(f"{proxy_dir}/mausbot.conf", "w") as f:
    f.write(proxy_conf)

rewrite_conf = '''RewriteEngine On
RewriteCond %{HTTP:Upgrade} =websocket [NC]
RewriteRule ^/(.*)$ http://proxy_mausbot/$1 [P,E=Proxy-Host:$host]
RewriteRule ^/(.*)$ http://proxy_mausbot/$1 [P,E=Proxy-Host:$host]
'''
with open(f"{urlrewrite_dir}/mausbot.conf", "w") as f:
    f.write(rewrite_conf)

# 4. Listen 80 mapping
listen_80 = f"{ols_dir}/listen/80.conf"
if os.path.exists(listen_80):
    with open(listen_80, "r") as f:
        l80_content = f.read()
    if site_name not in l80_content:
        with open(listen_80, "a") as f:
            f.write(f"\\tmap\\t{site_name} {site_name}\\n")
        print(f"Added {site_name} to listen/80.conf")

# 5. Listen 443 mapping & SSL
cert_dir = f"/www/server/panel/vhost/cert/{site_name}"
source_cert_dir = "/www/server/panel/vhost/cert/kiencanh.com"
if not os.path.exists(cert_dir):
    os.makedirs(cert_dir, exist_ok=True)
    if os.path.exists(f"{source_cert_dir}/fullchain.pem"):
        shutil.copy(f"{source_cert_dir}/fullchain.pem", f"{cert_dir}/fullchain.pem")
        shutil.copy(f"{source_cert_dir}/privkey.pem", f"{cert_dir}/privkey.pem")
        print(f"Copied SSL cert from kiencanh.com to {cert_dir}")

listen_443 = f"{ols_dir}/listen/443.conf"
if os.path.exists(listen_443):
    with open(listen_443, "r") as f:
        l443_content = f.read()
    if site_name not in l443_content:
        ssl_block = f'''  map                     {site_name} {site_name}
  keyFile                 {cert_dir}/privkey.pem
  certFile                {cert_dir}/fullchain.pem
'''
        # Chèn trước dấu đóng ngoặc nhọn cuối cùng của listener 443
        idx = l443_content.rfind('}')
        if idx != -1:
            new_l443 = l443_content[:idx] + ssl_block + l443_content[idx:]
            with open(listen_443, "w") as f:
                f.write(new_l443)
            print(f"Added {site_name} SSL to listen/443.conf")

# 6. Reload OpenLiteSpeed
os.system("/usr/local/lsws/bin/lswsctrl reload")
print("OpenLiteSpeed reloaded.")
"""

    sftp = ssh.open_sftp()
    with sftp.open('/tmp/deploy_mausbot_vhost.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/deploy_mausbot_vhost.py")
    out = stdout.read().decode()
    err = stderr.read().decode()
    print("DEPLOY OUT:\n", out)
    if err:
        print("DEPLOY ERR:\n", err)

    time.sleep(2)

    # Test curl locally via OLS
    stdin, stdout, stderr = ssh.exec_command("curl -s -I -H 'Host: team.kiencanh.com' http://127.0.0.1:80/")
    print("TEST PORT 80 CURL:\n", stdout.read().decode())

    stdin, stdout, stderr = ssh.exec_command("curl -s -k -I -H 'Host: team.kiencanh.com' https://127.0.0.1:443/")
    print("TEST PORT 443 CURL:\n", stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    main()
