import os
import subprocess


class Student:
    def __init__(self, student_dir):
        
        self.student_dir = student_dir
        self.compilation_errors = []
        self.warning_messages = []
        self.test_results = []
        self.grade = 100  # Starting grade, adjust based on errors and warnings
        self.extraction_penalty = 0  # Adjust based on extraction summary log
        self.catched_errors = []
        self.readme_content = self.read_readme()

    def read_readme(self):
        # Look for README or README.txt in the student's directory
        readme_files = [file for file in os.listdir(self.student_dir) if file.lower().startswith('readme')]
        readme_content = []
        if readme_files:
            readme_path = os.path.join(self.student_dir, readme_files[0])  # Consider the first README file found
            try:
                with open(readme_path, 'r') as readme_file:
                    # Read the first 5 lines from the README file
                    for _ in range(5):
                        line = readme_file.readline()
                        if not line:  # Stop if the file has less than 5 lines
                            break
                        readme_content.append(line.strip())
            except Exception as e:
                readme_content.append(f"Error reading README: {e}")
        return readme_content

    def compile_program(self, program):
        source_file = os.path.join(self.student_dir, f"{program}.c")
        exe_file = os.path.join(self.student_dir, program)
 
        if os.path.exists(source_file):
            result = subprocess.run(["gcc", source_file, "-o", exe_file], capture_output=True, text=True)
            if result.returncode != 0:
                self.compilation_errors.append(result.stderr)
                self.grade -= 40  # Deduct points for compilation error
            elif result.stderr:
                self.warning_messages.append(result.stderr)
                self.grade -= 7  # Deduct points for warnings
        else:
            self.compilation_errors.append(f"Source file {program}.c not found.")
            self.grade -= 5  # Deduct points for missing file

    def summarize(self):
        summary = f"Summary for {self.student_dir}:\n"
        summary += f"Grade: {self.grade - self.extraction_penalty}\n"
        if self.readme_content:
            summary += "README Content:\n"
            summary += "\n".join(self.readme_content) + "\n\n"
        else:
            summary += "No README Content Found\n\n"    
        summary += "Compilation Errors:\n"
        if self.compilation_errors:
            for error in self.compilation_errors:
                summary += f"- {error}\n"
        else:
            summary += "No Compilation Errors\n"

        summary += "Warnings:\n"
        if self.warning_messages:
            for warning in self.warning_messages:
                summary += f"- {warning}\n"
        else:
            summary += "No Warnings\n"

        summary += "Test Results:\n"
        for command, actual, expected in self.test_results:
            result = "Pass" if expected in actual else "Fail"
            summary += f"Command: {command}\nExpected: {expected}\nActual: {actual}\nResult: {result}\n\n"

        summary += f"Extraction Penalty: {self.extraction_penalty}\n"
        summary += f"Final Grade: {self.grade - self.extraction_penalty}\n"

        return summary

    def run_test(self, test):
        max_output_size = 1024  # Limit the output size to 1KB

        for exit_cmd, timeout_duration in [("exit", 1), ("./exit", 1)]:
            try:
                process = subprocess.Popen(
                    [os.path.join(self.student_dir, "ex1b.exe")],
                    cwd=self.student_dir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Send the test command followed by an exit command
                test_input = f"{test['command']}\n{exit_cmd}\n"
                stdout, stderr = process.communicate(input=test_input, timeout=timeout_duration)

                # Truncate the output if it exceeds the maximum allowed size
                if len(stdout) > max_output_size:
                    stdout = stdout[:max_output_size] + "\n... [output truncated]"

                self.log_test_result(test, stdout, stderr)

            except subprocess.TimeoutExpired:
                # Handle the case where the process did not terminate within the timeout
                process.kill()
                stdout, stderr = process.communicate()
                self.log_to_file(f"Timeout expired with '{exit_cmd}', process killed.\n")
                self.catched_errors.append(f"Timeout expired with '{exit_cmd}', process killed.\n")

            except Exception as e:
                self.log_to_file(f"Error running test '{test['command']}': {e}\n")
                self.catched_errors.append(f"Error running test '{test['command']}': {e}\n")

    def log_test_result(self, test, stdout, stderr):
        # Log the output and stderr to the test result log
        self.log_to_file(f"Test command: {test['command']}\n")
        self.log_to_file(f"Output:\n{stdout}\n")
        if stderr:
            self.log_to_file(f"Errors:\n{stderr}\n")

        # Determine the test result and append the command, actual output, and expected output
        test_passed = test['expected'] in stdout
        actual_output = stdout.strip()  # Clean the actual output
        self.test_results.append((test['command'], actual_output, test['expected']))
        result_str = "Pass" if test_passed else "Fail"
        if not test_passed:
            self.grade -= 5
        self.log_to_file(f"Result: {result_str}\n")



    def log_to_file(self, message):
        with open(os.path.join(self.student_dir, "test_results.log"), 'a') as log_file:
            log_file.write(message + "\n")   





  
# Test commands and their expected outputs
tests = [
    {"command": "./str_str aa aabaa", "expected": "2"},
    {"command": "./max aa aaa aaaa", "expected": "aaaa 4"},
    {"command": "./count aa aabaa", "expected": "2"},
    {"command": "bad command", "expected": "error"},
]

def read_extraction_penalties(summary_log_path):
    penalties = {}
    with open(summary_log_path, 'r', encoding='utf-8') as f:
        content = f.read().split('\n\n')
        for block in content:
            lines = block.split('\n')
            if lines[0].startswith("Logs for "):
                student_name = lines[0][9:-1]  # Remove "Logs for " and trailing colon
                score_line = lines[-1]
                score = int(score_line.split(': ')[-1].split(' ')[0])
                penalties[student_name] = 100 - score  # Calculate penalty
    return penalties

# Main script
main_dir = os.getcwd()
extraction_summary_log_path = os.path.join(main_dir, "extraction_summary.log")
extraction_penalties = read_extraction_penalties(extraction_summary_log_path)

students = []  # List to hold Student objects

final_summary_file_path = os.path.join(main_dir, "final_summary.log")
with open(final_summary_file_path, 'w') as final_summary_file:
    for student_dir in os.listdir(main_dir):
        student_path = os.path.join(main_dir, student_dir)
        if not os.path.isdir(student_path): continue

        # Create a Student object for each directory
        student = Student(student_dir)
        student.extraction_penalty = extraction_penalties.get(student_dir, 0)  # Set extraction penalty if any
        students.append(student)

        print(f"Processing: {student_dir}")

        # Compile programs for the student
        for program in ['ex1b', 'str_str', 'count', 'max']:
            student.compile_program(program)

        # Run tests for the student
        for test in tests:
            student.run_test(test)

        # Summarize the results for the student
        student_summary = student.summarize()
        final_summary_file.write(student_summary)
        final_summary_file.write("\n" + "="*40 + "\n\n") 