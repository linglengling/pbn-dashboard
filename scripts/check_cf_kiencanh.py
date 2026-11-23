import paramiko

def check_cf():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("103.106.105.77", username="root", password="q9icdLH1!*0B", timeout=20)
    
    script = """
import sqlite3, json, urllib.request

conn = sqlite3.connect('/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db')
c = conn.cursor()
c.execute("SELECT value FROM settings WHERE key='cf_accounts'")
row = c.fetchone()
if row:
    cf_data = json.loads(row[0])
    if isinstance(cf_data, dict):
        accounts = cf_data.values()
    else:
        accounts = cf_data
    for acc in accounts:
        email = acc.get("email")
        key = acc.get("key") or acc.get("api_key")
        print(f"Checking account {email}...")
        req = urllib.request.Request(
            "https://api.cloudflare.com/client/v4/zones?name=kiencanh.com",
            headers={
                "X-Auth-Email": email,
                "X-Auth-Key": key,
                "Content-Type": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                res = json.loads(r.read().decode())
                if res.get("success") and res.get("result"):
                    zone = res["result"][0]
                    print(f"FOUND kiencanh.com in CF account '{email}' (Zone ID: {zone['id']})!")
                    
                    # Check DNS record team.kiencanh.com
                    rec_req = urllib.request.Request(
                        f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/dns_records?name=team.kiencanh.com",
                        headers={
                            "X-Auth-Email": email,
                            "X-Auth-Key": key,
                            "Content-Type": "application/json"
                        }
                    )
                    with urllib.request.urlopen(rec_req, timeout=10) as rr:
                        recs = json.loads(rr.read().decode())
                        if recs.get("result"):
                            print("Record team.kiencanh.com already exists:", recs["result"][0]["content"])
                        else:
                            print("Record team.kiencanh.com does NOT exist yet. Creating...")
                            create_data = json.dumps({
                                "type": "A",
                                "name": "team.kiencanh.com",
                                "content": "103.106.105.77",
                                "ttl": 1,
                                "proxied": True
                            }).encode()
                            create_req = urllib.request.Request(
                                f"https://api.cloudflare.com/client/v4/zones/{zone['id']}/dns_records",
                                data=create_data,
                                headers={
                                    "X-Auth-Email": email,
                                    "X-Auth-Key": key,
                                    "Content-Type": "application/json"
                                },
                                method="POST"
                            )
                            with urllib.request.urlopen(create_req, timeout=10) as cr:
                                c_res = json.loads(cr.read().decode())
                                if c_res.get("success"):
                                    print("SUCCESS: Added DNS A record team.kiencanh.com -> 103.106.105.77 (Proxied)!")
                                else:
                                    print("Failed to add DNS:", c_res)
        except Exception as e:
            print(f"Error checking {email}: {e}")
"""
    sftp = ssh.open_sftp()
    with sftp.open('/tmp/check_cf_kiencanh.py', 'w') as f:
        f.write(script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("python3 /tmp/check_cf_kiencanh.py")
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()

if __name__ == "__main__":
    check_cf()
