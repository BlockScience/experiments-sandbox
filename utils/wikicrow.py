import re 

def parse_wikicrow(path: str):
    with open(path, 'r') as a:
        markdown_text = a.read()
        
    root_title = markdown_text.splitlines()[0].strip('#').strip()
    # Regular expression pattern for detecting markdown headers (##, ###, etc.)
    section_pattern = re.compile(r'^(#+)\s*(.*?)\s*$')

    structured_data = []
    current_hierarchy = [root_title]
    current_title = root_title
    current_content = ""

    # Start with the root section
    structured_data.append({
        "title": current_title,
        "content": "",
        "hierarchy": ' > '.join(current_hierarchy)
    })

    for line in markdown_text.splitlines()[1:]:  # Skip the first line as it's the root title
        section_match = section_pattern.match(line)
        
        if section_match:
            # If there's an ongoing section, save the current one
            if current_content or len(current_hierarchy) > 1:  # Only append if there's content or it's not top-level
                structured_data.append({
                    "title": current_title,
                    "content": current_content.strip(),
                    "hierarchy": ' > '.join(current_hierarchy)
                })
            
            # New section detected, update the current title, hierarchy, and content
            level = len(section_match.group(1))  # Number of '#' indicates the level
            current_title = section_match.group(2).strip()
            
            # Update hierarchy based on the level
            current_hierarchy = current_hierarchy[:level-1] + [current_title]
            current_content = ""
        else:
            current_content += line.strip() + " "

    # Append the last section if it has content or is not top-level
    if current_content or len(current_hierarchy) > 1:
        structured_data.append({
            "title": current_title,
            "content": current_content.strip(),
            "hierarchy": ' > '.join(current_hierarchy)
        })

    # Remove any top-level sections without content besides the first one
    structured_data = [structured_data[0]] + [section for section in structured_data[1:] if section['content'] or section['hierarchy'] != root_title]

    return structured_data
