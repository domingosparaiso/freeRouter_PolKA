import paramiko
from datetime import datetime
print("* start")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("* connect")
ssh.connect("10.160.0.20", port=22222, username="rare", password="rare")
#"terminal length 100000\n"
#"show running-config\n"
#"exit\n"
commands = [ "terminal length 100000", "show running-config", "exit" ]
print("* exec")
stdin, stdout, stderr = ssh.exec_command("")
print("* while")
index = 0
timeout = True
start = datetime.now()
TIMEOUT_CMD = 1
out_text = ""
while not stdout.channel.exit_status_ready() and index < len(commands):
	if stdout.channel.recv_ready():
		print("* recv_ready")
		line = stdout.channel.recv(1024).decode("utf-8")
		out_text = out_text + line
	else:
		end = datetime.now()
		elapsed = (end - start).total_seconds()
		if elapsed > TIMEOUT_CMD:
			timeout = True
		if timeout:
			print("* send: " + commands[index])
			stdin.channel.send(commands[index] + "\n")
			timeout = False
			start = datetime.now()
			index = index + 1
print("* close")
ssh.close()
print("---------------------------------------------------------")
print(out_text)
print("---------------------------------------------------------")
del ssh, stdin, stdout, stderr