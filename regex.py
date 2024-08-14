import os
import re
import pymupdf
import csv
from get_directories import get_input_directory, get_output_file, input_directory_path, output_file_path


def patient_information(input_directory_path):

    data = []

    files = os.listdir(input_directory_path)

    for file in files:
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(input_directory_path, file)

            document = pymupdf.open(file_path)
            text = ""
            
            for page in document:
                text += page.get_text()

            patient_data = {'Patient Name': '', 'Date of Birth': '', 'Gender': '', 'MRN': '', 'Lab No.': '', 'Accession No.': '', 'Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': ''}

            text = text[text.find('PATIENT NAME'):]
            lines = text.splitlines()

            info1 = lines[1] ## name, date of birth, gender
            print(info1)
            pattern1 = r"^(.*?)(\d{2}/\d{2}/\d{4})(.*)$"

            match1 = re.match(pattern1, info1)

            if match1:
                name = match1.group(1)
                patient_data['Patient Name'] = name

                birth = match1.group(2)
                patient_data['Date of Birth'] = birth

                gender = match1.group(3)
                patient_data['Gender'] = gender
            else:
                print(f'Name, date of birth, and gender of {file_path} can not be identified ')

            info2 = lines[3] ## MRN, Lab No., Accession No.
            print(info2)
            pattern2 = r"^(\d+)\s+(M\w\d+)\s+(.*)$"

            match2 = re.match(pattern2, info2)

            if match2:
                mrn = match2.group(1)
                patient_data['MRN'] = mrn

                lab_no = match2.group(2)
                patient_data['Lab No.'] = lab_no

                accession_no = match2.group(3)
                patient_data['Accession No.'] = accession_no
            else:
                print(f'MRN, lab no., and accession no. of {file_path} can not be identified')

            data.append(patient_data)

    return data

def process_output(output_file_path, data: list):
    file_exists = os.path.exists(output_file_path)

    with open(output_file_path, 'a', newline='') as output_file:
        
        fieldnames = ['Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Tissue Origin', 'Physician', 'Date Received', 'Date Reported', 'Pathogenic Mutations', 'Variants of Unknown Significance']
        
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)

if __name__ == "__main__":
    input_directory_path = get_input_directory()
    output_file_path = get_output_file()
    data = patient_information(input_directory_path)
    process_output(output_file_path, data)
