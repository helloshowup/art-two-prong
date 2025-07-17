import os
import re

def slugify(text):
    # Extract and clean the module number and heading text
    match = re.match(r'^(\d+)\.(\d+)\s+(.*)', text)
    if match:
        major, minor, title = match.groups()
        prefix = f"{major}-{minor}"
    else:
        # fallback: no module number found
        prefix = ''
        title = text

    title = title.strip().lower()
    title = re.sub(r'[^\w\s-]', '', title)   # remove punctuation
    title = re.sub(r'\s+', '-', title)       # spaces to dashes
    title = re.sub(r'-+', '-', title)        # collapse multiple dashes

    return f"{prefix}-{title}".strip('-')

def rename_markdown_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('# '):
                        h1_text = line.lstrip('# ').strip()
                        break
                else:
                    print(f"No H1 found in {filename}")
                    continue

            new_slug = slugify(h1_text)
            new_filename = f"{new_slug}.md"
            new_file_path = os.path.join(folder_path, new_filename)

            if filename != new_filename:
                os.rename(file_path, new_file_path)
                print(f"Renamed: {filename} → {new_filename}")
            else:
                print(f"Skipped (already named): {filename}")

# 🔧 Replace this path with your markdown folder
rename_markdown_files_in_folder('./docs')
