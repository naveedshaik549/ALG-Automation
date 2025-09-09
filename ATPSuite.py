import os
import time
import json
import configparser
from datetime import datetime
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
        self.alg_ruleset_update_total = 1
            
            
    #### Each Test case is created as function below
    ## PreCondition for the Test suit to run
    def PreCondition_Config(self):
        testcase_id = "PreCondition_Config"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generating NE and NEM preconfig files
        with log_step("Generate Preconfig files for NE and NEM"):
            utility.generate_config_files()
            
        # Collecting initial metrics
        with log_step("Collecting initial metrics"):
            initial_metrics = utility.get_metrics_fields()
            if initial_metrics is None:
                assert False, "Failed to collect initial metrics"
            logger.debug(f"Initial metrics collected: {initial_metrics}")
            self.alg_ruleset_update_total = int(initial_metrics.get("alg_ruleset_update_total", 1))

        # Installing Filter-Rule As per Golden Config
        with log_step("Filter Rule update"):
            logger.info(f"Updating filter rule as per Goden Config for all test case")
            status_code, _ = utility.trigger_api("precondition_rule")
            time.sleep(1)
            if status_code is None or status_code >= 400:
                logger.error("Installation of filter rules failed")
                raise AssertionError("Installation of filter rules failed")
            logger.info("Filter Rule update successful")
            self.alg_ruleset_update_total += 1
            time.sleep(2)

        # GET Filter rules and validate
        with log_step("Get Filter Rule and validate"):
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
        
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request")
            assert result == 'PASS', f"Validation of test result failed"
            result = utility.search_string_in_file(alg_log_file, "Returning current rule chain")
            assert result == 'PASS', f"Validation of test result failed"


    ## Test case ID - ATP_4_2_1
    def ATP_4_2_1(self, run_time=10):
        testcase_id = "ATP-4_2_1"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        # Validating metrics
        with log_step("Validating Metrics"):
            logger.info(f"Validating Metrics")
            result = utility.compare_metrics_diff(initial_metrics, final_metrics, testcase_id)
            assert result == 'PASS', f"Validation of metric field failed."
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
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


    ## Test case ID - ATP_4_2_2
    def ATP_4_2_2(self, run_time=10):
        testcase_id = "ATP-4_2_2"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        #Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
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
            
            
    def ATP_4_2_4(self, run_time=10):
        testcase_id = "ATP-4_2_4"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
        
        # Collecting ALG logs for IPv4
        with log_step("Collecting ALG logs for IPv4"):
            utility.get_ALG_logs(testcase_id, start, file_name="ALG_IPv4.log")
            
        # Validating NE logs for IPv4
        with log_step("Validating NE logs for IPv4"):
            logger.info(f"Validating NE simulator logs")
            result = utility.search_string_in_file(ne_ipv4_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'FAIL', f"Validation of test result failed."
            
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
        
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
        
        # Collecting ALG logs for IPv6
        with log_step("Collecting ALG logs for IPv6"):
            utility.get_ALG_logs(testcase_id, start, file_name="ALG_IPv6.log")
            
        # Validating NE logs for IPv6
        with log_step("Validating NE logs for IPv6"):
            logger.info(f"Validating NE simulator logs for IPv6")
            result = utility.search_string_in_file(ne_ipv6_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'FAIL', f"Validation of test result failed."
            
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
            
        
    def ATP_4_2_5(self, run_time=10):
        testcase_id = "ATP-4_2_5"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Instaling MML Filter Rule using IPv4
        with log_step("Installing MML Filter Rule using IPv4"):
            logger.info(f"Installing MML Filter Rule using IPv4")
            status_code, _ = utility.trigger_api("ATP_4_2_5_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_5_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling MML Filter Rule using IPv6
        with log_step("Installing Text based Filter Rule using IPv6"):
            logger.info(f"Installing Text based Filter Rule using IPv6")
            status_code, _ = utility.trigger_api("ATP_4_2_5_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_5_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
            
        # Reverting Goden Config Filter Rules
        with log_step("Revert Goden Config Filter Rules"):
            status_code, _ = utility.trigger_api("precondition_rule")
            if status_code is None or status_code >= 400:
                logger.error("Reverting Filter rule failed")
                raise AssertionError("Revert back of filter rules failed")
            time.sleep(2)
            self.alg_ruleset_update_total += 1
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")
   
   
    def ATP_4_2_6(self, run_time=10):
        testcase_id = "ATP-4_2_6"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Instaling Binary based Filter Rule using IPv4
        with log_step("Installing Binary based Filter Rule using IPv4"):
            logger.info(f"Installing Binary based Filter Rule using IPv4")
            status_code, _ = utility.trigger_api("ATP_4_2_6_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_6_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling Binary based Filter Rule using IPv6
        with log_step("Installing Binary based Filter Rule using IPv6"):
            logger.info(f"Installing Binary based Filter Rule using IPv6")
            status_code, _ = utility.trigger_api("ATP_4_2_6_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_6_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
            
        # Reverting Goden Config Filter Rules
        with log_step("Revert Goden Config Filter Rules"):
            status_code, _ = utility.trigger_api("precondition_rule")
            if status_code is None or status_code >= 400:
                logger.error("Reverting Filter rule failed")
                raise AssertionError("Revert back of filter rules failed")
            time.sleep(2)
            self.alg_ruleset_update_total += 1
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")
            
            
    def ATP_4_2_7(self, run_time=10):
        testcase_id = "ATP-4_2_7"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Instaling both MML and Binary based Filter Rule using IPv4
        with log_step("Installing both MML and Binary based Filter Rule using IPv4"):
            logger.info(f"Installing both MML and Binary based Filter Rule using IPv4")
            status_code, _ = utility.trigger_api("ATP_4_2_7_IPv4", api_file=self.api_file, host=config['ALG']['IP_ADDRESS'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv4")
                raise AssertionError("Filter rule installation failed using IPv4")
            logger.info("Filter Rule installation successful using IPv4")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
        
        # GET Filter rules and validate over IPv4
        with log_step("Get Filter Rule and validate over IPv4"):
            logger.info(f"GET Filter rules and validate over IPv4")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_7_IPv4", host=config['ALG']['IP_ADDRESS'])
            
        # Instaling both MML and Binary based Filter Rule using IPv6
        with log_step("Installing both MML and Binary based Filter Rule using IPv6"):
            logger.info(f"Installing both MML and Binary based Filter Rule using IPv6")
            status_code, _ = utility.trigger_api("ATP_4_2_7_IPv6", api_file=self.api_file, host=config['ALG']['IP_ADDRESS_v6'])
            if status_code is None or status_code >= 400:
                logger.error("Filter rule installation failed using IPv6")
                raise AssertionError("Filter rule installation failed using IPv6")
            logger.info("Filter Rule installation successful using IPv6")
            self.alg_ruleset_update_total += 1
            time.sleep(2)
            
        # GET Filter rules and validate over IPv6
        with log_step("Triggering GET Filter rules API with IPv6"):
            logger.info(f"GET Filter rules and validate over IPv6")
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="ATP_4_2_7_IPv6", host=config['ALG']['IP_ADDRESS_v6'])
            
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "Successfully updated and saved filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Received GET /filter-rules request", 2)
            assert result == 'PASS', f"Validation of test result failed"
            
        # Reverting Goden Config Filter Rules
        with log_step("Revert Goden Config Filter Rules"):
            status_code, _ = utility.trigger_api("precondition_rule")
            if status_code is None or status_code >= 400:
                logger.error("Reverting Filter rule failed")
                raise AssertionError("Revert back of filter rules failed")
            time.sleep(2)
            self.alg_ruleset_update_total += 1
            utility.get_filter_rules_and_validate(api_key="get_filter_rules", expected_values_key="precondition_rule")
            
        
    ## Test case ID - ATP_4_2_8    
    def ATP_4_2_8(self, run_time=10):
        # Install invalid filter rules
        with log_step("Install invalid filter rules"):
            status, _ = utility.trigger_api("ATP_4_2_8_A", api_file=self.api_file)
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
            status, _ = utility.trigger_api("ATP_4_2_8_B", api_file=self.api_file)
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
            status, _ = utility.trigger_api("ATP_4_2_8_C", api_file=self.api_file)
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
            
    
    ## Test case ID - ATP_4_2_9
    def ATP_4_2_9(self, run_time=10):
        testcase_id = "ATP-4_2_9"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_config_params = {
            "total_connections": 2,
            "message.message_ratio": "100:0:0",
            "message.mml[0]": "f634003701000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e206163636570742a2f53484b2048414e443a3b",
            "message.mml[1]": "f634003e01000002000000000300000000000000000000002f2a3234363937372a2f445350204c4943494e464f3a46554e4354494f4e545950453d654e6f6465423b"
        }
            
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
        with log_step("Stopping NE simulator"):
            nem_server.stop_server()
            # Ensure NEM simulator has time to stop
            time.sleep(1)
            
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            # Ensure NE simulator has time to stop
            time.sleep(1)
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total packets received\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 2 connections")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(nem_log_file, r"\|\s*Messages sent\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull", 2)
            assert result == 'PASS', f"Validation of test result failed."
            
            
            
    ## Test case ID - ATP_4_2_10        
    def ATP_4_2_10(self, run_time=10):
        testcase_id = "ATP-4_2_10"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_config_params = {
            "total_connections": 2,
            "message.message_ratio": "100:0:0",
            "message.mml[0]": "f634003601000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e2072656a6563742a2f4c535420414c443a3b",
            "message.mml[1]": "f634003701000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e2072656a6563742a2f44535020555345523a3b"
        }
            
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
        with log_step("Stopping NE simulator"):
            nem_server.stop_server()
            # Ensure NEM simulator has time to stop
            time.sleep(1)
            
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            # Ensure NE simulator has time to stop
            time.sleep(1)
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total packets received\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'FAIL', f"Validation of test result failed."
            
        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 2 connections")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(nem_log_file, r"\|\s*Messages sent\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull", 2)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "\"operation\":\"LST\",\"operation-object\":\"ALD\"")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "\"operation\":\"DSP\",\"operation-object\":\"USER\"")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "message was rejected due to filter rule chain", 2)
            assert result == 'PASS', f"Validation of test result failed."
            
            
            
    ## Test case ID - ATP_4_2_11      
    def ATP_4_2_11(self, run_time=10):
        testcase_id = "ATP-4_2_11"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_config_params = {
            "message.message_ratio": "100:0:0",
            "message.mml[0]": "f634003e01000002000000000300000000000000000000002f2a3234363937372a2f44535020494e464f4c49433a46554e4354494f4e545950453d654e6f6465423b"
        }
            
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
        with log_step("Stopping NE simulator"):
            nem_server.stop_server()
            # Ensure NEM simulator has time to stop
            time.sleep(1)
            
        # Stopping NE simulator
        with log_step("Stopping NEM simulator"):
            ne_server.stop_server()
            # Ensure NE simulator has time to stop
            time.sleep(1)
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total packets received\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 1 connections")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(nem_log_file, r"\|\s*Messages sent\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "\"operation\":\"DSP\",\"operation-object\":\"INFOLIC\"")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Rule matched, continuing with logging")
            assert result == 'PASS', f"Validation of test result failed."


    ## Test case ID - ATP_4_2_12
    def ATP_4_2_12(self, run_time=10):
        testcase_id = "ATP-4_2_12"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {"message.message_ratio": "0:100:0"}
        ne_simulator_changes = {"ftp_config.disable_epsv_mode": True}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path, ne_simulator_changes)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_simulator_changes)

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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*FTP Success\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "227 Entering Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "150 File status okay")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "226 Closing data connection")
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
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Executing upstream FTP command")
            assert result == 'PASS', f"Validation of test result failed."
            
            
    ## Test case ID - ATP_4_2_13
    def ATP_4_2_13(self, run_time=10):
        testcase_id = "ATP-4_2_13"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {"message.message_ratio": "0:100:0"}
        ne_simulator_changes = {"ftp_config.disable_epsv_mode": False}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path, ne_simulator_changes)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_simulator_changes)

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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*FTP Success\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "229 Entering Extended Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "150 File status okay")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "226 Closing data connection")
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
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            
            
    
    ## Test case ID - ATP_4_2_14
    def ATP_4_2_14(self, run_time=10):
        testcase_id = "ATP-4_2_14"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {
            "message.message_ratio": "0:100:0",
            "message.ftp[0]": "f6340124010000020000000003000000000000000000003300010008454d53434f4d4d000002000f31302e3130322e3138392e3139360000050010e43a6949e1cebb5708886c8a8d6663b42f2a353238343533393239302a2f554c44204d4541535253543a464e3d224132303235303631342e323131352b303130302d323133302b303130305f4453542b36305f454d532d53484f5254504552494f442e6d72662e677a222c445354463d222f686f6d652f6c616261646d696e2f6674705f646174612f667470746573745f312e747874222c49503d225B666330303A6462383A313A303A3137323A32303A303A31305D3A32313231222c5553523d226c616261646d696e222c5057443d226c616261646d696e313233222c47413d302c4d4f44453d495056363b"
        }
        ne_simulator_changes = {"ftp_config.disable_epsv_mode": False}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv6_config.yaml", ne_dest_config_path, ne_simulator_changes)
            utility.update_config_file("generated_configs/NEM_ipv6_config.yaml", nem_dest_config_path, nem_simulator_changes)

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
                    
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*FTP Success\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "229 Entering Extended Passive Mode")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "150 File status okay")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "226 Closing data connection")
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
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            
            
            
    ## Test case ID - ATP_4_2_15
    def ATP_4_2_15(self, run_time=10):
        testcase_id = "ATP-4_2_15"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {
            "message.message_ratio": "0:100:0",
            "total_connections": 2,
            "message.ftp[0]": "f63400bf010000020000000003000000000000000000003300010008454d53434f4d4d000002000f31302e3130322e3138392e313936000005001077e737b00b0421a6b0a2df7e7da50da72f2a313433323535333130392a2f444c44204445464d4541533a535243463d222f686f6d652f6c616261646d696e2f6674705f646174612f4654505f444c442e747874222c49503d223137322e32302e302e31303a32313231222c5553523d2264756d6d79222c5057443d2264756d6d79222c47413d303b",
            "message.ftp[1]": "f63400c6010000020000000003000000000000000000003300010008454d53434f4d4d000002000f31302e3130322e3138392e313936000005001077e737b00b0421a6b0a2df7e7da50da72f2a313433323535333130392a2f444c44204445464d4541533a535243463d222f686f6d652f6c616261646d696e2f6674705f646174612f64756d6d792e747874222c49503d223137322e32302e302e31303a32313231222c5553523d226c616261646d696e222c5057443d226c616261646d696e313233222c47413d303b"
        }
        ne_simulator_changes = {"ftp_config.disable_epsv_mode": False}

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path, ne_simulator_changes)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_simulator_changes)

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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)

        # Validating NE logs
        with log_step("Validating NE logs"):
            logger.info(f"Validating NE simulator logs")
            ne_log_file = os.path.join(runner.report_dir, testcase_id, "NE_server.log")
            result = utility.search_string_in_file(ne_log_file, r"\|\s*Total connections\s*\|\s*2\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, r"\|\s*FTP Failure\s*\|\s*1\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "FTP DOWNLOAD failed: FTP login failed")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(ne_log_file, "FTPFailureCount: 1")
            assert result == 'PASS', f"Validation of test result failed."

        # Validating NEM logs
        with log_step("Validating NEM logs"):
            logger.info(f"Validating NEM simulator logs")
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            result = utility.search_string_in_file(nem_log_file, "Established 2 connections")
            assert result == 'PASS', f"Validation of test result failed."

        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG.log")
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with upstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "TLS handshake with downstream MML port successfull")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "BTS connected via FTP and matched a transfer configuration from the pool")
            assert result == 'PASS', f"Validation of test result failed."
            
            
    def ATP_4_3_1(self):
        testcase_id = "ATP-4_3_1"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        updates = {
            "alg_log_level": "INFO"
        }
        
        with log_step("Updating ALG configuration log level to INFO"):
            logger.info("Updating ALG configuration log level to INFO")
            utility.update_remote_alg_config(config["ALG"]['IP_ADDRESS'], config["ALG"]['USERNAME'], config["ALG"]['PASSWORD'], updates)
            logger.info("ALG configuration updated successfully")
            time.sleep(2)
        
        # Restarting ALG service
        with log_step("Restarting ALG service"):
            logger.info("Restarting ALG service")
            utility.run_remote_command(config["ALG"]['IP_ADDRESS'], config["ALG"]['USERNAME'], config["ALG"]['PASSWORD'], "sudo systemctl restart alggo.service")
            time.sleep(10)  # Wait for service to restart
            self.alg_ruleset_update_total = 1  # Resetting the counter after restart
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start, file_name="ALG_INFO.log")
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG_INFO.log")
            result = utility.search_string_in_file(alg_log_file, "Stopping ALG-GO")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "alggo.service: Deactivated successfully")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Started ALG-GO")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "\"level\":\"info\"")
            assert result == 'PASS', f"Validation of test result failed."
            
        
        updates = {
            "alg_log_level": "DEBUG"
        }
        
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with log_step("Updating ALG configuration log level to DEBUG"):
            logger.info("Updating ALG configuration log level to DEBUG")
            utility.update_remote_alg_config(config["ALG"]['IP_ADDRESS'], config["ALG"]['USERNAME'], config["ALG"]['PASSWORD'], updates)
            logger.info("ALG configuration updated successfully")
            time.sleep(2)
        
        # Restarting ALG service
        with log_step("Restarting ALG service"):
            logger.info("Restarting ALG service")
            utility.run_remote_command(config["ALG"]['IP_ADDRESS'], config["ALG"]['USERNAME'], config["ALG"]['PASSWORD'], "sudo systemctl restart alggo.service")
            time.sleep(10)  # Wait for service to restart
            self.alg_ruleset_update_total = 1  # Resetting the counter after restart
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start, file_name="ALG_DEBUG.log")
            
            
        # Validating ALG logs
        with log_step("Validating ALG logs"):
            logger.info(f"Validating ALG logs")
            alg_log_file = os.path.join(runner.report_dir, testcase_id, "ALG_DEBUG.log")
            result = utility.search_string_in_file(alg_log_file, "Stopping ALG-GO")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "alggo.service: Deactivated successfully")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "Started ALG-GO")
            assert result == 'PASS', f"Validation of test result failed."
            result = utility.search_string_in_file(alg_log_file, "\"level\":\"debug\"")
            assert result == 'PASS', f"Validation of test result failed."
            
            
    
    def ATP_4_3_3(self, run_time):
        testcase_id = "ATP-4_3_3"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {
            "message.message_ratio": "100:0:0",
            "total_connections": 10,
            "total_packets": 10,
            "packets_per_second": 2,
            "message.mml[0]": "f634003701000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e206163636570742a2f53484b2048414e443a3b",
            "message.mml[1]": "f634003601000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e2072656a6563742a2f4c535420414c443a3b"
        }

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_simulator_changes)
        
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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating metrics
        with log_step("Validating metrics"):
            nem_log_file = os.path.join(runner.report_dir, testcase_id, "NEM_server.log")
            if "alg_mml_tcp_accept_upstream_success" not in initial_metrics or "alg_mml_tcp_accept_upstream_success" not in final_metrics:
                assert False, "Required alg_mml_tcp_accept_upstream_success metrics not found"
            if int(final_metrics["alg_mml_tcp_accept_upstream_success"]) - int(initial_metrics["alg_mml_tcp_accept_upstream_success"]) != 10:
                assert False, f"alg_mml_tcp_accept_upstream_success metrics value is not as expected. Expected increase by 10, Actual increase by: {int(final_metrics['alg_mml_tcp_accept_upstream_success']) - int(initial_metrics['alg_mml_tcp_accept_upstream_success'])}"
            logger.info("alg_mml_tcp_accept_upstream_success metrics validation successful")
            if "alg_mml_tcp_dial_downstream_success" not in initial_metrics or "alg_mml_tcp_dial_downstream_success" not in final_metrics:
                assert False, "Required alg_mml_tcp_dial_downstream_success metrics not found"
            if int(final_metrics["alg_mml_tcp_dial_downstream_success"]) - int(initial_metrics["alg_mml_tcp_dial_downstream_success"]) != 10:
                assert False, f"alg_mml_tcp_dial downstream metrics values are not as expected. Expected increase by 10, Actual increase by {int(final_metrics['alg_mml_tcp_dial_downstream_success']) - int(initial_metrics['alg_mml_tcp_dial_downstream_success'])}"
            logger.info("alg_mml_tcp_dial_downstream_success metrics validation successful")
            bytes_received = int(final_metrics['alg_mml_bytes_transferred{direction="upstream"}']) - int(initial_metrics['alg_mml_bytes_transferred{direction="upstream"}'])
            result = utility.search_string_in_file(nem_log_file, fr"\|\s*Bytes received\s*\|\s*{bytes_received}\s*\|", use_regex=True)
            assert result == 'PASS', f"Validation of test result failed."
            
            
    def ATP_4_3_4(self, run_time):
        testcase_id = "ATP-4_3_4"
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        nem_simulator_changes = {
            "message.message_ratio": "100:0:0",
            "total_connections": 10,
            "total_packets": 10,
            "packets_per_second": 2,
            "message.mml[0]": "f634003701000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e206163636570742a2f53484b2048414e443a3b",
            "message.mml[1]": "f634003601000002000000000300000000000000000000002f2a4d4d4c204175746f6d6174696f6e2072656a6563742a2f4c535420414c443a3b"
        }

        # Generating NE and NEM config files
        with log_step("Generating NE and NEM config files"):
            ne_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NE_config.yaml")
            nem_dest_config_path = os.path.join(runner.report_dir, testcase_id, "NEM_config.yaml")
            utility.update_config_file("generated_configs/NE_ipv4_config.yaml", ne_dest_config_path)
            utility.update_config_file("generated_configs/NEM_ipv4_config.yaml", nem_dest_config_path, nem_simulator_changes)
        
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
        
        # Collecting ALG logs
        with log_step("Collecting ALG logs"):
            utility.get_ALG_logs(testcase_id, start)
            
        # Validating metrics
        with log_step("Validating metrics"):
            if "alg_ruleset_update_total" not in initial_metrics or "alg_ruleset_update_total" not in final_metrics:
                assert False, "Required alg_ruleset_update_total metrics not found"
            if int(initial_metrics["alg_ruleset_update_total"]) != self.alg_ruleset_update_total:
                assert False, f"alg_ruleset_update_total metrics value is not as expected. Expected: {self.alg_ruleset_update_total}, Actual: {final_metrics['alg_ruleset_update_total']}"
            logger.info("alg_ruleset_update_total metrics validation successful")
            if "alg_mml_messages_forwarded{direction=\"downstream\"}" not in initial_metrics or "alg_mml_messages_forwarded{direction=\"downstream\"}" not in final_metrics:
                assert False, "Required alg_mml_messages_forwarded{direction=\"downstream\"} metrics not found"
            if int(final_metrics["alg_mml_messages_forwarded{direction=\"downstream\"}"]) - int(initial_metrics["alg_mml_messages_forwarded{direction=\"downstream\"}"]) != 50:
                assert False, f"alg_mml_messages_forwarded downstream metrics values are not as expected. Expected increase by 50, Actual increase by {int(final_metrics['alg_mml_messages_forwarded{direction=\"downstream\"}']) - int(initial_metrics['alg_mml_messages_forwarded{direction=\"downstream\"}'])}"
            logger.info("alg_mml_messages_forwarded{direction=\"downstream\"} metrics validation successful")
            if "alg_mml_messages_rejected{direction=\"downstream\"}" not in initial_metrics or "alg_mml_messages_rejected{direction=\"downstream\"}" not in final_metrics:
                assert False, "Required alg_mml_messages_rejected{direction=\"downstream\"} metrics not found"
            if int(final_metrics["alg_mml_messages_rejected{direction=\"downstream\"}"]) - int(initial_metrics["alg_mml_messages_rejected{direction=\"downstream\"}"]) != 50:
                assert False, f"alg_mml_messages_rejected downstream metrics values are not as expected. Expected increase by 50, Actual increase by {int(final_metrics['alg_mml_messages_rejected{direction=\"downstream\"}']) - int(initial_metrics['alg_mml_messages_rejected{direction=\"downstream\"}'])}"
            logger.info("alg_mml_messages_rejected{direction=\"downstream\"} metrics validation successful")
            
        
        
        