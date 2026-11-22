import sqlite3
import paramiko

conn = sqlite3.connect('V2/pbn_matrix.db')
conn.execute('UPDATE servers SET password = ? WHERE host = ?', ('9W35Ewy1', '154.26.129.207'))
conn.commit()
conn.close()
print('Local DB updated for 154.26.129.207')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('103.106.105.77', username='root', password='q9icdLH1!*0B', timeout=10)
sftp = ssh.open_sftp()
sftp.put('V2/pbn_matrix.db', '/www/wwwroot/pbn-management2.keodinh.net/pbn_matrix.db')
sftp.close()
ssh.close()
print('Uploaded updated pbn_matrix.db to central server')
