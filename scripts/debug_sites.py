import paramiko

VPS_HOST = "103.106.105.77"
VPS_PORT = 22
VPS_USER = "root"
VPS_PASS = "q9icdLH1!*0B"

remote_script_lines = [
    "import subprocess, json",
    "",
    "test_sites = [",
    "    ('bblatinamerica.com', 'wp_bblatinameric', 1696),",
    "    ('conadecivil.com', 'wp_conadecivil_c', 9),",
    "    ('facturatabasco.com', 'wp_facturatabasc', 65),",
    "    ('greatdrivingchallenge.com', 'wp_greatdrivingc', 20253),",
    "    ('snow-design.com', 'wp_snow-design_c', 9)",
    "]",
    "",
    "for domain, dbname, pid in test_sites:",
    "    print('=== DOMAIN:', domain, dbname, '===')",
    "    # Check tables",
    "    p = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', dbname, '-N', '-e', 'SHOW TABLES'], stdout=subprocess.PIPE, text=True)",
    "    tables = [t.strip() for t in p.stdout.split() if 'posts' in t or 'options' in t]",
    "    print('Tables:', tables)",
    "    posts_table = [t for t in tables if t.endswith('posts')][0] if any(t.endswith('posts') for t in tables) else 'wp_posts'",
    "    options_table = [t for t in tables if t.endswith('options')][0] if any(t.endswith('options') for t in tables) else 'wp_options'",
    "    ",
    "    # Options",
    "    p_opt = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', dbname, '-N', '-e', f\"SELECT option_name, option_value FROM {options_table} WHERE option_name IN ('show_on_front', 'page_on_front', 'siteurl')\"], stdout=subprocess.PIPE, text=True)",
    "    print('Options:\\n' + p_opt.stdout.strip())",
    "    ",
    "    # Posts around pid",
    "    p_post = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', dbname, '-N', '-e', f\"SELECT ID, post_type, post_status, LENGTH(post_content), post_title FROM {posts_table} WHERE ID={pid}\"], stdout=subprocess.PIPE, text=True)",
    "    print(f'Post {pid}:\\n' + p_post.stdout.strip())",
    "    ",
    "    # Check postmeta for elementor or others",
    "    postmeta_table = posts_table.replace('posts', 'postmeta')",
    "    p_meta = subprocess.run(['mysql', '-uroot', '-pdc2fe6f2608cdc00', dbname, '-N', '-e', f\"SELECT meta_key, LENGTH(meta_value) FROM {postmeta_table} WHERE post_id={pid} AND (meta_key LIKE '%elementor%' OR meta_key LIKE '%content%')\"], stdout=subprocess.PIPE, text=True)",
    "    print('Meta:\\n' + p_meta.stdout.strip())",
    "    print()",
]

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, port=VPS_PORT, username=VPS_USER, password=VPS_PASS, timeout=15)
    
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/debug_pbn_sites.py', 'w') as f:
        f.write("\n".join(remote_script_lines))
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('python3 /tmp/debug_pbn_sites.py')
    print(stdout.read().decode('utf-8'))
    print(stderr.read().decode('utf-8'))
    ssh.close()

if __name__ == "__main__":
    main()

