import os

EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".idea", ".vscode"}

for root, dirs, files in os.walk("."):
    # фильтруем директории
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

    level = root.count(os.sep)
    indent = " " * 4 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 4 * (level + 1)
    for f in files:
        print(f"{subindent}{f}")
