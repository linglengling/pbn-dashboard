import paramiko
import sys
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

script = """
import urllib.request, re
req = urllib.request.Request('http://127.0.0.1/', headers={'Host': 'aaidudec.org', 'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
m = re.findall(r'<ul[^>]*id=\"primary-menu\"[^>]*>.*?</ul>', html, flags=re.S | re.I)
print('MATCH COUNT:', len(m))
for item in m:
    print('--- MATCH ---')
    print(item[:1000])
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_html.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('python3 /tmp/check_html.py')
print('STDOUT:\n', stdout.read().decode('utf-8', errors='ignore'))
print('STDERR:\n', stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
