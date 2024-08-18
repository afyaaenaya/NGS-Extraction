import ocrmypdf
import os

def ocr_file(file_path: str):
    temp_path = file_path.removesuffix('.pdf') + '_temp.pdf'
    
    try:
        ocrmypdf.ocr(file_path, temp_path, force_ocr=True)
        os.replace(temp_path, file_path) #replace original file with OCR version
    
    except Exception as e:
        print(f'Error: {e}')

        #remove temp file if already created but original file has not been successfully replaced
        if os.path.exists(temp_path):
            os.remove(temp_path)