import os
from docx import Document
from docx.oxml.ns import qn
import re

class ConvertPlainTxt:

    def __init__(self):

        """
        Initialize the converter with regular expression patterns for section and 
        subsection headings.
        
        """

        self.section_heading_pattern = re.compile(r'^\d+\.\s')
        self.subsection_heading_pattern = re.compile(r'^\d+\.\d+(?:\.\d+)?\.?\s')
        

    def get_list_level(self, paragraph):

        """
        This function inspects the XML element of the paragraph to determine if it is part 
        of a numbered or bullet list and returns its nesting level.

        Parameters:
            paragraph: A paragraph object from the DOCX document.

        Returns:
            int: The list level (indentation) if found, or 0 as a fallback.
        """

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

        """
        Collapse consecutive blank lines into a single blank line.
        
        Parameters:
            lines (list): A list of text lines.
        
        Returns:
            list: A new list of text lines with consecutive blanks collapsed.
        """
        
        cleaned_lines = [] #intialise list 
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

        """
        This method combines top-level and nested bullet items into a single
        sentence. Nested bullet items are merged using commas, while ensuring
        that punctuation is handled appropriately.
        """

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

        """      
        A delimiter ("<SEP>") is added to lines that are not recognized as section
        or subsection headings, except when a subsection heading does not contain a colon.
        
        Parameters:
            line (str): A line of text.
        
        Returns:
            bool: True if a delimiter should be added, otherwise False.
        """

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

        """     
        The method reads the .docx file, processes paragraphs to handle bullet lists 
        (including merging nested bullets), and collapses extra blank lines. It also adds
        a delimiter ("<SEP>") to separate content sections.
        
        Parameters:
            docx_path (str): The file path of the .docx document.
        
        Returns:
            str: The processed plain text output.
        """
        
        document = Document(docx_path)
        paragraphs = document.paragraphs


        output_lines = []
        in_list = False
        explicit_intro = None   # If a bullet list starts with an explicit intro (a colon-ending paragraph)
        current_bullets = []    # List of dictionaries: each is {"text": <top bullet>, "nested": [<nested bullet texts>]}
        
        for para in paragraphs:

            # Skip Heading 1 lines
            if para.style and para.style.name == "Heading 1":
                continue

            text = para.text.strip()

            if not in_list:
                #Check if the paragraph ends with a colon (explicit intro)
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
                
            # If already in a bullet list block:
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

                    
        #Finalize any remaining bullet list block.
        if in_list:
            merged = self.finalize_bullet_list(explicit_intro, current_bullets)
            output_lines.append(merged)
            

        final_lines = self.collapse_blank_lines(output_lines)
                       
        #Determine indices for non-heading lines where delimiters should be added.
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
