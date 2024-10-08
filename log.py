import os

def get_log():
    log_path = os.path.join(os.getcwd(), 'log.txt')
    if not os.path.exists(log_path):
        with open(log_path, 'w') as log:
            pass # creates an empty log.txt file
        print(f'Created log file at {log_path}')
    else:
        print(f'Using log file from {log_path}')

    with open(log_path, 'r') as log:
        return set(os.path.abspath(line.strip()) for line in log)

def log_processed_file(file_path):
    log_path = os.path.join(os.getcwd(), 'log.txt')
    with open(log_path, 'a') as log:
        log.write(f'{os.path.abspath(file_path)}\n')