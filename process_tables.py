import tempfile
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from img2table.document import Image
from img2table.ocr import TesseractOCR

def mutations_info(file_path: str) -> tuple[bool, str]:
    ocr = TesseractOCR()

    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(file_path, dpi = 200, output_folder=path, last_page = 1, paths_only = True)
        image = Image(src = images[0])
        extracted_tables = image.extract_tables(ocr = ocr)
        if extracted_tables:
            for table in extracted_tables:
                if table.content[0][0].value.strip() == "Pathogenic Mutations Detected" and table.content[1][0].value:
                    mutation = table.content[1][0].value
                    mutation.replace("¢", "c")
                    return True, mutation
        
        return False, ""