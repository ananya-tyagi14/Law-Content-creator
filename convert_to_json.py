import re
import json
import os


section_pattern = re.compile(r'^(\d+\. )(.+)$')
subsection_pattern = re.compile(r'^(\d+\.\d+\.? )(.+)$')


def parse_document(file_path):

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    data = []
    current_section = None
    current_subsection = None
    content_lines = []
    

    def flush_group():
        nonlocal current_section, current_subsection, content_lines
        if content_lines:
            group = {
                "Section": current_section,
                "Subsection": current_subsection,
                "Content": " ".join(content_lines).strip()
                }
            data.append(group)
            content_lines = []


    for line in lines:

        line = line.strip()
        if not line:
            continue


        if subsection_pattern.match(line):
            flush_group()
            current_subsection = line
            continue

        if section_pattern.match(line) and not subsection_pattern.match(line):
            flush_group()
            current_section = line
            current_subsection = None
            continue

        content_lines.append(line)

    flush_group()
    return data



def save_as_json(data, output_file):

    with open(output_file, "w", encoding ='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_directory(root_dir):

    for subdir, dirs, files in os.walk(root_dir):
      for file in files:
          if file.startswith("~$"):
                continue
          if file.lower().endswith(".txt"):
              txt_file_path = os.path.join(subdir, file)
              json_file_path = os.path.join(subdir, os.path.splitext(file)[0] + ".json")
              
              parsed_data = parse_document(txt_file_path)
              save_as_json(parsed_data, json_file_path)      
                

if __name__ == "__main__":

    #file_path = r"C:\Users\User\OneDrive\Documents\UNI work\SCC\year 4\placement\legal resources\Family law\Pracitcal Advice Note - Domestic Abuse.txt"
    #parsed_data = parse_document(file_path)

    root_dir = os.path.join(os.getcwd(), "legal resources")
    process_directory(root_dir)


    
