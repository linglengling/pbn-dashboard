import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

cmd = """python3 -c "
import json, subprocess

with open('/tmp/site_configs.json') as f:
    configs = json.load(f)

for idx, c in enumerate(configs, 1):
    dom = c['domain']
    path = f'/www/wwwroot/{dom}'
    p = subprocess.run(['wp', 'menu', 'list', f'--path={path}', '--format=json', '--allow-root'], capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        menus = json.loads(p.stdout)
        print(f'{idx:02d}. {dom}:')
        for m in menus:
            print(f'     ID={m[\"term_id\"]} | name={m[\"name\"]} | locations={m.get(\"locations\", [])} | count={m.get(\"count\", 0)}')
    else:
        print(f'{idx:02d}. {dom}: ERROR listing menus ({p.stderr.strip()})')
"
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

