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


class TestSuite:
    def __init__(self):
        # Load expected values from JSON file
        with open(expected_values_path  , "r") as f:
            self.expected_values = json.load(f)


    #### Each Test case is created as function below
    ## PreCondition for the Test suit to run
    def PreCondition_Config(self):
        testcase_id = "PreCondition_Config"
        start = time.time()
        
        with log_step("Generate Preconfig files for NE and NEM"):
            utility.generate_config_files()

        # Installing Filter-Rule As per Golden Config
        with log_step("Filter Rule update"):
            logger.info(f"Updating filter rule as per Goden Config for all test case")
            status_code, body = utility.trigger_api("precondition_rule")
            time.sleep(1)
            if status_code is None or status_code >= 400:
                logger.error("Installation of filter rules failed")
                raise AssertionError("Installation of filter rules failed")
            logger.info("Filter Rule update successful")
            time.sleep(2)

        with log_step("Get Filter Rule and validate"):
            # Checking current Filter-Rule setting after update
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")

        end = time.time()
        timeTaken = end - start
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)
        
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request")
            assert result == 'PASS', f"Validation of test result failed"
            result = utility.search_string_in_file(alg_log_file, "Returning current rule chain")
            assert result == 'PASS', f"Validation of test result failed"


    ## Test case ID - DTAL_291
    def DTAL_291(self, run_time=10):
        testcase_id = "DTAL-291"
        start = time.time()

        simulator_changes = {"message.message_ratio": "100:0:0"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

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
    def DTAL_292(self, run_time=10):
        testcase_id = "DTAL-292"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "100:0:0"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv6_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv6_config.yaml", nem_dest_config_path, simulator_changes)

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

    def DTAL_302(self, run_time=10):
        testcase_id = "DTAL-302"
        start = time.time()

        simulator_changes = {"message.message_ratio": "0:0:100"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

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


    ## Test case ID - DTAL_303
    def DTAL_303(self, run_time=10):
        testcase_id = "DTAL-303"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "0:0:100"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv6_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv6_config.yaml", nem_dest_config_path, simulator_changes)

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
            result = utility.search_string_in_file(alg_log_file, "binary-request-message")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "SERVICE_TAG_DL_BIN_2")
            assert result == 'PASS', f"Validation of test result failed."                

    ## Test case ID - DTAL_310
    def DTAL_310(self, run_time=10):
        testcase_id = "DTAL-310"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "0:0:100"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

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
            result = utility.search_string_in_file(ne_log_file, "227 Entering Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "150 File status okay")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "226 Closing data connection")
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
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "227 Entering Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Accepted downstream FTP transfer connection")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Executing upstream FTP command")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Closed the downstream FTP control channel connection")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Closed the upstream FTP control channel connection")
            assert result == 'PASS', f"Validation of test result failed."               


    ## Test case ID - DTAL_314
    def DTAL_314(self, ne_config_file=None, nem_config_file=None, run_time=10):
        testcase_id = "DTAL-314"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "0:0:100"}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

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

        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            #result = utility.search_string_in_file(ne_log_file, "Total connections: 1", int(simulator_val1))
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "229 Entering Extended Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "150 File status okay")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "226 Closing data connection")
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
            result = utility.search_string_in_file(alg_log_file, "220 Service ready for new user")
            assert result == 'PASS', f"Validation of test result failed."        
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "229 Entering Extended Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Accepted downstream FTP transfer connection")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Executing upstream FTP command")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Closed the downstream FTP control channel connection")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Closed the upstream FTP control channel connection")
            assert result == 'PASS', f"Validation of test result failed."               


    ## Test case ID - DTAL_298
    def DTAL_298(self, ne_config_file=None, nem_config_file=None, run_time=10):
        testcase_id = "DTAL-298"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "0:0:100"}
        
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

        with log_step("Update Filter Rules - MML"):
            # Installing New Filter-Rule
            logger.info("Updating filter rule as per test case")
            status_code, body = utility.trigger_api("DTAL-298")
            if status_code is None or status_code >= 400:
                logger.error("Filter rules with update failed")
                raise AssertionError("Installation of filter rules having mml only failed")
            logger.info("Filter Rule update successful")
            time.sleep(2)

        with log_step("Validating updated Filter Rules"):
            # Checking current Filter-Rule setting after update
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL-298")

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

        with log_step("Revert Goden Config Filter Rules"):
            # Reverting Filter-Rule setting after test case completion
            status_code, body = utility.trigger_api("precondition_rule")
            if status_code is None or status_code >= 400:
                logger.error("Reverting Filter rule failed")
                raise AssertionError("Revert back of filter rules failed")
            time.sleep(2)
            # Checking current Filter-Rule setting after revert
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")

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
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request")
            assert result == 'PASS', f"Validation of test result failed"
            result = utility.search_string_in_file(alg_log_file, "Returning current rule chain")
            assert result == 'PASS', f"Validation of test result failed"                               


    ## Test case ID - DTAL_299
    def DTAL_299(self, ne_config_file=None, nem_config_file=None, run_time=10):
        testcase_id = "DTAL-299"
        start = time.time()
        
        simulator_changes = {"message.message_ratio": "0:0:100"}
        
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, simulator_changes)

        with log_step("Update Filter Rules - Binary"):
            # Installing New Filter-Rule
            logger.info("Updating filter rule as per test case")
            status_code, body = utility.trigger_api("DTAL-299")
            if status_code is None or status_code >= 400:
                logger.error("Filter rules with update failed")
                raise AssertionError("Installation of filter rules having binary only failed")
            logger.info("Filter Rule update successful")
            time.sleep(2)

        with log_step("Validating updated Filter Rules"):
            # Checking current Filter-Rule setting after update
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL-298")

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

        with log_step("Revert Goden Config Filter Rules"):
            # Reverting Filter-Rule setting after test case completion
            status_code, body = utility.trigger_api("precondition_rule")
            if status_code is None or status_code >= 400:
                logger.error("Reverting Filter rule failed")
                raise AssertionError("Revert back of filter rules failed")
            time.sleep(2)
            # Checking current Filter-Rule setting after revert
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")

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
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request")
            assert result == 'PASS', f"Validation of test result failed"
            result = utility.search_string_in_file(alg_log_file, "Returning current rule chain")
            assert result == 'PASS', f"Validation of test result failed"                               


    ## Test case ID - DTAL_318
    def DTAL_318(self):
        testcase_id = "DTAL-318"
        start = time.time()

        # Retrieving current Metrics
        with log_step("Retrieving Metrics"):
            status_code, body = utility.trigger_api("get_metrics")
            if status_code is None or status_code >= 400:
                logger.error(f"No response received from ALG Server")
                assert False, "API did not return any response"
                return
            time.sleep(1)

        with log_step("Parsing Metrics"):
            metrics_dict = utility.parse_metrics_to_dict(body)

        with log_step("Getting Metrics in Tablular format"):
            metrics_table = utility.format_metrics_as_table(body)
            logger.info(f"Generated Metrics Table")
            logger.debug(f"[Metrics Table]\n" + metrics_table)

        end = time.time()
        timeTaken = end - start
        
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)                               
            
            
    ## Test case ID - DTAL_17
    def DTAL_17(self):
        testcase_id = "DTAL-17"

        with log_step("Install invalid filter rules"):
            status, body = utility.trigger_api("install_invalid_filter_rules")
            if status is None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")

            logger.info("Installation api called successfully")

        with log_step("Validate response failure"):
            if status != 422:
                logger.error(f"Expected status 422, got {status}")
                raise AssertionError(f"Expected status 422, got {status}")

            logger.info("Response status code is 422 as expected")


    def DTAL_18(self):
        testcase_id = "DTAL-18"

        with log_step("Install filter rules with missing fields"):
            status, body = utility.trigger_api("install_filter_rules_with_missing_fields")
            if status == None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")

            logger.info("Installation api called successfully")

        with log_step("Validate response failure"):
            if status != 422:
                logger.error(f"Expected status 422, got {status}")
                raise AssertionError(f"Expected status 422, got {status}")

            logger.info("Response status code is 422 as expected")


    def DTAL_19(self):
        testcase_id = "DTAL-19"

        with log_step("Install filter rules with invalid JSON/Schema"):
            status, body = utility.trigger_api("install_filter_rules_with_invalid_json_schema")
            if status is None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")

            logger.info("Installation api called successfully")

        with log_step("Validate response failure"):
            if status != 415:
                logger.error(f"Expected status 415, got {status}")
                raise AssertionError(f"Expected status 415, got {status}")

            logger.info("Response status code is 415 as expected")