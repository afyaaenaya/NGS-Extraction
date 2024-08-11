import ocrmypdf
import os
from get_directories import get_input_directory, input_directory_path

def ocr_folder(dir_path):

    files = os.listdir(dir_path)

    for file in files:
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(dir_path, file)
            temp_path = os.path.join(dir_path, f"temp_{file}")
            
            ocrmypdf.ocr(file_path, temp_path, force_ocr=True)
            os.replace(temp_path, file_path)

if __name__ == '__main__':
    input_directory_path = get_input_directory()
    # ocr_folder(dir)