from ATPSuite import ATPSuite, runner

if __name__ == "__main__":
    suite = ATPSuite()
    
    runner.run_test("PreCondition_Config", "Configuring ALG with Golden Config for the Automated Run", suite.PreCondition_Config)
    runner.run_test("ATP-4_2_1", "To verify the connection between NEM-ALG and ALG-NE over IPv4", lambda: suite.ATP_4_2_1(run_time=10))
    runner.run_test("ATP-4_2_2", "To verify the connection between NEM-ALG and ALG-NE over IPv6", lambda: suite.ATP_4_2_2(run_time=10))
    runner.run_test("ATP-4_2_4", "To verify the connection failure between NEM-ALG and ALG-NE due to invalid certificate over IPv4 and IPv6", lambda: suite.ATP_4_2_4(run_time=10))
    runner.run_test("ATP-4_2_5", "To verify MML filter rule configuration and retrieval via HTTP client", lambda: suite.ATP_4_2_5(run_time=15))
    runner.run_test("ATP-4_2_6", "To verify Binary encoded MML filter rule configuration and retrieval via HTTP client", lambda: suite.ATP_4_2_6(run_time=10))
    runner.run_test("ATP-4_2_7", "To verify Mix of MML and Binary encoded MML filter rule configuration and retrieval via HTTP client", lambda: suite.ATP_4_2_7(run_time=10))
    runner.run_test("ATP-4_2_8", "To verify ALG application rejects Filter rule changes via HTTP client due to different error conditions", suite.ATP_4_2_8)
    runner.run_test("ATP-4_2_9", "To verify MML Handling of ALG application for Accept Rule", lambda: suite.ATP_4_2_9(run_time=10))
    runner.run_test("ATP-4_2_10", "To verify MML Handling of ALG application for Reject Rule", lambda: suite.ATP_4_2_10(run_time=10))
    runner.run_test("ATP-4_2_11", "To verify MML Handling of ALG application for continue Rule", lambda: suite.ATP_4_2_11(run_time=10))
    runner.run_test("ATP-4_2_12", "To verify MML Handling of ALG application for FTP command in Passive Mode over IPv4", lambda: suite.ATP_4_2_12(run_time=10))
    runner.run_test("ATP-4_2_13", "To verify MML Handling of ALG application for FTP command in Extended Passive Mode over IPv4", lambda: suite.ATP_4_2_13(run_time=10))
    runner.run_test("ATP-4_2_14", "To verify MML Handling of ALG application for FTP command in Extended Passive Mode over IPv6", lambda: suite.ATP_4_2_14(run_time=10))
    runner.run_test("ATP-4_2_15", "To verify MML Handling of ALG application for FTP command in negative conditions", lambda: suite.ATP_4_2_15(run_time=10))
    runner.run_test("ATP-4_3_1", "To verify ALG service restart with different log levels", suite.ATP_4_3_1)
    runner.run_test("ATP-4_3_3", "To verify ALG application Metrics for TCP performance and Message Counter", lambda: suite.ATP_4_3_3(run_time=20))
    runner.run_test("ATP-4_3_4", "To verify ALG application Metrics for filter rules", lambda: suite.ATP_4_3_4(run_time=20))
    
    runner.generate_summary()
