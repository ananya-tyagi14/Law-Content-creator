import re
import json
import os


class ConvertToJson:

    def __init__(self):
        
        """
        Initialize the ConvertToJson instance with regex patterns for detecting section and subsection headings.
        """

        #patterns for headings
        self.section_pattern = re.compile(r'^(\d+\. )(.+)$')           
        self.subsection_pattern = re.compile(r'^(\d+(?:\.\d+)+\.?\s)(.+)$')

    def parse_heading_line(self, line, pattern, split=True):

        """      
        If 'split' is True and a colon is present in the line, the heading is split at the colon
        into a heading part and extra content.
        
        Parameters:
            line (str): The heading line to parse.
            pattern (re.Pattern): The regex pattern to match the heading.
            split (bool): Determines whether to split the heading at a colon.
        
        Returns:
            tuple: A tuple (heading, extra_content) where extra_content is an empty string if not applicable.
        """

        match = pattern.match(line)
        if not match:
            return line, ""

        if not split:
            return line, ""

        prefix = match.group(1)
        rest = match.group(2)

        colon_index = rest.find(":")
        if colon_index != -1:
            heading = prefix + rest[:colon_index].strip()
            extra_content = rest[colon_index+1:].strip()
            return heading, extra_content

        else:
            return line, ""


    def parse_document(self, text):

        """           
        The document is split into lines and each line is analyzed to determine if it is a section heading,
        subsection heading, or content. Groups of lines are aggregated into dictionaries with keys:
        "Section", "Subsection", and "Content".
        
        Parameters:
            text (str): The input text document.
        
        Returns:
            list: A list of dictionaries containing parsed document structure.
        """

        lines = text.splitlines()
        data = []
        current_section = None
        current_subsection = None
        content_lines = []
        

        def flush_group():
            """
            Helper function to flush the current group of content lines into the data list.
            """
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

            #Process subsection headings.
            if self.subsection_pattern.match(line):
                flush_group()
                
                current_subsection, extra = self.parse_heading_line(line, self.subsection_pattern, split=True)
                # Remove numbering from the subsection heading.
                match = re.match(r'^(\d+(?:\.\d+)+\.?\s)(.+)$', current_subsection)
                if match:
                    current_subsection = match.group(2)
                if extra:
                    content_lines.append(extra)
                continue

            # Process section headings (only if not a subsection).
            if self.section_pattern.match(line) and not self.subsection_pattern.match(line):
                flush_group()
                
                current_section, extra = self.parse_heading_line(line, self.section_pattern, split=False)
                #Remove numbering from the section heading.
                match = re.match(r'^(\d+\. )(.+)$', current_section)
                if match:
                    current_section = match.group(2)
                current_subsection = None
                if extra:
                    content_lines.append(extra)
                continue
            
            #Regular content lines are appended to the current content group.
            content_lines.append(line)

        #Flush any remaining content after processing all lines.
        flush_group()
        return data


    def parse_and_save(self, text, output_file):

        """
        Parse the input text and save the structured data as a JSON file.
        
        Parameters:
            text (str): The input text document.
            output_file (str): The file path to save the JSON output.
        """

        data = self.parse_document(text)

        with open(output_file, "w", encoding ='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
                
