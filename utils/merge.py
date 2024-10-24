"""
TODO: Rewrite to better handle the data structures output by the agents
"""

import os
import json

def load_and_organize_json_data(json_dir):
    all_json_data = {}

    # Load all JSON files in the directory
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

    for file in json_files:
        with open(os.path.join(json_dir, file), 'r') as f:
            file_data = json.load(f)
            
            # Extract category and section title from the filename
            category, section_title = file[:-5].rsplit('_', 1)  # Remove '.json' and split by last underscore
            
            if section_title not in all_json_data:
                all_json_data[section_title] = {}
            
            if category not in all_json_data[section_title]:
                all_json_data[section_title][category] = []

            # Append the section data to the category list
            all_json_data[section_title][category].extend(file_data.get('sections', []))

    return all_json_data

def remove_non_applicable_entries(data):
    """
    Removes entries where 'applicable' is False from the JSON data.
    """
    for section in data.get("sections", []):
        for _, feedback_list in section.get("feedback", {}).items():
            for feedback in feedback_list:
                feedback["requirement_evaluations"] = [
                    evaluation for evaluation in feedback.get("requirement_evaluations", [])
                    if evaluation.get("applicable") is not False
                ]

# Directory containing the JSON files
json_dir = 'data/score/results'
all_json_data = load_and_organize_json_data(json_dir)

article_path = 'data/score/article.json'
with open(article_path, 'r') as a:
    article = json.load(a)

# Match article sections with feedback
for article_section in article:
    section_title = article_section['title']
    if section_title in all_json_data:
        article_section['feedback'] = all_json_data[section_title]
    else:
        article_section['feedback'] = {}

# Output the combined structure in JSON format
output_json = {
    "sections": article
}

# Remove non-applicable entries
remove_non_applicable_entries(output_json)

output_json_str = json.dumps(output_json['sections'], indent=2)

output_file_path = 'data/output.json'
with open(output_file_path, 'w') as output_file:
    output_file.write(output_json_str)

print(f"Combined JSON data has been saved to {output_file_path}")