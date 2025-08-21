from ATPSuite import ATPSuite, runner

if __name__ == "__main__":
    suite = ATPSuite()

    runner.run_test("PreCondition_Config", "Configuring ALG with Golden Config for the Automated Run", suite.PreCondition_Config)
    runner.run_test("DTAL-4_2_1", "To verify the connection between NEM-ALG and ALG-NE over IPv4", lambda: suite.DTAL_4_2_1(run_time=10))
    runner.run_test("DTAL-4_2_2", "To verify the connection between NEM-ALG and ALG-NE over IPv6", lambda: suite.DTAL_4_2_2(run_time=10))
    runner.run_test("DTAL-4_2_4", "To verify the connection failure between NEM-ALG and ALG-NE due to invalid certificate over IPv4 and IPv6", lambda: suite.DTAL_4_2_4(run_time=10))
    runner.run_test("DTAL-4_2_5", "To verify MML filter rule configuration and retrieval via HTTP client", lambda: suite.DTAL_4_2_5(run_time=10))
    runner.run_test("DTAL-4_2_6", "To verify Binary encoded MML filter rule configuration and retrieval via HTTP client", lambda: suite.DTAL_4_2_6(run_time=10))
    runner.run_test("DTAL-4_2_7", "To verify Mix of MML and Binary encoded MML filter rule configuration and retrieval via HTTP client", lambda: suite.DTAL_4_2_7(run_time=10))
    runner.run_test("DTAL-4_2_8", "To verify ALG application rejects Filter rule changes via HTTP client due to different error conditions", suite.DTAL_4_2_8)

    runner.generate_summary()
