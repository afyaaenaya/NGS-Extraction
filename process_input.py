import os
import re
import pymupdf
import ast
from operator import itemgetter
from openai import OpenAI

import tempfile
from pdf2image import convert_from_path
from img2table.document import Image
from img2table.ocr import TesseractOCR

def extract_text(file_path: str):
    """Extracts text from the PDF file and returns it as a string"""
    document = pymupdf.open(file_path)
    text = ""
            
    for page in document:
        text += page.get_text()
    
    return text

def patient_information(file_path: str, text: str):
    """Extract patient and specimen information from provided text"""

    patient_info = {'Patient Name': '', 'Date of Birth': '', 'Gender': '', 'MRN': '', 'Lab No.': '', 'Accession No.': '', 'Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': '', 'Mutations': ''}

    start = text.find('PATIENT NAME')
    if start == -1:
        if not alternate_patient_information(file_path, text, patient_info)[0]:
            validate_input(patient_info, file_path, no_start=True)
            return patient_info
        else:
            return alternate_patient_information(file_path, text, patient_info)[1]
    
    # Using table detection to fill in information
    ocr = TesseractOCR()

    with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(file_path, dpi = 200, output_folder=temp_dir, last_page = 1, paths_only = True)
            image = Image(src = images[0])
            extracted_tables = image.extract_tables(ocr=ocr, borderless_tables=True, implicit_rows=True)
            
            if extracted_tables:
                for table in extracted_tables:
                    df = table.df
                    if df.index[df.iloc[:,0].str.contains('PATIENT NAME:', na = False)].tolist():

                        headings1 = df.index[df.iloc[:,0].str.contains('PATIENT NAME:', na = False)].tolist()[0]
                        patient_info['Patient Name'] = df[0][headings1 + 1]
                        patient_info['Date of Birth'] = df[1][headings1 + 1]
                        patient_info['Gender'] = df[2][headings1 + 1]
                    
                    if df.index[df.iloc[:,0].str.contains('MRN:', na = False)].tolist():
                        headings2 = df.index[df.iloc[:,0].str.contains('MRN:', na = False)].tolist()[0]

                        patient_info['MRN'] = df[0][headings2 + 1]
                        patient_info['Lab No.'] = df[1][headings2 + 1]
                        patient_info['Accession No.'] = df[2][headings2 + 1]

                    if df.index[df.iloc[:,0].str.contains('CLINICAL INDICATION:', na = False)].tolist():
                        headings3 = df.index[df.iloc[:,0].str.contains('CLINICAL INDICATION:', na = False)].tolist()[0]
                        patient_info['Clinical Indication'] = df[0][headings3 + 1]
                        patient_info['Type of Specimen'] = df[1][headings3 + 1]
                        patient_info['Tissue Origin'] = df[2][headings3 + 1]

                    if df.index[df.iloc[:,0].str.contains('ORDERING PHYSICIAN:', na = False)].tolist():
                        headings4 = df.index[df.iloc[:,0].str.contains('ORDERING PHYSICIAN:', na = False)].tolist()[0]
                        patient_info['Physician'] = df[0][headings4 + 1]
                        patient_info['Date Received'] = df[1][headings4 + 1]
                        patient_info['Date Reported'] = df[2][headings4 + 1]

    # extracting mutation information
    mutations_info(file_path, patient_info)

    # checking if any necessary information is still empty after extracting info from table
    check_patient_info = itemgetter('Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Physician', 'Date Received', 'Date Reported', 'Mutations')
    result = check_patient_info(patient_info)

    if "" in result: # if empty values, use regex wherever possible
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
        
        if patient_info['Patient Name'] == '':
            name_pattern = r"^([A-Za-z\s'-]+)"
            name_match = re.search(name_pattern, info)
            if name_match:
                patient_info['Patient Name'] = name_match.group(1).strip()
        
        if patient_info['Date of Birth'] == '':
            date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
            date_match = re.search(date_pattern, info)
            if date_match:
                patient_info['Date of Birth'] = date_match.group(1)

        if patient_info['Gender'] == '':
            gender_pattern = r"(\w{4,6})$"
            gender_match = re.search(gender_pattern, info)
            if gender_match:
                patient_info['Gender'] = gender_match.group(1)

        i += 1
        while lines[i].endswith(':'):
            i += 1            

        info = lines[i] ## MRN, Lab No., Accession No.

        if patient_info['MRN'] == '':
            mrn_pattern = r"^(\d+)"
            mrn_match = re.search(mrn_pattern, info)
            if mrn_match:
                patient_info['MRN'] = mrn_match.group(1).strip()

        if patient_info['Lab No.'] == '':
            lab_no_pattern = r"([A-Za-z]{1,2}\d+)"
            lab_no_match = re.search(lab_no_pattern, info)
            if lab_no_match:
                lab_no_match = lab_no_match.group(1).strip()
                # a common error is an "O" appearing after the first letter in the lab no. after the OCR. this removes that "O" if present
                if lab_no_match[1] == ("O" or "o"):
                    lab_no_match = lab_no_match[0] + lab_no_match[2:]

                patient_info['Lab No.'] = lab_no_match

        if patient_info['Accession No.'] == '':
            accession_no_pattern = r"(MDI(\s*\d+)+)$"
            accession_no_match = re.search(accession_no_pattern, info)
            if accession_no_match:
                patient_info['Accession No.'] = accession_no_match.group(1).strip()

    return patient_info


def alternate_patient_information(file_path:str, text: str, patient_info: dict) -> tuple[bool, dict]:
    """
    Extract patient and specimen information from provided text
    Works on 2021 and older PDF template
    """

    start = text.find("Patient's")
    if start == -1:
        return False, patient_info

    # Using table detection to fill in information
    ocr = TesseractOCR()

    with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(file_path, dpi = 200, output_folder=temp_dir, last_page = 1, paths_only = True)
            image = Image(src = images[0])
            extracted_tables = image.extract_tables(ocr=ocr, borderless_tables=False, implicit_rows=False)
            
            if extracted_tables:
                for table in extracted_tables:
                    df = table.df
                    if df[0][0] == "Patient's Name:":
                        patient_info['Patient Name'] = df[1][0].replace('/n', ' ')
                        patient_info['MRN'] = df[5][0]

                        patient_info['Lab No.'] = df[5][1]

                        patient_info['Date of Birth']= df[1][2]
                        patient_info['Gender'] = df[3][2]
                        patient_info['Accession No.'] = df[5][2]

                        patient_info['Clinical Indication'] = df[1][3]
                        patient_info['Physician'] = df[5][3]

                        patient_info['Type of Specimen'] = df[1][4]
                        patient_info['Tissue Origin'] = df[5][4]

                        patient_info['Date Received'] = df[1][5]
                        patient_info['Date Reported'] = df[5][5]

    # checking if any necessary information is still empty after extracting info from table
    check_patient_info = itemgetter('Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Physician', 'Date Received', 'Date Reported')
    result = check_patient_info(patient_info)

    if "" in result: # if empty values, use regex wherever possible
        lines = text.splitlines()
        lines = [line.strip() for line in lines if len(line.strip()) > 1] ##remove empty or short lines

        # trimming the beginning of the file
        index = 0
        for i, s in enumerate(lines):
            if "patient's name" in s.lower():
                index = i - 1 #Patient's name is a line before the heading "Patient's Name"
                break

        lines = lines[index:]

        #trimming after the patient information
        index = len(lines)
        for i, s in enumerate(lines):
            if "pathogenic mutations" in s.lower():
                index = i
                break

        lines = lines[:index]

        i = 0
        info = lines[i] # first and middle name, MRN
        info = info.replace("|", "") #OCR returns | in between table cells. this removes them

        if patient_info['MRN'] == '':
            name_mrn_pattern = r"([A-Z\s'-]+)\s*[^A-Z]*\s*(M\w{2,3}:)\s+(\d+)"
            name_mrn_match = re.search(name_mrn_pattern, info)
            if name_mrn_match:
                patient_info['MRN'] = name_mrn_match.group(3).strip()

        i += 2
        
        info = lines[i] #last name and lab no.
        info = info.replace("|", "")

        if patient_info['Lab No.'] == '':
            name_lab_pattern = r"^([A-Z\s'-]+?)(Lab No:)\s+([A-Za-z]{1,2}\d+)"
            name_lab_match = re.search(name_lab_pattern, info)
            if name_lab_match:
                lab_no_match = name_lab_match.group(3).strip()

                # a common error is an "O" replacing the zero after the first letter in the lab no. after the OCR. this replaces that "O" if present
                if lab_no_match.lower()[1] == "o":
                    lab_no_match = lab_no_match.lower().replace("o", "0", 1).upper()

                patient_info['Lab No.'] = lab_no_match
        
        i += 1
        info = lines[i] #Date of birth, gender, accession no
        info = info.replace("|", "") 

        if patient_info['Date of Birth'] == '':
            date_pattern = r"(Date of Birth:)\s+(\d{1,2}/\d{1,2}/\d{4})"
            date_match = re.search(date_pattern, info)
            if date_match:
                patient_info['Date of Birth'] = date_match.group(2)

        if patient_info['Gender'] == '':
            gender_pattern = r"(Gender:)\s+(\w{4,6})"
            gender_match = re.search(gender_pattern, info)
            if gender_match:
                patient_info['Gender'] = gender_match.group(2)
        
        if patient_info['Accession No.'] == '':
            accession_no_pattern = r"(Accession No:)\s+(\d+(\s*\d*)*)$"
            accession_no_match = re.search(accession_no_pattern, info)
            if accession_no_match:
                patient_info['Accession No.'] = accession_no_match.group(2).strip()
            
    # extracting mutation information
    mutations_info(file_path, patient_info)

    return True, patient_info # return True if able to extract

def mutations_info(file_path: str, patient_info: dict) -> None:
    ocr = TesseractOCR()

    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(file_path, dpi = 200, output_folder=path, last_page = 1, paths_only = True)
        image = Image(src = images[0])

        extracted_tables = image.extract_tables(ocr = ocr)
        if extracted_tables:
            try:
                mutations = []

                for table in extracted_tables:
                    mutations_found = False

                    for row in table.content:
                        if table.content[row][0] and table.content[row][0].value:
                            if table.content[row][0].value.strip() == 'Pathogenic Mutations Detected':
                                mutations_found = True
                                continue

                        if mutations_found:
                            mutation = table.content[row][0].value
                            if mutation:
                                mutation = mutation.replace("¢", "c")
                                if mutation.startswith(('I', '\\')):
                                    mutation = mutation[1:]

                                mutations.append(mutation.strip())

                mutations_str = ' '.join(f'[{mutation}]' for mutation in mutations)

                patient_info['Mutations'] = mutations_str
            except Exception as e:
                validate_input(patient_info, file_path, mutation_error = e)

def validate_input(patient_info: dict, file_path: str, no_start = False, mutation_error = None):

    if no_start:
        print(f"{file_path} does not contain the proper information; could not find patient information")
        patient_info['File Name'] = file_path
        return False
    
    if mutation_error:
        print(f'Error extracting mutation: {mutation_error}')
        patient_info['File Name'] = file_path
        return False
    
    ## checking if any of the patients' required information is missing
    check_patient_info = itemgetter('Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Clinical Indication', 'Type of Specimen', 'Physician', 'Date Received', 'Date Reported', 'Mutations')
    result = check_patient_info(patient_info)

    if "" in result:
        print(f"Patient from file {file_path} missing required information")
        patient_info['File Name'] = file_path
        return False
    
    return True