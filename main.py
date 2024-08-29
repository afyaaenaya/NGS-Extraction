import os
from get_directories import get_input_directory, get_output_file, input_directory_path, output_file_path
from process_input import extract_text, patient_information, validate_input
from process_output import process_output, process_errors
from OCR import ocr_file
from log import get_log, log_processed_file

if __name__ == '__main__':
    input_directory_path = get_input_directory()
    output_file_path = get_output_file()
    
    processed_files = get_log()

    files = os.listdir(input_directory_path)
    for file in files:
        file_path = os.path.abspath(os.path.join(input_directory_path, file))
        if (file.lower().endswith(".pdf")) and (file_path not in processed_files):
            print(f'Processing {file}')

            print(f'Started OCR of {file}...')
            ocr_file(file_path)
            print(f'Completed OCR of {file}')

            print(f'Extracting text from {file}')
            text = extract_text(file_path)
            print(f'Extracted text from {file}')

            print(f'Extracting patient information from {file}')
            patient_info = patient_information(file_path, text)
            print(f'Extracted patient information from {file}')

            if validate_input(patient_info, file_path):
                process_output(output_file_path, patient_info)
                log_processed_file(file_path)
            else:
                process_errors(output_file_path, patient_info)
                log_processed_file(file_path)
            print(f'Data from {file} added to {output_file_path}')

            print(f'Done processing {file}')