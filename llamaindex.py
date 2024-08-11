import os
import csv
import ast
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import llama_index.llms.openai
from get_directories import get_input_directory, get_output_file, input_directory_path, output_file_path
from api_keys import get_api_keys

def parser_setup(llama_cloud_api_key):

    parser = LlamaParse(
        result_type="markdown",
        api_key=llama_cloud_api_key
    )

    file_extractor = {".pdf": parser}

    return file_extractor


def process_files(input_directory_path, file_extractor):

    data = []

    files = os.listdir(input_directory_path)

    for file in files:
        if file.lower().endswith(".pdf"):
            file_path = os.path.join(input_directory_path, file)

            document = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
            index = VectorStoreIndex.from_documents(document)

            # create a query engine for the index
            query_engine = index.as_query_engine()

            # query the engine
            query = "Complete this python dictionary with data from the provided file and return just the dictionary with no added context.\
                If no pathogenic mutation is found, fill it in the dictionary as 'None found'\
                If no variants of unknown significance were found, fill it in the dictionary as 'None found'\
                {'Patient Name': '', 'Date of Birth': '', 'Gender': '', 'MRN': '', 'Lab No.': '', 'Accession No.':'', 'Specimen Clinical Indication': '', 'Type of Specimen': '', 'Tissue Origin': '', 'Physician': '', 'Date Received': '', 'Date Reported': '', 'Pathogenic Mutations': '', 'Variants of Unknown Significance': ''}"
            response = query_engine.query(query)

            if hasattr(response, 'response'):
                    dict_data = ast.literal_eval(response.response)
                    if isinstance(dict_data, dict):
                        data.append(dict_data)
                    else:
                        print(f"Entry is not formatted as a dictionary: {response.response}")

    return data

def process_output(output_file_path, data: list):
    file_exists = os.path.exists(output_file_path)

    with open(output_file_path, 'a', newline='') as output_file:
        
        fieldnames = ['Patient Name', 'Date of Birth', 'Gender', 'MRN', 'Lab No.', 'Accession No.', 'Specimen Clinical Indication', 'Type of Specimen', 'Tissue Origin', 'Physician', 'Date Received', 'Date Reported', 'Pathogenic Mutations', 'Variants of Unknown Significance']
        
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)

if __name__ == "__main__":
    input_directory_path = get_input_directory()
    output_file_path = get_output_file()
    llama_cloud_api_key, openai_api_key = get_api_keys()
    file_extractor = parser_setup(llama_cloud_api_key)
    data = process_files(input_directory_path, file_extractor)
    process_output(output_file_path, data)