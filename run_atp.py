from ATPSuite import ATPSuite, runner

if __name__ == "__main__":
    suite = ATPSuite()

    runner.run_test("DTAL-291", "Execution of MML Command 'LICINFO' over IPv4 connection", lambda: suite.DTAL_291(run_time=10))
    runner.run_test("DTAL-292", "Execution of MML Command 'LICINFO' over IPv6 connection", lambda: suite.DTAL_292(run_time=10))

    runner.generate_summary()
