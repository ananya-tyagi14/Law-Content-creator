import os
from plain_txt4 import ConvertPlainTxt
from convert_to_json import ConvertToJson
import json


def main():

    root_dir = os.path.join(os.getcwd(), "legal resources")

    txt_converter = ConvertPlainTxt()
    json_parser = ConvertToJson()


    for subdir, dirs, files in os.walk(root_dir):
        for file in files:

            if file.startswith("~$"):
                continue

            if file.lower().endswith(".docx"):
                docx_file_path = os.path.join(subdir, file)
                json_file_path = os.path.join(subdir, os.path.splitext(file)[0] + ".json")

                plain_txt = txt_converter.docx_to_text(docx_file_path)
                json_parser.parse_and_save(plain_txt, json_file_path)
                print(f"Saved JSON to {json_file_path}\n")


if __name__ == "__main__":
    main()
