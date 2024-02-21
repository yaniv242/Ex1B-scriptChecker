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
        #expected_results 
        # Print summary for a student
        print(f"Summary for {self.student_dir}:")
        print(f"Grade: {self.grade}")
        print("Total Compilation Errors:" if self.compilation_errors else "No Compilation Errors")
        print("Actual Compilation Errors:" if self.compilation_errors else "No Compilation Errors")
        for error in self.compilation_errors:
            print(error)
        print("Total Warnings:" if self.warning_messages else "No Warnings")
        print("Actual Warnings:" if self.warning_messages else "No Warnings")
        for warning in self.warning_messages:
            print(warning)
        print("Test Results:")
        for command, result in self.test_results:
            print(f"{command}: {'Pass' if result else 'Fail'}")

    def run_test(self, test):
        try:
            executable_path = os.path.abspath(os.path.join(self.student_dir, "ex1b.exe"))
            output, stderr = "", ""
            command_attempts = [("exit", 1), ("./exit", 1)]

            for exit_cmd, timeout_duration in command_attempts:
                process = subprocess.Popen([executable_path], cwd=self.student_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                input_command = f"{test['command']}\n{exit_cmd}\n"
                try:
                    out, err = process.communicate(input=input_command, timeout=timeout_duration)
                    output += out
                    stderr += err
                    if len(output) > 1024:
                        output = output[:1024] + "\n... [output truncated]"
                        break
                except subprocess.TimeoutExpired:
                    self.log_to_file(f"Timeout expired with '{exit_cmd}', process killed.\n")
                    self.catched_errors.append(f"Timeout expired with '{exit_cmd}', process killed.\n")
                    process.kill()
                    out, err = process.communicate()
                    output += out
                    stderr += err
                finally:
                    process.terminate()

                if not process.poll():
                    break

            self.log_to_file(f"Final Command Output:\n{output}\n")
            if stderr:
                self.log_to_file(f"Errors from stderr:\n{stderr}\n")
                self.catched_errors.append(f"Errors from stderr: \n{stderr}\n")
            actual_output = "error running test" if not output else output.strip()
            self.test_results.append((test['command'], test['expected'] in actual_output))

        except Exception as e:
            self.log_to_file(f"Error running test '{test['command']}': {e}\n")
            self.catched_errors.append(f"Error running test '{test['command']}': {e}\n")

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