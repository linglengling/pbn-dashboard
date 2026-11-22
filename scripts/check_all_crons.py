import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, glob

for f in sorted(glob.glob('/www/server/cron/*')):
    if f.endswith('.log') or f.endswith('.pl'):
        continue
    try:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            content = fp.read()
            # print non-standard lines
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith('#') and 'PATH' not in l and 'endDate' not in l and 'log_task' not in l and 'echo' not in l]
            print(f"CRON {os.path.basename(f)}:")
            for l in lines[:5]:
                print("  ", l)
    except:
        pass
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_crons.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_all_crons.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
ssh.close()

