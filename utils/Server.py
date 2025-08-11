import paramiko
import threading
import time
from . import utility

# This class represents a server that can be started, stopped, and configured via SSH
class Server:
    def __init__(self, server_name, ip_address, username, password, path, command, log_file, logger):
        self.name = server_name
        self.ip = ip_address
        self.username = username
        self.password = password
        self.path = path
        self.command = command
        self.log_file = log_file
        self.logger = logger

        self.client = None
        self.thread = None
        self.stop_flag = threading.Event()

    # Apply configuration to the server by uploading a config file via SFTP
    def apply_config(self, local_config_path, remote_config_path):
        if not local_config_path:
            self.logger.info(f"[{self.name}] No config file provided to apply")
            return
        try:
            self.logger.info(f"Updating {self.name} simulator config file")
            transport = paramiko.Transport((self.ip, 22))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(local_config_path, remote_config_path)
            sftp.close()
            transport.close()
            self.logger.info(f"{self.name} simulator config file updated successful")
        except Exception as e:
            self.logger.error(f"Failed to update {self.name} simulator config file: {e}", exc_info=True)

    # Start the server and run the command in a separate thread
    def start_server(self):
        self.client = utility.ssh_connect(self.ip, self.username, self.password)
        if self.client is None:
            self.logger.error(f"[{self.name}] Failed to establish SSH connection")
            return
        self.stop_flag.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    # Internal method to run the server command in a separate thread
    def _run(self):
        try:
            transport = self.client.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel.exec_command(f"cd {self.path} && {self.command}")

            with open(self.log_file, "w") as f:
                while not self.stop_flag.is_set():
                    if channel.recv_ready():
                        output = channel.recv(1024).decode('utf-8', errors='replace')
                        f.write(output)
                        f.flush()
                    time.sleep(0.2)

            channel.close()
        except Exception as e:
            self.logger.error(f"[{self.name}] Error in remote logging: {e}", exc_info=True)
        finally:
            self.logger.info(f"{self.name} simulator stopped successfully")

    # Stop the server and clean up resources
    def stop_server(self):
        self.logger.info(f"Stopping {self.name} simulator")
        self.stop_flag.set()

        if self.thread and self.thread.is_alive():
            self.thread.join()
            self.thread = None

        if self.client:
            self.client.close()
            self.client = None