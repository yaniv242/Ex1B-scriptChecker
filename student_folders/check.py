import os
import subprocess






# Test commands and their expected outputs
tests = [
    {"command": "./str_str aa aabaa", "expected": "2"},
    {"command": "./max aa aaa aaaa", "expected": "aaaa 4"},
    {"command": "./count aa aabaa", "expected": "4"},
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



def compile_programs(student_path, log_file):
    for program in ['ex1b', 'str_str', 'count', 'max', 'shell']:
        source_file = os.path.join(student_path, f"{program}.c")
        # Check if the source file exists before attempting to compile
        if os.path.exists(source_file):
            try:
                if program == 'shell':
                    exe_path = os.path.join(student_path, "ex1b")
                else:
                    exe_path =  os.path.join(student_path, program)    
                result = subprocess.run(["gcc", source_file, "-o",exe_path], capture_output=True, text=True)
                if result.returncode == 0 and result.stderr:
                    log_file.write(f"Compilation warning in {program}:\n{result.stderr}\n\n")
                elif result.returncode != 0:
                    log_file.write(f"Compilation error in {program}:\n{result.stderr}\n\n")
                    return False
            except Exception as e:
                log_file.write(f"Error compiling {program}: {e}\n\n")
                return False
        else:
            log_file.write(f"Source file not found for {program}\n\n")
            # Decide if you want to return False or continue trying to compile other programs
            # return False  # Uncomment if you want to stop compilation process for this student upon missing a file
    return True
def run_test(student_path, test, log_file):
    try:
        print('before popen')
        executable_path = os.path.abspath(os.path.join(student_path, "ex1b.exe"))
        output, stderr = "", ""
        command_attempts = [("exit", 1), ("./exit", 1)]  # List of exit commands and timeouts

        for exit_cmd, timeout_duration in command_attempts:
            process = subprocess.Popen([executable_path], cwd=student_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"ex1b.exe process started with PID {process.pid}")
            log_file.write(f"\n---\nExecuting command: {test['command']}\n")
            
            input_command = f"{test['command']}\n{exit_cmd}\n"
            try:
                out, err = process.communicate(input=input_command, timeout=timeout_duration)
                output += out
                if len(output) > 1024:  # Limit output capture to 1KB to prevent huge log files
                    output = output[:1024] + "\n... [output truncated]"
                    break  # Stop further attempts if output is too large
                stderr += err
            except subprocess.TimeoutExpired:
                log_file.write(f"Timeout expired with '{exit_cmd}', process killed.\n")
                process.kill()
                out, err = process.communicate()
                output += out
                stderr += err
            finally:
                process.terminate()  # Ensure the process is terminated

            if not process.poll():  # Check if the process has terminated
                break  # Exit the loop if the process has exited

        # Log the outputs
        log_file.write(f"Final Command Output:\n{output}\n")
        if stderr:
            log_file.write(f"Errors:\n{stderr}\n")

        # Check if the actual output matches expected
        actual_output = "error running test" if not output else output.strip()
        log_file.write(f"Test command: {test['command']}\nExpected output: {test['expected']}\nActual output: {actual_output}\n")
        result = "Pass" if test['expected'] in actual_output else "Fail"
        log_file.write(f"Result: {result}\n---\n")

        return actual_output

    except Exception as e:
        log_file.write(f"Error running test '{test['command']}': {e}\n\n")
        return "error running test"







def log_test_results(log_file, test, test_output, scores, student_dir):
    log_file.write(f"Test command: {test['command']}\n")
    log_file.write(f"Expected output: {test['expected']}\n")
    log_file.write(f"Actual output: {test_output}\n")
    test_passed = test['expected'] in test_output
    log_file.write("Result: " + ("Pass" if test_passed else "Fail") + "\n\n")

    if not test_passed:
        scores[student_dir] -= 7  # Deduct 7 points for each failed test

main_dir = os.getcwd()
extraction_summary_log_path = os.path.join(main_dir, "extraction_summary.log")
extraction_penalties = read_extraction_penalties(extraction_summary_log_path)
scores = {}

for student_dir in os.listdir(main_dir):
    student_path = os.path.join(main_dir, student_dir)
    if not os.path.isdir(student_path): continue

    initial_score = 100 - extraction_penalties.get(student_dir, 0)
    scores[student_dir] = initial_score

    print(f"Processing: {student_dir}")

    with open(os.path.join(student_path, "test_results.log"), 'w') as log_file:
        log_file.write(f"Checking {student_dir}...\n\n")

        if compile_programs(student_path, log_file):
            print(f"Compilation successful for {student_dir}")
            for test_dict in tests:
                print(f"Running test: {test_dict['command']} for {student_dir}")
                if not run_test(student_path, test_dict, log_file):
                    scores[student_dir] -= 7  # Deduct points for failed test
        else:
            scores[student_dir] -= 20
            print(f"Compilation errors for {student_dir}")

     

 



with open(os.path.join(main_dir, "final_scores.log"), 'w') as score_log:
    for student, score in scores.items():
        score_log.write(f"{student}: {score} points\n")

print("Checking complete. Results are logged in each student's directory.")
