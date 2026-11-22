import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_code = '''
import os, subprocess

for site in ['fsc12.lo', 'fsc123.lo', 'vt2.com']:
    lp = f"/www/wwwroot/{site}/wp-content/plugins/learnpress"
    print(f"=== {site} ===")
    if os.path.exists(lp):
        # find cache in lp
        p = subprocess.run(f"find {lp} -name '*cache*'", shell=True, capture_output=True, text=True)
        print("cache files:", p.stdout.strip())
        # check header
        header = subprocess.run(f"head -n 10 {lp}/learnpress.php", shell=True, capture_output=True, text=True)
        for line in header.stdout.splitlines():
            if 'Version' in line:
                print("version:", line)
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_other_lp.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_other_lp.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()

