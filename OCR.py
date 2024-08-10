import ocrmypdf
import os

def get_dir():
    dir = input("Enter the path to the folder containing the PDF files:")
    while not os.path.isdir(dir):
        dir = input("Invalid. Enter the path to the folder containing the PDF files:")
    
    return dir

def ocr_folder(dir_path):
    files = os.listdir(dir_path)

    for file in files:
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(dir_path, file)
            temp_path = os.path.join(dir_path, f"temp_{file}")
            
            ocrmypdf.ocr(file_path, temp_path, force_ocr=True)
            os.replace(temp_path, file_path)

if __name__ == '__main__':
    dir = get_dir()
    ocr_folder(dir)