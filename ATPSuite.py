import os
import time
import json
import configparser
from utils import utility
from utils.html_report_generator import log_step

config = configparser.ConfigParser()
config_dir = os.path.join(os.path.dirname(__file__), "Config")
config_path = os.path.join(config_dir, 'config.ini')
config.read(os.path.abspath(config_path))
expected_values_path = os.path.join(config_dir, config['AUTOMATION_VARS']['EXPECTED_API_FILE'])

logger = utility.logger
runner = utility.TestRunner()


class ATPSuite:
    def __init__(self):
        # Load expected values from JSON file
        with open(expected_values_path  , "r") as f:
            self.expected_values = json.load(f)
        self.api_file = config['AUTOMATION_VARS']['API_FILE']
            
            
    #### Each Test case is created as function below
    ## PreCondition for the Test suit to run
    def PreCondition_Config(self):
        testcase_id = "PreCondition_Config"
        start = time.time()
        
        # Generating NE and NEM preconfig files
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

        # GET Filter rules and validate
        with log_step("Get Filter Rule and validate"):
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")

        end = time.time()
        timeTaken = end - start
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)
        
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request")
            assert result == 'PASS', f"Validation of test result failed"
            result = utility.search_string_in_file(alg_log_file, "Returning current rule chain")
            assert result == 'PASS', f"Validation of test result failed"


    ## Test case ID - DTAL_4_2_1
    def DTAL_4_2_1(self, run_time=10):
        testcase_id = "DTAL-4_2_1"
        start = time.time()

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path)

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
            time.sleep(1)
        
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            time.sleep(1)

        # Collecting final metrics
        with log_step("Collecting final metrics"):
            final_metrics = utility.get_metrics_fields()
            if final_metrics is None:
                assert False, "Failed to collect final metrics"
            logger.debug(f"Final metrics collected: {final_metrics}")

        end = time.time()
        timeTaken = end - start
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)

        # Validating metrics
        with log_step("Validating Metrics"):
            logger.info(f"Validating Metrics")
            result = utility.compare_metrics_diff(initial_metrics, final_metrics, testcase_id)
            assert result == 'PASS', f"Validation of metric field failed."
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."

        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."

        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."


    ## Test case ID - DTAL_4_2_2
    def DTAL_4_2_2(self, run_time=10):
        testcase_id = "DTAL-4_2_2"
        start = time.time()
        
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv6_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv6_config.yaml", nem_dest_config_path)

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
            time.sleep(1)
        
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            time.sleep(1)

        end = time.time()
        timeTaken = end - start
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)

        #Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."

        #Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."

        #Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            
            
    def DTAL_4_2_4(self, run_time=10):
        testcase_id = "DTAL-4_2_4"
        start = time.time()
        
        nem_config_params = {"tls_config.tls_server_name": "www.example.com"}
        ne_ipv4_log_file = os.path.join(runner.report_dir, testcase_id, "NE_IPv4_server.log")
        ne_ipv6_log_file = os.path.join(runner.report_dir, testcase_id, "NE_IPv6_server.log")
        nem_ipv4_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_IPv4_server.log")
        nem_ipv6_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_IPv6_server.log")
        
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM IPv4 & IPv6 config files"):
            ne_ipv4_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_IPv4_config.yaml")
            nem_ipv4_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_IPv4_config.yaml")
            ne_ipv6_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_IPv6_config.yaml")
            nem_ipv6_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_IPv6_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_ipv4_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_ipv4_dest_config_path, nem_config_params)
            utility.update_config_file("generated_configs/NE_ipv6_config.yaml", ne_ipv6_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv6_config.yaml", nem_ipv6_dest_config_path, nem_config_params)
            
        # Starting NE simulator with IPv4 config
        with log_step("Starting NE simulator with IPv4 config"):
            ne_server = utility.start_NE(testcase_id, runner.report_dir, ne_ipv4_dest_config_path, ne_ipv4_log_file)
            if ne_server is None:
                assert False, "NE server failed to start with IPv4 config"
                
        # Starting NEM simulator with IPv4 config
        with log_step("Starting NEM simulator with IPv4 config"):
            nem_server = utility.start_NEM(testcase_id, runner.report_dir, nem_ipv4_dest_config_path, nem_ipv4_log_file)
            if nem_server is None:
                assert False, "NEM server failed to start with IPv4 config"
            logger.info(f"Waiting for {run_time} seconds for simulator to complete the operation")
            time.sleep(run_time)
            
        # Stopping NEM simulator
        with log_step("Stopping NE simulator"):
            nem_server.stop_server()
            time.sleep(1)
            
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            time.sleep(1)
            
        end = time.time()
        timeTaken = end - start
        
        # Collecting ALG logs for IPv4
        with log_step("Collecting ALG logs for IPv4"):
            utility.get_ALG_logs(testcase_id, timeTaken, "ALG_IPv4.log")
            
        # Validating NE logs for IPv4
        with log_step("Validating NE logs for IPv4"):
            logger.info(f"Validating NE simulator logs")
            result = utility.search_string_in_file(ne_ipv4_log_file, "Total connections: 0")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating NEM logs for IPv4
        with log_step("Validating NEM logs for IPv4"):
            logger.info(f"Validating NEM simulator logs")
            result = utility.search_string_in_file(nem_ipv4_log_file, f"TLS handshake failed: tls: failed to verify certificate: x509: certificate is valid for {config['ALG']['DOMAIN_NAME']}, not www.example.com")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs for IPv4
        with log_step("Validating ALG logs for IPv4"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG_IPv4.log")
            result = utility.search_string_in_file(alg_log_file, "remote error: tls: bad certificate")
            assert result == 'PASS', f"Validation of test result failed."
        
        start = time.time()
        
        # Starting NE simulator with IPv6 config
        with log_step("Starting NE simulator with IPv6 config"):
            ne_server_ipv6 = utility.start_NE(testcase_id, runner.report_dir, ne_ipv6_dest_config_path, ne_ipv6_log_file)
            if ne_server_ipv6 is None:
                assert False, "NE server failed to start with IPv6 config"
                
        # Starting NEM simulator with IPv6 config
        with log_step("Starting NEM simulator with IPv6 config"):
            nem_server_ipv6 = utility.start_NEM(testcase_id, runner.report_dir, nem_ipv6_dest_config_path, nem_ipv6_log_file)
            if nem_server_ipv6 is None:
                assert False, "NEM server failed to start with IPv6 config"
            logger.info(f"Waiting for {run_time} seconds for simulator to complete the operation")
            time.sleep(run_time)
            
        # Stopping NEM simulator
        with log_step("Stopping NE simulator with IPv6 config"):
            nem_server_ipv6.stop_server()
            time.sleep(1)
            
        # Stopping NE simulator
        with log_step("Stopping NEM simulator with IPv6 config"):
            ne_server_ipv6.stop_server()
            time.sleep(1)
            
        end = time.time()
        timeTaken = end - start
        
        # Collecting ALG logs for IPv6
        with log_step("Collecting ALG logs for IPv6"):
            utility.get_ALG_logs(testcase_id, timeTaken, "ALG_IPv6.log")
            
        # Validating NE logs for IPv6
        with log_step("Validating NE logs for IPv6"):
            logger.info(f"Validating NE simulator logs for IPv6")
            result = utility.search_string_in_file(ne_ipv6_log_file, "Total connections: 0")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating NEM logs for IPv6
        with log_step("Validating NEM logs for IPv6"):
            logger.info(f"Validating NEM simulator logs for IPv6")
            result = utility.search_string_in_file(nem_ipv6_log_file, f"TLS handshake failed: tls: failed to verify certificate: x509: certificate is valid for {config['ALG']['DOMAIN_NAME']}, not www.example.com")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs for IPv6
        with log_step("Validating ALG logs for IPv6"):
            logger.info(f"Validating ALG logs for IPv6")
            alg_log_file_ipv6 = os.path.join(runner.report_dir, testcase_id, "ALG_IPv6.log")
            result = utility.search_string_in_file(alg_log_file_ipv6, "remote error: tls: bad certificate")
            assert result == 'PASS', f"Validation of test result failed."
            
        
    def DTAL_4_2_5(self, run_time=10):
        testcase_id = "DTAL-4_2_5"
        start = time.time()
        
        # Instaling MML Filter Rule using IPv4
        with log_step("Installing MML Filter Rule using IPv4"):
            logger.info(f"Installing MML Filter Rule using IPv4")
            status_code, body = utility.trigger_api("DTAL_4_2_5_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_5_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling MML Filter Rule using IPv6
        with log_step("Installing Text based Filter Rule using IPv6"):
            logger.info(f"Installing Text based Filter Rule using IPv6")
            status_code, body = utility.trigger_api("DTAL_4_2_5_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_5_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        end = time.time()
        timeTaken = end - start
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            logger.info(f"Total time taken for the test case: {timeTaken} seconds")
            utility.get_ALG_logs(testcase_id, timeTaken)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
   
   
    def DTAL_4_2_6(self, run_time=10):
        testcase_id = "DTAL-4_2_6"
        start = time.time()
        
        # Instaling Binary based Filter Rule using IPv4
        with log_step("Installing Binary based Filter Rule using IPv4"):
            logger.info(f"Installing Binary based Filter Rule using IPv4")
            status_code, body = utility.trigger_api("DTAL_4_2_6_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_6_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling Binary based Filter Rule using IPv6
        with log_step("Installing Binary based Filter Rule using IPv6"):
            logger.info(f"Installing Binary based Filter Rule using IPv6")
            status_code, body = utility.trigger_api("DTAL_4_2_6_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_6_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        end = time.time()
        timeTaken = end - start
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
            
            
    def DTAL_4_2_7(self, run_time=10):
        testcase_id = "DTAL-4_2_7"
        start = time.time()
        
        # Instaling both MML and Binary based Filter Rule using IPv4
        with log_step("Installing both MML and Binary based Filter Rule using IPv4"):
            logger.info(f"Installing both MML and Binary based Filter Rule using IPv4")
            status_code, body = utility.trigger_api("DTAL_4_2_7_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_7_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling both MML and Binary based Filter Rule using IPv6
        with log_step("Installing both MML and Binary based Filter Rule using IPv6"):
            logger.info(f"Installing both MML and Binary based Filter Rule using IPv6")
            status_code, body = utility.trigger_api("DTAL_4_2_7_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="DTAL_4_2_7_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        end = time.time()
        timeTaken = end - start
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
            
        
    ## Test case ID - DTAL_4_2_8    
    def DTAL_4_2_8(self):
        # Install invalid filter rules
        with log_step("Install invalid filter rules"):
            status, body = utility.trigger_api("DTAL_4_2_8_A", api_file=self.api_file)
            if status is None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")
            logger.info("Installation api called successfully")

        # Validate response failure
        with log_step("Validate response failure"):
            if status != 422:
                logger.error(f"Expected status 422, got {status}")
                raise AssertionError(f"Expected status 422, got {status}")
            logger.info("Response status code is 422 as expected")
            
        # Install filter rules with missing fields
        with log_step("Install filter rules with missing fields"):
            status, body = utility.trigger_api("DTAL_4_2_8_B", api_file=self.api_file)
            if status == None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")
            logger.info("Installation api called successfully")

        # Validate response failure
        with log_step("Validate response failure"):
            if status != 422:
                logger.error(f"Expected status 422, got {status}")
                raise AssertionError(f"Expected status 422, got {status}")
            logger.info("Response status code is 422 as expected")
            
        # Install filter rules with invalid JSON/Schema
        with log_step("Install filter rules with invalid JSON/Schema"):
            status, body = utility.trigger_api("DTAL_4_2_8_C", api_file=self.api_file)
            if status is None:
                logger.error(f"Api call failed")
                raise AssertionError(f"Api execution failed")
            logger.info("Installation api called successfully")

        # Validate response failure
        with log_step("Validate response failure"):
            if status != 415:
                logger.error(f"Expected status 415, got {status}")
                raise AssertionError(f"Expected status 415, got {status}")
            logger.info("Response status code is 415 as expected")
            
    
    def DTAL_4_2_9(self):
        testcase_id = "DTAL-4_2_9"
        
        nem_config_params = {
            "total_connections": 2,
            "message.message_ratio": "50:50:0",
            "message.mml[0]": "f634003e01000002000000000300000000000000000000002f2a3234363937372a2f445350204c4943494e464f3a46554e4354494f4e545950453d654e6f6465423b", 
            "message.bin[0]": "f63400340213370211223344031f234200004433221100102342000774e282ac735c7400000000000503e9020000007b000001c800000000"
        }
        
        # Installing MML and Binary Accept Filter Rules
        with log_step("Instaling MML and Binary Accept Filter Rules"):
            logger.info(f"Instaling MML and Binary Accept Filter Rules")
            status_code, body = utility.trigger_api("DTAL_4_2_9", api_file=self.api_file)
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed")
                raise AssertionError("Filter rule installation failed")
            logger.info("Filter Rule installation successful")
            time.sleep(2)
            
        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_config_params)
            
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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, timeTaken)
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, "Total connections: 1")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."

