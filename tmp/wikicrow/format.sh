#!/bin/bash

# Loop through all files with .md extension in the current directory
for file in *.md; do
    # Check if file exists (in case no .md files are found)
    if [ -f "$file" ]; then
        # Get the base name of the file without the extension
        base_name=$(basename "$file" .md)
        
        # Rename the file, changing the extension to .txt
        mv "$file" "${base_name}.txt"
        
        echo "Renamed: $file to ${base_name}.txt"
    fi
done

echo "Renaming complete."
