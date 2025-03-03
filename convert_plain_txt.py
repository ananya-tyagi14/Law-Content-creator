import os
from docx import Document
from docx.oxml.ns import qn
import re 

def get_list_level(paragraph):

    p = paragraph._element
    pPr = p.find(qn("w:pPr"))
    if pPr is None:
        return None
    numPr = pPr.find(qn("w:numPr"))
    if numPr is None:
        return None
    ilvl = numPr.find(qn("w:ilvl"))
    if ilvl is not None and ilvl.get(qn("w:val")).isdigit():
        return int(ilvl.get(qn("w:val")))
    return 0  # fallback if <w:ilvl> has no val


def is_list_paragraph(paragraph):
    """Return True if the paragraph is a bullet/numbered list item (at any level)."""
    return get_list_level(paragraph) is not None


def collapse_blank_lines(lines):
    
    cleaned_lines = []
    for line in lines:
        if not line.strip():
            if cleaned_lines and not cleaned_lines[-1].strip():
                    continue
            else:
                cleaned_lines.append("")
        else:
            cleaned_lines.append(line)
    return cleaned_lines


def finalize_bullet_list(explicit_intro, bullet_entries):

    merged_entries = []
    for entry in bullet_entries:
        parent = entry["text"]
        nested = entry["nested"]
        if nested:
            if len(nested) == 1:
                merged = parent + " " + nested[0]
            else:
                # Remove trailing periods for all but last nested bullet.
                merged_nested = nested[0].rstrip(".")
                for i in range(1, len(nested)):
                    if i == len(nested) - 1:
                        merged_nested += ", " + nested[i]  # keep period of last
                    else:
                        merged_nested += ", " + nested[i].rstrip(".")
                merged = parent + " " + merged_nested
        else:
            merged = parent
        merged_entries.append(merged)
    # Join all merged bullet entries with commas.
    joined = ", ".join(merged_entries)
    if explicit_intro:
        return explicit_intro + " " + joined
    else:
        return joined

 
def docx_to_text(docx_path, txt_path):
    document = Document(docx_path)
    paragraphs = document.paragraphs


    output_lines = []
    in_list = False
    explicit_intro = None   # If a bullet list starts with an explicit intro (a colon-ending paragraph)
    current_bullets = []    # List of dictionaries: each is {"text": <top bullet>, "nested": [<nested bullet texts>]}
    
    for para in paragraphs:

        #print(para.style.name, repr(para.text))
        
        if para.style and para.style.name == "Heading 1":
            continue

        text = para.text.strip()

        if not in_list:
            if text.endswith(":"):
                explicit_intro = text  # keep the colon
                in_list = True
                current_bullets = []
                continue
            
            elif is_list_paragraph(para):
                
                in_list = True
                explicit_intro = None
                current_bullets = []

                lvl = get_list_level(para)
                current_bullets.append({"text": text, "nested": []})
                continue
            else:
                output_lines.append(text)
                continue

        if is_list_paragraph(para):
            lvl = get_list_level(para)
            if lvl == 0:
                # Top-level bullet.
                current_bullets.append({"text": text, "nested": []})

            else:
                # Nested bullet: append to the nested list of the last top-level bullet.
                if current_bullets:
                    current_bullets[-1]["nested"].append(text)
                else:
                    # Fallback if no top-level bullet exists.
                    current_bullets.append({"text": text, "nested": []})
        else:
            if in_list:
                merged = finalize_bullet_list(explicit_intro, current_bullets)
                output_lines.append(merged)
               
                in_list = False
                explicit_intro = None
                current_bullets = []

            if text.endswith(":"):
                explicit_intro = text
                in_list = True
                current_bullets = []
            else:
                output_lines.append(text)

    if in_list:
        merged = finalize_bullet_list(explicit_intro, current_bullets)
        output_lines.append(merged)
        

    final_lines = collapse_blank_lines(output_lines)

    check_heading_pattern = re.compile(r'^\d+(\.\d+)*\.?\s')

    non_heading_indices = [
        i for i, line in enumerate(final_lines)
        if line.strip() and not check_heading_pattern.match(line)
        ]
    
    processed_lines = []
    for i, line in enumerate(final_lines):
        if line.strip() and not check_heading_pattern.match(line):
            if non_heading_indices and i != non_heading_indices[-1]:
                processed_lines.append(line + "<SEP>")
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)

    
    full_text = "\n".join(processed_lines)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)
        
        

def process_directory(root_dir):

    for subdir, dirs, files in os.walk(root_dir):
      for file in files:
          if file.startswith("~$"):
                continue
          if file.lower().endswith(".docx"):
              docx_file_path = os.path.join(subdir, file)
              txt_file_path = os.path.join(subdir, os.path.splitext(file)[0] + ".txt")
            
              print(f"processing {docx_file_path}...")
              docx_to_text(docx_file_path, txt_file_path)
              print("\n")

if __name__ == "__main__":
    
    #docx_path = r"C:\Users\User\OneDrive\Documents\UNI work\SCC\year 4\placement\legal resources\Family law\Practical Advice Note - General Family.docx"
    #docx_to_text(docx_path, "output.txt")

    root_dir = os.path.join(os.getcwd(), "legal resources")
    process_directory(root_dir)
