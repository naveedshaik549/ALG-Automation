from TestSuite import TestSuite, runner

if __name__ == "__main__":
    suite = TestSuite()

    runner.run_test("PreCondition_Config", "Configuring ALG with Golden Config for the Automated Run", suite.PreCondition_Config)
    runner.run_test("DTAL-291", "Execution of MML Command 'LICINFO' over IPv4 connection", lambda: suite.DTAL_291(run_time=10))
    runner.run_test("DTAL-292", "Execution of MML Command 'LICINFO' over IPv6 connection", lambda: suite.DTAL_292(run_time=10))
    '''runner.run_test("DTAL-302", lambda: suite.DTAL_302(ne_config_file="Config/DTAL_302_NE_config.yaml", nem_config_file="Config/DTAL_302_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-303", lambda: suite.DTAL_303(ne_config_file="Config/DTAL_303_NE_config.yaml", nem_config_file="Config/DTAL_303_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-310", lambda: suite.DTAL_310(ne_config_file="Config/DTAL_310_NE_config.yaml", nem_config_file="Config/DTAL_310_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-314", lambda: suite.DTAL_314(ne_config_file="Config/DTAL_314_NE_config.yaml", nem_config_file="Config/DTAL_314_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-298", lambda: suite.DTAL_298(ne_config_file="Config/DTAL_291_NE_config.yaml", nem_config_file="Config/DTAL_291_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-299", lambda: suite.DTAL_299(ne_config_file="Config/DTAL_303_NE_config.yaml", nem_config_file="Config/DTAL_303_NEM_config.yaml", run_time=10))
    runner.run_test("DTAL-318", suite.DTAL_318)
    runner.run_test("DTAL-17", suite.DTAL_17)
    runner.run_test("DTAL-18", suite.DTAL_18)
    runner.run_test("DTAL-19", suite.DTAL_19)'''

    runner.generate_summary()
