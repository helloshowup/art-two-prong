import os

def clean_file_wrappers(folder_path):
    START_TOKENS = {"'''", '```json', '```markdown'}
    END_TOKENS = {'```'}

    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Strip wrappers
            trimmed = lines[:]
            if trimmed and trimmed[0].strip() in START_TOKENS:
                trimmed = trimmed[1:]
            if trimmed and trimmed[-1].strip() in END_TOKENS:
                trimmed = trimmed[:-1]

            if trimmed != lines:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(trimmed)
                print(f"Cleaned: {filename}")
            else:
                print(f"Skipped (no wrapper found): {filename}")

# 🔧 Replace with your folder name
clean_file_wrappers('./docs')
