import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('site_configs.json', 'r') as f:
    configs = json.load(f)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', port=22, username='root', password='q9icdLH1!*0B', timeout=15)

# Upload sites.json and remote_check_indexing.py
sftp = ssh.open_sftp()
with sftp.file('/tmp/sites.json', 'w') as f:
    json.dump(configs, f)

sftp.put('scripts/remote_check_indexing.py', '/tmp/remote_check_indexing.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/www/server/panel/pyenv/bin/python3 /tmp/remote_check_indexing.py')
out = stdout.read().decode()
err = stderr.read().decode()

if err:
    print("Stderr:", err)

try:
    data = json.loads(out)
    print(f"{'#':2s} | {'Domain':25s} | {'blog_public':11s} | {'Meta Robots':20s} | {'Disallow /':10s} | {'Index Status':12s}")
    print("-" * 92)
    need_open = []
    for r in data:
        is_open = r['is_index_open']
        disallow = "YES" if r['live_robots_disallow'] else "no"
        meta = r['live_meta_robots'][:20]
        status_str = "OPEN (Indexed)" if is_open else "CLOSED (Blocked)"
        print(f"{r['idx']:2d} | {r['domain']:25s} | {str(r['blog_public']):11s} | {meta:20s} | {disallow:10s} | {status_str:12s}")
        if not is_open:
            need_open.append(r)
    
    print("\n" + "=" * 50)
    print(f"Tổng số site: {len(data)}")
    print(f"Đã mở index (OPEN): {len(data) - len(need_open)}")
    print(f"Chưa mở index (CLOSED / Noindex): {len(need_open)}")
    if need_open:
        print("\nCác site CHƯA mở index cần mở:")
        for s in need_open:
            reasons = []
            if s['blog_public'] == '0':
                reasons.append("blog_public=0")
            if 'noindex' in s['live_meta_robots'].lower():
                reasons.append(f"meta='{s['live_meta_robots']}'")
            if s['live_robots_disallow']:
                reasons.append("robots.txt Disallow: /")
            print(f"- #{s['idx']:2d} {s['domain']:25s} -> Lý do: {', '.join(reasons)}")
            
    # Save results to json for easy step 2
    with open('indexing_audit_result.json', 'w', encoding='utf-8') as jf:
        json.dump(data, jf, indent=2)

except Exception as e:
    print("Raw output:", out)
    print("Error:", e)

ssh.close()
