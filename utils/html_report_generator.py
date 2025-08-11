import os
import re
import json
import logging
from contextlib import contextmanager
from datetime import datetime
import threading as _threading

# Step logging state
_step_log_state = {
    'current_testcase': None,
    'current_step': None,
    'testcases': {},  # testcase_id: {steps: [step dicts], description: str}
    'lock': _threading.Lock()
}

# Start a new test case
def start_testcase(testcase_id, testcase_description=None):
    with _step_log_state['lock']:
        _step_log_state['current_testcase'] = testcase_id
        _step_log_state['testcases'][testcase_id] = {
            'steps': [],
            'description': testcase_description
        }

# End the current test case
def end_testcase(testcase_id):
    with _step_log_state['lock']:
        _step_log_state['current_testcase'] = None

# Get the current test case ID
@contextmanager
def log_step(keyword):
    testcase_id = _step_log_state['current_testcase']
    start_time = datetime.now()
    step = {
        'keyword': keyword,
        'start': start_time,
        'end': None,
        'status': None,
        'logs': []
    }
    with _step_log_state['lock']:
        _step_log_state['current_step'] = step
        _step_log_state['testcases'][testcase_id]['steps'].append(step)
    try:
        yield
        step['status'] = 'PASS'
    except Exception:
        step['status'] = 'FAIL'
        raise
    finally:
        step['end'] = datetime.now()
        with _step_log_state['lock']:
            _step_log_state['current_step'] = None

# Log a message to the current step
def log_to_step(msg):
    with _step_log_state['lock']:
        step = _step_log_state['current_step']
        if step:
            step['logs'].append(msg)


class HTMLReportGenerator:
    """
    Handles HTML report generation for automation test results.
    Generates unified HTML reports with collapsible sections for test cases and steps.
    """
    
    def __init__(self, report_dir, step_log_state):
        """
        Initialize HTML report generator.
        
        Args:
            report_dir (str): Directory where HTML report will be saved
            step_log_state (dict): Global step logging state containing test case data
        """
        self.report_dir = report_dir
        self.step_log_state = step_log_state
        self.html_file = os.path.join(report_dir, "Automation.html")
        self.encoding = "utf-8"
        
    def _initialize_html_template(self):
        """Initialize HTML file with template content if it doesn't exist."""
        if not os.path.exists(self.html_file):
            template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Config/Automation.html")
            if os.path.exists(template_path):
                with open(template_path, "r", encoding=self.encoding) as tf:
                    template_content = tf.read()
                with open(self.html_file, "w", encoding=self.encoding) as f:
                    f.write(template_content)
            else:
                raise FileNotFoundError(f"HTML Template file not found: {template_path}")
    

    #  Helper function to calculate elapsed time between two timestamps.
    def _get_elapsed_time(self, start_time, end_time):
        """
        Calculate elapsed time between two datetime objects or strings.
        
        Args:
            start_time: Start time (datetime object or string)
            end_time: End time (datetime object or string)
            
        Returns:
            str: Formatted elapsed time string
        """
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

    #  Write the summary section with total, pass, fail, and elapsed time.
    def _write_summary_section(self, f, automation_summary):
        """Write the summary information section to HTML file."""
        total = automation_summary.get('total', 0)
        passed = automation_summary.get('passed', 0)
        failed = automation_summary.get('failed', 0)
        total_time = automation_summary.get('total_time', 0.0)
        
        f.write(f'''
            <div class="heading">
                <h2>Summary Information</h2>
            </div>
            <table class="equal-cols">
                <thead>
                    <tr>
                        <th>Total</th>
                        <th>Pass</th>
                        <th>Fail</th>
                        <th>Time Elapsed</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{total}</td>
                        <td class="pass">{passed}</td>
                        <td class="fail">{failed}</td>
                        <td>{total_time:.2f}s</td>
                    </tr>
                </tbody>
            </table>
        ''')

    # Write the test statistics section with test IDs, descriptions, results, and execution times.
    def _write_statistics_section(self, f, runner=None):
        """Write the test statistics section to HTML file."""
        f.write('''
            <div class="heading">
                <h2>Test Statistics</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width:1%">Test ID</th>
                        <th>Description</th>
                        <th style="width:1%">Result</th>
                        <th style="width:1%">Execution Time (s)</th>
                    </tr>
                </thead>
                <tbody>
        ''')
        
        # Write test statistics from the runner if available
        if runner and hasattr(runner, 'test_results'):
            for test_id, result, exec_time in runner.test_results:
                status_class = 'pass' if result == 'PASS' else 'fail'
                # Get description from step_log_state if available
                description = ''
                tcdata = self.step_log_state['testcases'].get(test_id, {})
                description = tcdata.get('description', '') if tcdata else ''
                # Make Test ID an anchor link to the testcase log section
                anchor_id = f'testcase-{test_id}'
                anchor_html = f'<a href="#{anchor_id}" class="testcase-link" onmouseover="this.style.textDecoration=\'underline\'" onmouseout="this.style.textDecoration=\'none\'"">{test_id}</a>'
                f.write(f'''<tr>
                        <td>{anchor_html}</td>
                        <td>{description}</td>
                        <td class="{status_class}">{result}</td>
                        <td>{exec_time}</td>
                        </tr>''')
        
        f.write('''
                </tbody>
            </table>
        ''')

    # Write the test logs section with collapsible test cases and steps.
    def _write_test_logs_section(self, f):
        """Write the test logs section with collapsible test cases and steps."""
        f.write('''
            <div class="heading">
                <h2>Test Logs</h2>
            </div>
            <div class="collapsible-container">
        ''')
        
        for testcase_id, tcdata in self.step_log_state['testcases'].items():
            description = tcdata.get('description', '')
            steps = tcdata.get('steps', [])
            
            # Determine testcase status based on step statuses
            if steps and all(step.get('status') == 'PASS' for step in steps):
                testcase_status_class = 'pass'
                test_result = 'PASS'
            else:
                testcase_status_class = 'fail'
                test_result = 'FAIL'
            
            anchor_id = f'testcase-{testcase_id}'
            f.write(f'''<div class="collapsible" id="{anchor_id}">
                    <div class="header">
                        <span class="arrow">▶</span>
                        <span class="title">
                            Testcase: {testcase_id} - {description} 
                            <span class="chip {testcase_status_class}">{test_result}</span>
                        </span>
                    </div>
                    <div class="content">\n''')
            
            # Write steps for this testcase
            for step in steps:
                self._write_step_section(f, step)
            
            f.write('</div></div>\n')
        
        f.write('</div>')

    # Write individual step section with logs.
    def _write_step_section(self, f, step):
        """Write individual step section with logs."""
        status_class = 'pass' if step['status'] == 'PASS' else 'fail'
        f.write(f'''<div class="collapsible">
                <div class="header">
                    <span class="arrow">▶</span>
                    <span class="title">
                        {step["keyword"]}
                        <span class="chip {status_class}">{step['status']}</span>
                    </span>
                </div>\n''')
        
        total_time = self._get_elapsed_time(step['start'], step['end'])
        f.write(f'''<div class="content">
                <p>Execution Time: {total_time}</p>
                <div class="logs">\n''')
        
        # Write logs for this step
        for log in step['logs']:
            self._write_log_entry(f, log)
        
        f.write('</div></div></div>\n')

    # Write individual log entry with time, level, and message.
    def _write_log_entry(self, f, log):
        """Parse and write individual log entry."""
        logEntryPattern = r"^(?P<time>[\d\-:\, ]+) - (?P<level>[A-Z]+) - (?P<message>.*)$"
        match = re.match(logEntryPattern, log)
        
        if match:
            time = match.group("time")
            level = match.group("level")
            message = match.group("message")
            f.write(f'''<div>
                    <span class="time">{time}</span>
                    <span class="level {level}">{level}</span>
                    {message}
                </div>\n''')
        else:
            # If log doesn't match pattern, write as is
            f.write(f'<div>{log}</div>\n')

    # Write JavaScript for collapsible functionality and close HTML.
    def _write_javascript_and_closing(self, f):
        """Write JavaScript for collapsible functionality and close HTML."""
        f.write('''
            <script>
                document.querySelectorAll(".header").forEach(header => {
                    header.addEventListener("click", (e) => {
                        if (e.target.classList.contains("chip")) return;
                        const content = header.nextElementSibling;
                        header.classList.toggle("active");
                        content.style.display = content.style.display === "block" ? "none" : "block";
                    });
                });
                
                document.querySelectorAll(".testcase-link").forEach(link => {
                    link.addEventListener("click", function(e) {
                        e.preventDefault();
                        var anchorId = this.getAttribute("href").substring(1);
                        var tcDiv = document.getElementById(anchorId);
                        if (tcDiv) {
                            // Collapse all other test case sections
                            document.querySelectorAll(".collapsible").forEach(div => {
                                var header = div.querySelector(".header");
                                var content = header.nextElementSibling;
                                header.classList.remove("active");
                                content.style.display = "none";
                            });
                            // Expand the clicked test case section
                            var header = tcDiv.querySelector(".header");
                            var content = header.nextElementSibling;
                            header.classList.add("active");
                            content.style.display = "block";
                            // Scroll to the test case section
                            tcDiv.scrollIntoView({behavior: "smooth", block: "start"});
                        }
                    });
                });
            </script>
            </body>
        </html>
        ''')

    # Generate complete HTML report with summary, statistics, and logs.
    def generate_html_report(self, automation_summary, runner=None):
        """
        Generate complete HTML report.
        
        Args:
            automation_summary (dict): Summary statistics for the test run
            runner: TestRunner instance containing test results
        """
        self._initialize_html_template()
        
        with open(self.html_file, "a", encoding=self.encoding) as f:
            self._write_summary_section(f, automation_summary)
            self._write_statistics_section(f, runner)
            self._write_test_logs_section(f)
            self._write_javascript_and_closing(f)


# Custom logging handler that integrates with HTMLReportGenerator.
class UnifiedHtmlHandler(logging.Handler):
    """
    Custom logging handler that integrates with HTMLReportGenerator.
    Buffers logs during execution and generates HTML report on close.
    """
    
    # UnifiedHtmlHandler constructor initializes the HTML handler.
    def __init__(self, filename, step_log_state):
        """
        Initialize the HTML handler.
        
        Args:
            filename (str): Path to HTML file
            step_log_state (dict): Global step logging state
        """
        super().__init__()
        self.filename = filename
        self.step_log_state = step_log_state
        self.encoding = "utf-8"
        
        # Initialize HTML template if file doesn't exist
        report_dir = os.path.dirname(filename)
        self.html_generator = HTMLReportGenerator(report_dir, step_log_state)
        self.html_generator._initialize_html_template()

    # Emit method handles log records and buffers them in step logs.
    def emit(self, record):
        """
        Handle log record by buffering it in step logs.
        
        Args:
            record: LogRecord instance
        """
        msg = self.format(record)
        self._log_to_step(msg)

    # Log message to the current step's logs in step_log_state.
    def _log_to_step(self, msg):
        """Add log message to current step's logs."""
        with self.step_log_state['lock']:
            step = self.step_log_state['current_step']
            if step:
                step['logs'].append(msg)

    # Close method generates the final HTML report when the handler is closed.
    def close(self):
        """Generate final HTML report when handler is closed."""
        # Get automation summary from global variable
        try:
            from .utility import _automation_summary
            automation_summary = _automation_summary
        except ImportError:
            # Fallback if import fails
            automation_summary = {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'total_time': 0.0
            }
        
        # Get runner instance if available
        runner = None
        try:
            import __main__
            runner = getattr(__main__, 'runner', None)
        except Exception:
            runner = None
        
        # Generate the HTML report
        self.html_generator.generate_html_report(automation_summary, runner)
        super().close()

# Factory function to create UnifiedHtmlHandler instance.
def create_html_handler(filename):
    """
    Factory function to create UnifiedHtmlHandler instance.
    
    Args:
        filename (str): Path to HTML file
        step_log_state (dict): Global step logging state
        
    Returns:
        UnifiedHtmlHandler: Configured HTML handler instance
    """ 
    return UnifiedHtmlHandler(filename, _step_log_state)