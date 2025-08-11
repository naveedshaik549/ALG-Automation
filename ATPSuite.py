import os
from utils import utility
import configparser
config_dir = os.path.join(os.path.dirname(__file__), "Config")
config = configparser.ConfigParser()
config_path = os.path.join(config_dir, 'config.ini')
config.read(os.path.abspath(config_path))
expected_values_path = os.path.join(config_dir, "expected_values.json")
import json
import time
from utils.html_report_generator import log_step

logger = utility.logger
runner = utility.TestRunner()


class ATPSuite:
    def __init__(self):
        # Load expected values from JSON file
        with open(expected_values_path  , "r") as f:
            self.expected_values = json.load(f)


    ## Test case ID - DTAL_291
    def DTAL_291(self, run_time=10):
        testcase_id = "DTAL-291"
        start = time.time()

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.generate_sim_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.generate_sim_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path)

        # Collecting initial metrics
        with log_step("Collecting initial metrics"):
            initial_metrics = utility.get_metrics_fields()
            if initial_metrics is None:
                assert False, "Failed to collect initial metrics"
            logger.debug(f"Initial metrics collected: {initial_metrics}")
            
                
        # Starting NE simulator
        with log_step("Starting NE simulator"):
            ne_server = utility.start_NE(testcase_id, runner.report_dir, ne_dest_config_path)
            if ne_server is None:
                assert False, "NE server failed to start"

        # Starting NEM simulator
        with log_step("Starting NEM simulator"):
            nem_server = utility.start_NEM(testcase_id, runner.report_dir, nem_dest_config_path)
            if nem_server is None:
                assert False, "NEM server failed to start"
            logger.info(f"Waiting for {run_time} seconds for simulator to complete the operation")
            time.sleep(run_time)

        # Stopping NEM simulator
        with log_step("Stopping NE simulator "):
            nem_server.stop_server()
            # Ensure NEM simulator has time to stop
            time.sleep(1)
        
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            # Ensure NE simulator has time to stop
            time.sleep(1)

        # Collecting final metrics
        with log_step("Collecting final metrics"):
            final_metrics = utility.get_metrics_fields()
            if final_metrics is None:
                assert False, "Failed to collect final metrics"
            logger.debug(f"Final metrics collected: {final_metrics}")

        end = time.time()
        timeTaken = end - start
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)

        #simulator_val1 = int(run_time) - 2
        with log_step("Validating Metrics"):
            logger.info(f"Validating Metrics")
            result = utility.compare_metrics_diff(initial_metrics, final_metrics, testcase_id)
            assert result == 'PASS', f"Validation of metric field failed."
            
        #simulator_val1 = int(run_time) - 2
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            #result = utility.search_string_in_file(ne_log_file, "Total connections: 1", int(simulator_val1))
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."

        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."

        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."


    ## Test case ID - DTAL_292
    def DTAL_292(self, ne_config_file=None, nem_config_file=None, run_time=10):
        testcase_id = "DTAL-292"
        start = time.time()
        
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.generate_sim_config_file("generated_configs/NE_ipv6_config.yaml", ne_dest_config_path)
            utility.generate_sim_config_file("generated_configs/NEM_ipv6_config.yaml", nem_dest_config_path, {"message.message_ratio": "0:100:0"})

        # Starting NE simulator
        with log_step("Starting NE simulator"):
            ne_server = utility.start_NE(testcase_id, runner.report_dir, ne_dest_config_path)
            if ne_server is None:
                assert False, "NE server failed to start"

        # Starting NEM simulator
        with log_step("Starting NEM simulator"):
            nem_server = utility.start_NEM(testcase_id, runner.report_dir, nem_dest_config_path)
            if nem_server is None:
                assert False, "NEM server failed to start"
            logger.info(f"Waiting for {run_time} seconds for simulator to complete the operation")
            time.sleep(run_time)

        # Stopping NEM simulator
        with log_step("Stopping NE simulator "):
            nem_server.stop_server()
            # Ensure NEM simulator has time to stop
            time.sleep(1)
        
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            # Ensure NE simulator has time to stop
            time.sleep(1)

        end = time.time()
        timeTaken = end - start
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)

        #simulator_val1 = int(run_time) - 2
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            #result = utility.search_string_in_file(ne_log_file, "Total connections: 1", int(simulator_val1))
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."

        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."

        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."