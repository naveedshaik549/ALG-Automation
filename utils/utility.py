import os
import time
import csv
import json
import ssl
import ast
import re
import textwrap
import logging
import paramiko
import tempfile
import http.client
from datetime import datetime
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from tabulate import tabulate
import configparser
from .html_report_generator import create_html_handler
from .Server import Server
from .html_report_generator import start_testcase, end_testcase

config = configparser.ConfigParser()
config_dir = os.path.join(os.path.dirname(__file__), "..", "Config")
config_path = os.path.join(config_dir, 'config.ini')
config.read(os.path.abspath(config_path))
api_json_path = os.path.join(config_dir, config['AUTOMATION_VARS']['API_FILE'])
expected_values_path = os.path.join(config_dir, config['AUTOMATION_VARS']['EXPECTED_API_FILE'])

# This function creates a directory for reports
def create_run_folder(base_dir="reports"):
    timestamp = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir

# This function creates a directory inside reports based on the current timestamp
# It returns the directory path and the timestamp string
def get_timestamped_report_dir(base_dir="reports"):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    report_dir = os.path.join(base_dir, f"report-{timestamp}")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir, timestamp


# This function creates a folder for a specific test case within the run directory
def create_testcase_folder(run_dir, testcase_id):
    testcase_dir = os.path.join(run_dir, testcase_id)
    os.makedirs(testcase_dir, exist_ok=True)
    return testcase_dir


def get_elapsed_time(start_time, end_time):
    fmt = "%Y-%m-%d %H:%M:%S,%f"

    # Convert only if they are strings
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, fmt)
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, fmt)

    elapsed = end_time - start_time
    seconds = elapsed.total_seconds()

    if seconds >= 60:
        minutes = int(seconds // 60)
        seconds = round(seconds % 60, 1)
        return f"{minutes}m {seconds}s"
    else:
        return f"{round(seconds, 1)}s"


# This function initializes the logger and sets up file and console handlers
def get_logger(report_dir, timestamp=None):
    log_file = os.path.join(report_dir, "Automation.log")
    json_log_file = os.path.join(report_dir, "Automation.json")

    html_file = os.path.join(report_dir, "Automation.html")
    logger = logging.getLogger("AutomationLogger")
    log_level_str = config['AUTOMATION_VARS']['LOG_LEVEL'].upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%b-%d-%y %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # JSON file handler
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "funcName": record.funcName,
                "lineNo": record.lineno
            }
            return json.dumps(log_record)

    json_handler = logging.FileHandler(json_log_file)
    json_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_handler)

    # HTML handler using the new HTML report generator
    html_handler = create_html_handler(html_file)
    html_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(html_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%b-%d-%y %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger, log_file


# This function establishes an SSH connection to a remote server
def ssh_connect(ip_address, username, password, port=22):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip_address, port=port, username=username, password=password, allow_agent=False, look_for_keys=False)
        logger.debug(f"SSH connection successful - {ip_address} - with username - {username}")
        return client
    except Exception as e:
        logger.error(f"SSH connection failed: {e}", exc_info=True)
        return None
    

# This function starts the NE server in a background thread using SSH    
def start_NE(testcase_id, report_dir, config_file, log_file=None):
    if log_file is None:
        log_file = os.path.join(report_dir, testcase_id, "NE_server.log")
    
    ne_server = Server(
        server_name="NE",
        ip_address=config['NE']['IP_ADDRESS'],
        username=config['NE']['USERNAME'],
        password=config['NE']['PASSWORD'],
        path=config['NE']['START_PATH'],
        command=config['NE']['START_COMMAND'],
        log_file=log_file,
        logger=logger
    )
    ne_server.apply_config(local_config_path=config_file, remote_config_path=f"{config['NE']['START_PATH']}/config.yaml")
    logger.info(f"Starting NE simulator")
    ne_server.start_server()
    logger.info(f"NE simulator started successfully")
    return ne_server


# This function starts the NEM server in a background thread using SSH
def start_NEM(testcase_id, report_dir, config_file, log_file=None):
    if log_file is None:
        log_file = os.path.join(report_dir, testcase_id, "NEM_server.log")
    
    nem_server = Server(
        server_name="NEM",
        ip_address=config['NEM']['IP_ADDRESS'],
        username=config['NEM']['USERNAME'],
        password=config['NEM']['PASSWORD'],
        path=config['NEM']['START_PATH'],
        command=config['NEM']['START_COMMAND'],
        log_file=log_file,
        logger=logger
    )
    nem_server.apply_config(local_config_path=config_file, remote_config_path=f"{config['NEM']['START_PATH']}/config.yaml")
    logger.info(f"Starting NEM simulator")
    nem_server.start_server()
    logger.info(f"NEM simulator started successfully")
    return nem_server


# This function runs an API call using HTTPS with client certificate authentication
def run_api(host, port, api_path, headers, client_crt, client_key, client_ca, data, method='POST'):
    conn = None
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=client_ca)
        context.load_cert_chain(certfile=client_crt, keyfile=client_key)

        conn = http.client.HTTPSConnection(host, port, context=context)
        body = json.dumps(data) if data else None
        conn.request(method.upper(), api_path, body=body, headers=headers)

        response = conn.getresponse()
        logger.info(f"Received response - [{response.status}] - from the ALG Server")
        response_data = response.read().decode()
        return response.status, response_data
    except Exception as e:
        logger.error("Request failed: %s", e)
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# This function triggers an API call based on the provided API key and JSON configuration file
def trigger_api(api_key, api_file=config['AUTOMATION_VARS']['API_FILE'], host=config['ALG']['DOMAIN_NAME'], port=config['ALG']['PORT']):
    
    api_json_path = os.path.join(config_dir, api_file)
    try:
        with open(api_json_path, "r") as f:
            api_config = json.load(f)

        if api_key not in api_config:
            raise KeyError(f"API key '{api_key}' not found in {api_file}")

        api_details = api_config[api_key]
        method = api_details.get("method", "POST")
        api_path = api_details.get("api_path", "")
        data = api_details.get("data", None)
        headers = api_details.get("headers", {"Content-Type": "application/json"})
        logger.info(f"Running Rest API - {api_path} - {method} from REST Client to ALG Server")
        result = run_api(host, port, api_path, headers,
                         config['TLS_CERTS']['CERT'], config['TLS_CERTS']['KEY'], config['TLS_CERTS']['CA'], data, method)
        if not result:
            logger.error("No response returned from ALG server")
            return None, None

        status_code, body = result

        try:
            parsed = json.loads(body)
            return status_code, parsed
        except json.JSONDecodeError:
            return status_code, body

    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"[ERROR] In trigger_api {e}")
        return None, None


# This function validates the result against expected values and logs discrepancies
def validate_result(expected, result, parent_key=""):
    
    if not isinstance(result, dict):
        logger.error(f"[Invalid Result] Expected a dict but got: {type(result).__name__}")
        return False
    
    success = True
    for key in expected:
        full_key = f"{parent_key}.{key}" if parent_key else key
        if key not in result:
            logger.error(f"[Missing Key] '{full_key}' not found in result")
            success = False
        elif isinstance(expected[key], dict) and isinstance(result[key], dict):
            if not validate_result(expected[key], result[key], parent_key=full_key):
                success = False
        else:
            if expected[key] != result[key]:
                logger.error(f"[Mismatch] '{full_key}': Expected={expected[key]}, Got={result[key]}")
                success = False
            else:
                logger.info(f"'{full_key}' - Received expected response for the API requet from ALG Server")
                logger.info(f"[Match] '{full_key}' = {expected[key]}")
    return success


# This function parses the response string into a dictionary of metrics
def parse_metrics_to_dict(response_str):
    metrics_dict = {}
    for line in response_str.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'(\w+)(\{.*?\})?\s+([\d\.\-eE]+)$', line)
        if match:
            metric, labels_str, value = match.groups()
            key = f"{metric}{labels_str or ''}"
            metrics_dict[key] = value
    return metrics_dict


# This function formats the metrics into a table-like string representation
def format_metrics_as_table(response_str, field_width=100, value_width=20):
    table_data = []
    for line in response_str.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.match(r'(\w+)(\{.*?\})?\s+([\d\.\-eE]+)$', line)
        if not match:
            continue
        metric, labels_str, value = match.groups()
        label_str = ", ".join(f"{k}={v}" for k, v in re.findall(r'(\w+)=["\'](.*?)["\']', labels_str)) if labels_str else ""
        field = f"{metric} [{label_str}]" if label_str else metric
        wrapped_field = "\n".join(textwrap.wrap(field, width=field_width))
        wrapped_value = "\n".join(textwrap.wrap(value, width=value_width))
        table_data.append([wrapped_field, wrapped_value])
    return tabulate(table_data, headers=["Field", "Value"], tablefmt="grid")



# Global variable to store automation summary for HTML log
_automation_summary = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'total_time': 0.0
}

# Initialize report directory and logger globally
_report_dir, _timestamp = get_timestamped_report_dir()
logger, log_path = get_logger(_report_dir, _timestamp)



# TestRunner class to manage test execution and results
class TestRunner:
    def __init__(self):
        self.report_dir, self.timestamp = get_timestamped_report_dir()
        self.csv_file = os.path.join(self.report_dir, "Reports.csv")
        self.test_results = []
        self.start_time = time.time()
        self._ensure_csv_exists()

    # Ensure the CSV file exists and has headers
    def _ensure_csv_exists(self):
        with open(self.csv_file, mode="w", newline="") as f:
            writer = csv.writer(f)
#            writer.writerow(["Test ID", "Executed", "Result", "Execution Time (s)"])
            writer.writerow(["Test ID", "Result", "Execution Time (s)"])

    # Log test results to both in-memory list and CSV file
    def _log_test_result(self, test_id, result, exec_time):
        formatted_time = f"{exec_time:.2f}"
        self.test_results.append((test_id, result, formatted_time))
        with open(self.csv_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([test_id, result, formatted_time])

    # Run a test method, log its execution, and handle exceptions
    def run_test(self, test_id, test_description, test_method):
        print("\n")
        try:
            logger.info(f" ----- **************************************-------")
            logger.info(f" ----- Starting Test execution - [{test_id}] -------")
            create_testcase_folder(self.report_dir, test_id)
            logger.info(f"ALG Status: {is_ALG_active()}")
            start = time.time()
            alg_logs_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_testcase(test_id, test_description)
            logger.info(f"[{test_id}] - {test_description}")
            test_method()
            result = "PASS"
            end = time.time()
            alg_logs_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            get_ALG_logs(test_id, alg_logs_start_time, alg_logs_end_time)
            logger.info(f"ALG Status: {is_ALG_active()}")
        except AssertionError as ae:
            logger.error(f"[Assertion Failure]: {ae}")
            result = "FAIL"
        except Exception as e:
            logger.exception(f"[Exception]: {e}")
            result = "FAIL"
        finally:
            end_testcase(test_id)
        end = time.time()
        logger.info(f" ----- Test execution Completed - [{test_id}] : Status - [{result}] -------")
        self._log_test_result(test_id, result, end - start)

    # Generate a summary of all test results and write to CSV
    def generate_summary(self):
        logger.info(f" ---- Test Suit execution completed ----- ")
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r[1] == "PASS")
        failed = sum(1 for r in self.test_results if r[1] == "FAIL")
        total_time = time.time() - self.start_time

        with open(self.csv_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([])
            writer.writerow(["Total Tests", total, f"Pass: {passed}", f"Fail: {failed}", f"Total Time: {total_time:.2f}s"])
        logger.info(f"Total: {total} | Passed: {passed} | Failed: {failed} | Duration: {total_time:.2f}s")
        print("\n" + "-" * 80)
        print("|{:^78}|".format("Final Result"))
        print("-" * 80)
        print("| {:<12} | {:<12} | {:<12} | {:<31} |".format(f"Total: {total}", f"Passed: {passed}", f"Failed: {failed}", f"Duration: {total_time:.2f}s"))
        print("-" * 80)
        print("| {:<18} | {:<55} |".format(f"Report", f"{self.report_dir}/Reports.csv"))
        print("| {:<18} | {:<55} |".format(f"Automation (JSON)", f"{self.report_dir}/Automation.json"))
        print("| {:<18} | {:<55} |".format(f"Automation (Log)", f"{self.report_dir}/Automation.log"))
        print("| {:<18} | {:<55} |".format(f"Automation (HTML)", f"{self.report_dir}/Automation.html"))
        print("-" * 80)


        # Update global summary for HTML log
        global _automation_summary
        _automation_summary['total'] = total
        _automation_summary['passed'] = passed
        _automation_summary['failed'] = failed
        _automation_summary['total_time'] = total_time
        

# This function searches for a string in a file and counts occurrences
def search_string_in_file(file_path, search_string, num_occurrences=None, use_regex=False):
    count_occurrences = 0
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        for _, line in enumerate(file, 1):
            if use_regex:
                if re.search(search_string, line):
                    count_occurrences += 1
            else:
                if search_string in line:
                    count_occurrences += 1

    logger.debug(f"{search_string} - found {count_occurrences} times in - {file_path}")

    if num_occurrences is not None:
        if count_occurrences == num_occurrences:
            logger.info(f"Success - [{search_string}] - {count_occurrences} times in {file_path} (expected {num_occurrences})")
            return 'PASS'
        else:
            logger.warning(f"Failed - [{search_string}] - {count_occurrences} times in {file_path} (expected {num_occurrences})")
            return 'FAIL'
    else:
        if count_occurrences > 0:
            logger.info(f"Success - [{search_string}] available in {file_path}")
            return 'PASS'
        else:
            logger.info(f"Failed - [{search_string}] not available in {file_path}")
            return 'FAIL'


# This function retrieves filter rules from the ALG server and validates them against expected values
def get_filter_rules_and_validate(
        api_key, 
        expected_values_key, 
        api_file=config['AUTOMATION_VARS']['API_FILE'], 
        host=config['ALG']['DOMAIN_NAME'], 
        port=config['ALG']['PORT']
    ):
    # Load expected values from JSON file
    with open(expected_values_path, "r") as f:
        expected_values = json.load(f)
        
    status_code, body = trigger_api(api_key, api_file, host, port)
    expected = expected_values[expected_values_key]
    
    if body is None:
        logger.error("[Failure] No response received")
        raise AssertionError("No response received from ALG Server")
    assert validate_result(expected, body), "Test failed: Result does not match expected output"


# This function runs a remote command via SSH and returns the output
def run_remote_command(ip_address, username, password, command, waitTime=0, port=22):
    try:
        ssh_client = ssh_connect(ip_address, username, password, port)
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        
        # If command uses sudo, pipe password to sudo
        if command.strip().startswith('sudo '):
            command = f"echo {password} | sudo -S {command[5:]}"
        
        channel.exec_command(command)
        
        if waitTime > 0:
            time.sleep(waitTime)
        
        stdout = channel.makefile('r')
        stderr = channel.makefile_stderr('r')
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        if error:
            logger.warning(f"Remote command error: {error}")
        
        channel.close()
        ssh_client.close()
    except Exception as e:
        logger.error(f"Failed to run remote command: {e}", exc_info=True)
    return output


# This function checks if the ALG service is active (running) on the ALG server
def is_ALG_active():
    """
    SSH into ALG server, run 'systemctl status alggo', and check if service is active (running).
    Returns True if active, False otherwise. Only reads first 10 lines of output for efficiency.
    """
    logger.info("Checking ALG service status")
    try:
        output = run_remote_command(
            config['ALG']['IP_ADDRESS'],
            config['ALG']['USERNAME'],
            config['ALG']['PASSWORD'],
            "systemctl status alggo | head -n 10"
        )
        if "Active: active (running)" in output:
            logger.info("ALG service is active (running)")
            return True
        else:
            logger.warning("ALG service is NOT active (running). Output:\n" + output)
            return False
    except Exception as e:
        logger.error(f"Failed to check ALG status: {e}", exc_info=True)
        return False


# This function retrieves the ALG logs from the ALG server using journalctl
def get_ALG_logs(testcase_id, since, until=None, file_name="ALG.log"):
    try:
        logger.info("Retriving ALG logs for the test case")
        if until == None:
            cmd = f'journalctl --no-pager -u alggo --since "{since}"'
        else:
            cmd = f'journalctl --no-pager -u alggo --since "{since}" --until "{until}"'
            
        logger.info(f"Running command: {cmd}")
        output = run_remote_command(
            config['ALG']['IP_ADDRESS'],
            config['ALG']['USERNAME'],
            config['ALG']['PASSWORD'],
            cmd
        )
        # Use the global _report_dir for the current automation run
        log_file_path = os.path.join(_report_dir, testcase_id, file_name)
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(output)
        logger.info(f"ALG logs retrived successfully to - {log_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to get ALG logs: {e}", exc_info=True)
        return False


# This function retrieves the metrics fields from the ALG server
def get_metrics_fields():
    status_code, metrics_raw = trigger_api("get_metrics")
    if metrics_raw is None:
        return None
    return parse_metrics_to_dict(metrics_raw)


# This function compares the difference in a specific metric field between two metrics dictionaries
def compare_metrics_diff(initial_metrics, final_metrics, testcase_id):
    try:
        with open(expected_values_path, "r") as f:
            expected_values = json.load(f)
        testcase_metrics = expected_values.get(testcase_id, {}).get("metrics_to_validate", [])
        all_pass = True
        for metric in testcase_metrics:
            field = metric["field"]
            expected_diff = metric["expected_diff"]
            try:
                initial_val = int(float(initial_metrics.get(field, 0) or 0))
                final_val = int(float(final_metrics.get(field, 0) or 0))
                actual_diff = int(final_val - initial_val)
                logger.info(f"Comparing {field}: Initial={initial_val}, Final={final_val}, Diff={actual_diff}")
            except (TypeError, ValueError):
                logger.error(f"Could not parse values for field '{field}'")
                all_pass = False
                continue
            try:
                expected_diff_int = int(expected_diff)
            except (TypeError, ValueError):
                logger.error(f"Could not parse expected diff for field '{field}'")
                all_pass = False
                continue
            if actual_diff != expected_diff_int:
                logger.error(f"Metric diff for '{field}' does not match: actual={actual_diff}, expected={expected_diff_int}")
                all_pass = False
            else:
                logger.info(f"Metric diff for '{field}' matches: {actual_diff}")
        return 'PASS' if all_pass else 'FAIL'
    except Exception as e:
        logger.error(f"Failed to compare metrics diff for testcase {testcase_id}: {e}", exc_info=True)
        return 'FAIL'


def generate_config_files():
    simulator_ports = ast.literal_eval(config['NE']['PORTS'])
    ne_ipv4_config_params = {
        "certificate_paths.server_crt_path": f"{config['NE']['CERT']}",
        "certificate_paths.server_key_path": f"{config['NE']['KEY']}",
        "certificate_paths.rootca_crt_path": f"{config['NE']['CA']}",
        "ftp_config.upload_from_path": f"{config['NE']['FTP_UPLOAD_FILE']}",
        "whitelisted_ips[0].ip": f"{config['NE']['IPv4_ADDRESS']}",
        "whitelisted_ips[0].ports": simulator_ports
    }
    nem_ipv4_config_params = {
        "certificate_paths.client_crt_path": f"{config['NEM']['CERT']}",
        "certificate_paths.client_key_path": f"{config['NEM']['KEY']}",
        "certificate_paths.rootca_crt_path": f"{config['NEM']['CA']}",
        "tls_config.tls_server_name": f"{config['ALG']['DOMAIN_NAME']}",
        "whitelisted_ips[0].ip": f"{config['NE']['IPv4_ADDRESS']}",
        "whitelisted_ips[0].ports": simulator_ports
    }
    ne_ipv6_config_params = {
        "ftp_config.upload_from_path": f"{config['NE']['FTP_UPLOAD_FILE']}",
        "certificate_paths.server_crt_path": f"{config['NE']['CERT']}",
        "certificate_paths.server_key_path": f"{config['NE']['KEY']}",
        "certificate_paths.rootca_crt_path": f"{config['NE']['CA']}",
        "whitelisted_ips[0].ip": f"{config['NE']['IPv6_ADDRESS']}",
        "whitelisted_ips[0].ports": simulator_ports
    }
    nem_ipv6_config_params = {
        "certificate_paths.client_crt_path": f"{config['NEM']['CERT']}",
        "certificate_paths.client_key_path": f"{config['NEM']['KEY']}",
        "certificate_paths.rootca_crt_path": f"{config['NEM']['CA']}",
        "tls_config.tls_server_name": f"{config['ALG']['DOMAIN_NAME']}",
        "whitelisted_ips[0].ip": f"{config['NE']['IPv6_ADDRESS']}",
        "whitelisted_ips[0].ports": simulator_ports
    }
    
    output_dir = "generated_configs"
    os.makedirs(output_dir, exist_ok=True)
    update_config_file('Config/NE_config.yaml', f"{output_dir}/NE_ipv4_config.yaml", ne_ipv4_config_params)
    update_config_file('Config/NEM_config.yaml', f"{output_dir}/NEM_ipv4_config.yaml", nem_ipv4_config_params)
    update_config_file('Config/NE_config.yaml', f"{output_dir}/NE_ipv6_config.yaml", ne_ipv6_config_params)
    update_config_file('Config/NEM_config.yaml', f"{output_dir}/NEM_ipv6_config.yaml", nem_ipv6_config_params)
 
    
def update_config_file(file_path: str, output_file: str = None, updates: dict ={}):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.preserve_quotes = True

    # Load file
    if ext in (".yaml", ".yml"):
        with open(file_path, "r") as f:
            data = yaml.load(f)
    elif ext == ".json":
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        raise ValueError("Unsupported file type. Use .yaml, .yml, or .json")

    def parse_path(path):
        parts = []
        for segment in path.split('.'):
            tokens = re.findall(r'([^\[\]]+)|\[(\d+)\]', segment)
            for key, idx in tokens:
                if key:
                    parts.append(key)
                elif idx:
                    parts.append(int(idx))
        return parts

    for path_str, value in updates.items():
        keys = parse_path(path_str)
        d = data
        for i, key in enumerate(keys[:-1]):
            next_key = keys[i + 1]
            if isinstance(key, int):
                while len(d) <= key:
                    d.append(CommentedMap() if isinstance(next_key, str) else CommentedSeq())
                d = d[key]
            else:
                if key not in d or not isinstance(d[key], (dict, list, CommentedMap, CommentedSeq)):
                    d[key] = CommentedSeq() if isinstance(next_key, int) else CommentedMap()
                d = d[key]

        last_key = keys[-1]
        # If the value is a string, force quotes
        if isinstance(value, str):
            value = DoubleQuotedScalarString(value)

        # Only wrap in sequence if it's an actual list
        elif isinstance(value, list):
            seq = CommentedSeq(value)
            seq.fa.set_flow_style()
            value = seq

        if isinstance(last_key, int):
            while len(d) <= last_key:
                d.append(None)
            d[last_key] = value
        else:
            d[last_key] = value

    # Decide output path
    save_path = output_file if output_file else file_path

    # Save back in correct format
    if ext in (".yaml", ".yml"):
        with open(save_path, "w") as f:
            yaml.dump(data, f)
    elif ext == ".json":
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)


# This function generates an MML command in hexadecimal format from a JSON structure
def generate_mml_command(cmd_json: dict) -> str:
    comment = cmd_json.get("comment", "").strip()
    operation = cmd_json.get("operation", "").strip()
    operation_object = cmd_json.get("operation_object", "").strip()
    parameters = cmd_json.get("parameters", {})

    # Format comment, operation, and parameters
    comment_part = f"/*{comment}*/" if comment else ""
    op_obj_part = f"{operation} {operation_object}" if operation_object else operation
    params_part = ",".join(f"{k}={v}" for k, v in parameters.items()) if parameters else ""

    # Final body string
    body_str = f"{comment_part}{op_obj_part}:{params_part};" if params_part else f"{comment_part}{op_obj_part}:;"
    body_bytes = body_str.encode("ascii")
    body_hex = body_bytes.hex()
    body_len = len(body_bytes)  # size in bytes

    data_size = (body_len*2 + 40) // 2   # integer division
    data_size_hex = f"{data_size:04x}"  # 2-byte big-endian

    header_hex = (
        "f634"           # Start Tag
        + data_size_hex  # Data Size (big-endian)
        + "01"           # Service Tag (MML)
        + "0000"         # Session Handle
        + "02"           # Version V2
        + "00000000"     # UIID
        + "03"           # Frame Tag (Single Frame)
        + "00"           # Product ID
        + "0000"         # Reserved1
        + "0000"         # Frame No
        + "00000000"     # Reserved2
        + "0000"         # Extended Length
    )

    final_hex = header_hex + body_hex
    return final_hex


def update_remote_alg_config(ip_address, username, password, updates: dict, port=22, remote_path=config['ALG']['CONFIG_PATH']):
    ssh_client = None
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip_address, port=port, username=username, password=password)
        
        tmp_remote = "/tmp/alg-config.json"
        _, stdout, stderr = ssh_client.exec_command(f"sudo cp {remote_path} {tmp_remote} && sudo chmod 666 {tmp_remote}")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(stderr.read().decode())
        
        sftp = ssh_client.open_sftp()

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            local_path = tmp_file.name
        sftp.get(tmp_remote, local_path)

        with open(local_path, "r") as f:
            config = json.load(f)

        for key, value in updates.items():
            if key in config:
                config[key] = value
            else:
                # add new keys if not present
                config[key] = value

        with open(local_path, "w") as f:
            json.dump(config, f, indent=2)

        sftp.put(local_path, tmp_remote)
        
        _, stdout, stderr = ssh_client.exec_command(f"sudo mv {tmp_remote} {remote_path}")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            raise RuntimeError(stderr.read().decode())

        logger.info(f"✅ Updated {remote_path} on {ip_address}")

        sftp.close()
        ssh_client.close()

    except Exception as e:
        if ssh_client:
            ssh_client.close()
        raise RuntimeError(f"Failed to update {remote_path} on {ip_address}: {e}")