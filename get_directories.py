import os

input_directory_path = None
output_file_path = None

def get_input_directory():

    global input_directory_path

    if not input_directory_path:
        input_directory_path = input("Enter the path to the folder containing the PDF files:")

        while not os.path.isdir(input_directory_path):
            input_directory_path = input("Invalid. Enter the path to the folder containing the PDF files:")

    return input_directory_path

def get_output_file():
    
    global output_file_path

    if not output_file_path:
        output_file_path = input("Enter the path to the .csv file for the results. If the file does not exist, it will be created:")
        
        while not output_file_path.endswith(".csv"):
            output_file_path = input("The file has to be a .csv file. Enter the path to the .csv file for the results. If the file does not exist, it will be created:")
        
        if not os.path.exists(output_file_path):
            create_confirmation = input(f"Do you want to create a new file at {output_file_path}? [y/n]")
            
            while create_confirmation not in ["y", "n"]:
                create_confirmation = input(f"Invalid input. Do you want to create a new file at {output_file_path}? [y/n]")

            if create_confirmation == "n":
                output_file_path = ''
                get_output_file()

    return output_file_path