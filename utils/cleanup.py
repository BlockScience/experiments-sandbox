"""
TODO: 
Rewrite to better handle the outputs of the LLMS, potentially using a /tmp/ dir and then a cleanup process

Probably best to convert to a Tool as well, IE last job in the workflow is to cleanup your mess

"""

import os
import json

def aggregate_json_content(input_path, output_path):
    """Aggregate JSON content from all files in the directory and write to 'aggregated_output.json'."""
    all_data = {"groups": {}}

    json_files = [f for f in os.listdir(input_path)]

    for filename in json_files:
        path = os.path.join(input_path, filename)
        with open(path, 'r') as file:
            file_data = json.load(file)
        
        for group_name, group_info in file_data.get('groups', {}).items():
            if group_name not in all_data['groups']:
                all_data['groups'][group_name] = group_info
            else:
                all_data['groups'][group_name]['requirements'].extend(group_info['requirements'])

    # Write the aggregated data to 'aggregated_output.json'
    output_file_path = os.path.join(ouput_path, 'requirements.json')
    with open(output_file_path, 'w') as output_file:
        json.dump(all_data, output_file, indent=4)

# Example usage
input_path = 'data/requirements'
ouput_path = 'data'
aggregate_json_content(input_path, ouput_path)

