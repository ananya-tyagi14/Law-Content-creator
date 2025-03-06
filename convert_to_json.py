import re
import json
import os


class ConvertToJson:

    def __init__(self):

        #patterns for headings
        #self.section_pattern = re.compile(r'^(\d+\. )(.+)$')
        self.section_pattern = re.compile(
            r'^(?:<SEC>\s*)?(\d+\.\s)(.+?)(?:\s*</SEC>)?$'
        )
        
        #self.subsection_pattern = re.compile(r'^(\d+(?:\.\d+)+\.?\s)(.+)$')
        self.subsection_pattern = re.compile(r'^((?:<SUBSEC>\s*)?\d+\.\d+(?:\.\d+)?\.?\s)(.+?)(?:\s*</SUBSEC>)?$')

    def parse_heading_line(self, line, pattern, split=True):

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

        #with open(file_path, 'r', encoding='utf-8') as f:
            #lines = f.read().splitlines()

        lines = text.splitlines()
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


            if self.subsection_pattern.match(line):
                flush_group()
                #current_subsection = line
                current_subsection, extra = self.parse_heading_line(line, self.subsection_pattern, split=True)
                
                if extra:
                    content_lines.append(extra)
                continue

            if self.section_pattern.match(line) and not self.subsection_pattern.match(line):
                flush_group()
                #current_section = line
                current_section, extra = self.parse_heading_line(line, self.section_pattern, split=False)                
                current_subsection = None
                if extra:
                    content_lines.append(extra)
                continue

            content_lines.append(line)

        flush_group()
        return data


    def parse_and_save(self, text, output_file):

        data = self.parse_document(text)

        with open(output_file, "w", encoding ='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
                
