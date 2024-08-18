import os
import re
import pymupdf
import csv
import ast
from operator import itemgetter
from get_directories import get_input_directory, get_output_file, input_directory_path, output_file_path
from openai import OpenAI

def patient_information(input_directory_path):
    """Extract patient and specimen information from all files in directory"""

    data = [] ## patients' data will be stored here
    incomplete = [] ## patients' data with missing info will be stored here

    files = os.listdir(input_directory_path)

    for file in files:
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(input_directory_path, file)

            document = pymupdf.open(file_path)
            text = ""
            
            for page in document:
                text += page.get_text()

            patient_info = {'Patient Name': '', 'Date of Birth': '', 'Gender': '', 'MRN': '', 'Lab No.': '', 'Accession No.': '', 'Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': ''}

            start = text.find('PATIENT NAME')
            if start == -1:
                print(f"{file_path} does not contain the proper information; could not find patient information")
                patient_info['File Name'] = file
                incomplete.append(patient_info)
                continue

            text = text[start:]
            lines = text.splitlines()
            lines = [line for line in lines if len(line.strip()) > 1] ##remove empty or short lines

            index = len(lines)
            for i, s in enumerate(lines):
                if "pathogenic mutations" in s.lower():
                    index = i
                    break

            lines = lines[:index]

            print(lines)

            i = 1 ##skipping lines[0] as that contains PATIENT NAME

            while lines[i].endswith(':'):
                i += 1
            
            info = lines[i] ## name, date of birth, gender
            
            name_pattern = r"^([A-Za-z\s'-]+)"
            name_match = re.search(name_pattern, info)
            if name_match:
                patient_info['Patient Name'] = name_match.group(1).strip()
            else:
                print(f"Failed to extract 'Patient Name' from {file_path}")

            date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
            date_match = re.search(date_pattern, info)
            if date_match:
                patient_info['Date of Birth'] = date_match.group(1)
            else:
                print(f"Failed to extract 'Date of Birth' from {file_path}")


            gender_pattern = r"(\w{4,6})$"
            gender_match = re.search(gender_pattern, info)
            if gender_match:
                patient_info['Gender'] = gender_match.group(1)
            else:
                print(f"Failed to extract 'Gender' from {file_path}")

            i += 1
            while lines[i].endswith(':'):
                i += 1            

            info = lines[i] ## MRN, Lab No., Accession No.

            mrn_pattern = r"^(\d+)"
            mrn_match = re.search(mrn_pattern, info)
            if mrn_match:
                patient_info['MRN'] = mrn_match.group(1).strip()
            else:
                print(f"Failed to extract 'MRN' from {file_path}")

            lab_no_pattern = r"([A-Za-z]\d+)"
            lab_no_match = re.search(lab_no_pattern, info)
            if lab_no_match:
                patient_info['Lab No.'] = lab_no_match.group(1).strip()
            else:
                print(f"Failed to extract 'Lab No.' from {file_path}")

            accession_no_pattern = r"(MDI(\s*\d+)+)$"
            accession_no_match = re.search(accession_no_pattern, info)
            if accession_no_match:
                patient_info['Accession No.'] = accession_no_match.group(1).strip()
            else:
                print(f"Failed to extract 'Accession No.' from {file_path}")
            
            lines = lines[i+1:] ## removing data that has already been extracted

            client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

            model="gpt-4o-mini"

            for attempt in range(2):
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Add the values to the following python dictionary using the provided text\
                        {'Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': ''}\
                        return just the dictionary with no formatting"},
                        {"role": "user", "content": "\n".join(lines)}
                    ]
                )

                try:
                    specimen_info = ast.literal_eval(response.choices[0].message.content)
                    patient_info.update(specimen_info)
                    break  
                except:  
                    if attempt == 1:  
                        print(f'Failed to extract information from line in {file_path}: {lines}')
        
            ## checking if any of the patients' required information is missing
            check_patient_info = itemgetter('Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Physician', 'Date Received', 'Date Reported')
            result = check_patient_info(patient_info)


            if "" in result:
                print(f"Patient from file {file_path} missing required information")
                patient_info['File Name'] = file
                incomplete.append(patient_info)
                continue
            else:
                data.append(patient_info)

    return data, incomplete

##TODO: convert to xlsx
def process_output(output_file_path, data: list):
    file_exists = os.path.exists(output_file_path)

    with open(output_file_path, 'a', newline='') as output_file:
        
        fieldnames = ['Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Tissue Origin', 'Physician', 'Date Received', 'Date Reported']
        
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)

def process_errors(output_file_path, data: list):
    file_exists = os.path.exists(output_file_path)

    with open(output_file_path, 'a', newline='') as output_file:
        
        fieldnames = ['File Name','Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Tissue Origin', 'Physician', 'Date Received', 'Date Reported']
        
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)

if __name__ == "__main__":
    input_directory_path = get_input_directory()
    output_file_path = get_output_file()
    data, incomplete = patient_information(input_directory_path)
    process_output(output_file_path, data)
    process_errors(output_file_path, incomplete)
