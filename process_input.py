import os
import re
import pymupdf
import ast
from operator import itemgetter
from openai import OpenAI

def extract_text(file_path: str):
    """Extracts text from the PDF file and returns it as a string"""
    document = pymupdf.open(file_path)
    text = ""
            
    for page in document:
        text += page.get_text()
    
    return text

def patient_information(file_path: str, text: str):
    """Extract patient and specimen information from provided text"""

    patient_info = {'Patient Name': '', 'Date of Birth': '', 'Gender': '', 'MRN': '', 'Lab No.': '', 'Accession No.': '', 'Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': ''}

    start = text.find('PATIENT NAME')
    if start == -1:
        validate_input(patient_info, file_path, no_start=True)
        return patient_info
        

    text = text[start:]
    lines = text.splitlines()
    lines = [line for line in lines if len(line.strip()) > 1] ##remove empty or short lines

    index = len(lines)
    for i, s in enumerate(lines):
        if "pathogenic mutations" in s.lower():
            index = i
            break

    lines = lines[:index]

    i = 1 ##skipping lines[0] as that contains PATIENT NAME

    while lines[i].endswith(':'):
        i += 1
    
    info = lines[i] ## name, date of birth, gender
    
    name_pattern = r"^([A-Za-z\s'-]+)"
    name_match = re.search(name_pattern, info)
    if name_match:
        patient_info['Patient Name'] = name_match.group(1).strip()

    date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
    date_match = re.search(date_pattern, info)
    if date_match:
        patient_info['Date of Birth'] = date_match.group(1)


    gender_pattern = r"(\w{4,6})$"
    gender_match = re.search(gender_pattern, info)
    if gender_match:
        patient_info['Gender'] = gender_match.group(1)

    i += 1
    while lines[i].endswith(':'):
        i += 1            

    info = lines[i] ## MRN, Lab No., Accession No.

    mrn_pattern = r"^(\d+)"
    mrn_match = re.search(mrn_pattern, info)
    if mrn_match:
        patient_info['MRN'] = mrn_match.group(1).strip()

    lab_no_pattern = r"([A-Za-z]\d+)"
    lab_no_match = re.search(lab_no_pattern, info)
    if lab_no_match:
        patient_info['Lab No.'] = lab_no_match.group(1).strip()

    accession_no_pattern = r"(MDI(\s*\d+)+)$"
    accession_no_match = re.search(accession_no_pattern, info)
    if accession_no_match:
        patient_info['Accession No.'] = accession_no_match.group(1).strip()
    
    lines = lines[i+1:] ## removing data that has already been extracted

    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    model="gpt-4o-mini"

    for attempt in range(2): # two attempts for OpenAI API to return a proper dictionary
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
        except Exception as e:  
            if attempt == 1:  
                validate_input(patient_info, file_path, error = e)
    
    return patient_info

    

def validate_input(patient_info: dict, file_path: str, no_start = False, error = None):

    if no_start:
        print(f"{file_path} does not contain the proper information; could not find patient information")
        patient_info['File Name'] = file_path
        return False
    
    if error:
        print(f'Error with specimen information: {error}')
        patient_info['File Name'] = file_path
        return False
    
    ## checking if any of the patients' required information is missing
    check_patient_info = itemgetter('Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Physician', 'Date Received', 'Date Reported')
    result = check_patient_info(patient_info)

    if "" in result:
        print(f"Patient from file {file_path} missing required information")
        patient_info['File Name'] = file_path
        return False
    
    return True