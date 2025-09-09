from TestSuite import TestSuite, runner
from utils import utility

if __name__ == "__main__":
    suite = TestSuite()
    
    updates = {
        "alg_log_level": "DEBUG"
    }

    utility.update_remote_alg_config(
        ip_address="109.230.228.91",
        username="labadmin",
        password="lab123admin123",
        updates=updates
    )

    '''runner.run_test("PreCondition_Config", "Configuring ALG with Golden Config for the Automated Run", suite.PreCondition_Config)
    runner.run_test("DTAL-291", "Execution of MML Command 'LICINFO' over IPv4 connection", lambda: suite.DTAL_291(run_time=10))
    runner.run_test("DTAL-292", "Execution of MML Command 'LICINFO' over IPv6 connection", lambda: suite.DTAL_292(run_time=10))
    runner.run_test("DTAL-302", "Execution of Binary CmdCode - 5 over IPv4 connection", lambda: suite.DTAL_302(run_time=10))
    runner.run_test("DTAL-303", "Execution of Binary CmdCode - 257 over IPv6 connection", lambda: suite.DTAL_303(run_time=10))
    runner.run_test("DTAL-310", "Execution of MML command with FTP upload command in passive mode over IPv4 connection", lambda: suite.DTAL_310(run_time=10))
    runner.run_test("DTAL-314", "Execution of MML command with FTP upload command in Extended Passive mode over IPv6 connection", lambda: suite.DTAL_314(run_time=10))
    runner.run_test("DTAL-298", "Updating Filter Rule runtime for MML rules only and running MML command over IPv4 connection", lambda: suite.DTAL_298(run_time=10))
    runner.run_test("DTAL-299", "Updating Filter Rule runtime for Binary rules only and running Binary command over IPv4 connection", lambda: suite.DTAL_299(run_time=10))
    runner.run_test("DTAL-318", "Getting Metrics from ALG and validating for some static fields", suite.DTAL_318)
    runner.run_test("DTAL-17", "Validate Installation of invalid filter rules", suite.DTAL_17)
    runner.run_test("DTAL-18", "Validate Installation of filter rules with missing fields", suite.DTAL_18)
    runner.run_test("DTAL-19", "Validate Installation of filter rules with invalid JSON/Schema", suite.DTAL_19)'''

    runner.generate_summary()
