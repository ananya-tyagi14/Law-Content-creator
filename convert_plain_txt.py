import os
from docx import Document
from docx.oxml.ns import qn
import re

class ConvertPlainTxt:

    def __init__(self):

        self.section_heading_pattern = re.compile(r'^\d+\.\s')
        self.subsection_heading_pattern = re.compile(r'^\d+\.\d+(?:\.\d+)?\.?\s')

    def get_list_level(self, paragraph):

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


    def is_list_paragraph(self, paragraph):
        """Return True if the paragraph is a bullet/numbered list item (at any level)."""
        return self.get_list_level(paragraph) is not None


    def collapse_blank_lines(self, lines):
        
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


    def finalize_bullet_list(self, explicit_intro, bullet_entries):

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

    def add_delimiter(self, line):

        stripped = line.strip()
        if not stripped:
            return False

        if not (self.section_heading_pattern.match(stripped) or self.subsection_heading_pattern.match(stripped)):
            return True

        if self.section_heading_pattern.match(stripped):
            return False
        
        if self.subsection_heading_pattern.match(stripped):
            if ":" in stripped:
                return True
            else:
                return False
            
        return True

     
    def docx_to_text(self, docx_path):
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
                
                elif self.is_list_paragraph(para):
                    
                    in_list = True
                    explicit_intro = None
                    current_bullets = []

                    lvl = self.get_list_level(para)
                    current_bullets.append({"text": text, "nested": []})
                    continue
                else:
                    output_lines.append(text)
                    continue

            if self.is_list_paragraph(para):
                lvl = self.get_list_level(para)
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
                    merged = self.finalize_bullet_list(explicit_intro, current_bullets)
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
            merged = self.finalize_bullet_list(explicit_intro, current_bullets)
            output_lines.append(merged)
            

        final_lines = self.collapse_blank_lines(output_lines)
                       

        non_heading_indices = [
            i for i, line in enumerate(final_lines)
            if line.strip() and self.add_delimiter(line)
            ]
        
        processed_lines = []
        for i, line in enumerate(final_lines):
            if line.strip() and self.add_delimiter(line):
                if non_heading_indices and i != non_heading_indices[-1]:
                    processed_lines.append(line + "<SEP>")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        full_text = "\n".join(processed_lines)
         
        return full_text
