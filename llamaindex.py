import os
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import llama_index.llms.openai
from get_directories import get_input_directory, get_output_file, input_directory_path, output_file_path

def get_api_keys():

    llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
    if not llama_cloud_api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY is not set. Please set it in the environment.")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please set it in the environment.")
    
    return llama_cloud_api_key, openai_api_key

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
            print(file_path)

            document = SimpleDirectoryReader(input_files=[file_path], file_extractor=file_extractor).load_data()
            index = VectorStoreIndex.from_documents(document)

            # create a query engine for the index
            query_engine = index.as_query_engine()

            # query the engine
            query = "Complete this dictionary with data from the provided file and return just the dictionary with no added context: {'patient name': ''}"
            response = query_engine.query(query)
            print(response)
            data.append(response)
    
    return data

def process_output(data: list):


if __name__ == "__main__":
    input_directory_path = get_input_directory()
    llama_cloud_api_key, openai_api_key = get_api_keys()
    file_extractor = parser_setup(llama_cloud_api_key)
    process_files(input_directory_path, file_extractor)