import os
import zipfile
import tarfile
import shutil



def handle_extraction_directory(student_path, log_entries):
    contents_after_extraction = os.listdir(student_path)
    # Check for a single new directory that might contain all the extracted contents
    if len(contents_after_extraction) == 1 and os.path.isdir(os.path.join(student_path, contents_after_extraction[0])):
        unwanted_dir = contents_after_extraction[0]
        unwanted_dir_path = os.path.join(student_path, unwanted_dir)
        for item in os.listdir(unwanted_dir_path):
            shutil.move(os.path.join(unwanted_dir_path, item), student_path)
        os.rmdir(unwanted_dir_path)  # Remove the now-empty unwanted directory
        log_entries.append(f"Moved contents from unwanted directory '{unwanted_dir}' to the main directory.")


def unzip_and_extract_student_submissions(main_dir):
    extraction_logs = {}
    scores = {}

    for student_dir in os.listdir(main_dir):
        student_path = os.path.join(main_dir, student_dir)
        if not os.path.isdir(student_path):
            continue

        log_entries = []
        score = 100  # Start with a full score

        for file in os.listdir(student_path):
            file_path = os.path.join(student_path, file)
            if file.endswith('.zip'):
                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(student_path)
                    log_entries.append(f"Extracted and deleted {file}")
                    os.remove(file_path)  # Delete the zip file after extraction
                except zipfile.BadZipFile:
                    log_entries.append(f"Error extracting {file}: Bad zip file")
                    score -= 10
            elif file.endswith('.tgz'):
                try:
                    with tarfile.open(file_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(student_path)
                        log_entries.append(f"TGZ archive found: {file}. Manual extraction required.")
                        score -= 15
                    log_entries.append(f"Extracted and deleted {file}")
                    os.remove(file_path)  # Delete the tgz file after extraction
                    handle_extraction_directory(student_path, log_entries)
                except tarfile.TarError:
                    log_entries.append(f"Error extracting {file}: Bad tgz file")
                    score -= 20
            elif file.endswith('.rar'):
                log_entries.append(f"RAR archive found: {file}. Manual extraction required.")
                score -= 15
            elif file.endswith('.tar'):
                log_entries.append(f"TAR archive found: {file}. Manual extraction required.")
                score -= 15
                # Note: Manual extraction required for .rar files or use an external tool

        extraction_logs[student_dir] = log_entries
        scores[student_dir] = score

    # Return the logs and scores for further processing
    return extraction_logs, scores

def write_summary_log(main_dir, extraction_logs, scores):
    summary_log_path = os.path.join(main_dir, "extraction_summary.log")
    with open(summary_log_path, 'w') as log_file:
        for student, logs in extraction_logs.items():
            log_file.write(f"Logs for {student}:\n")
            for log in logs:
                log_file.write(f" - {log}\n")
            log_file.write(f"Score for {student}: {scores[student]} points\n\n")

# Directory containing all student folders
main_dir = os.getcwd()

# Run the function to unzip and extract submissions, and collect logs and scores
extraction_logs, scores = unzip_and_extract_student_submissions(main_dir)

# Write a summary log file with the extraction logs and scores for all students
write_summary_log(main_dir, extraction_logs, scores)

print(f"Extraction summary log has been written to {os.path.join(main_dir, 'extraction_summary.log')}")
