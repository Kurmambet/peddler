# C:\projects\peddler\peddler\tree.py - скрипт для генерации этого project_structure.md
import os

# Директории для исключения из обхода
EXCLUDE_DIRS = {
    ".ruff_cache",
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "postgres_dev_data",
    "redis_dev_data",
}

# Файлы/директории, которые НЕ нужно копировать содержимое
SKIP_CONTENT_DIRS = {
    "alembic/versions",
    "backend/alembic",
    "node_modules",
    ".vscode",
    ".venv",
    ".ruff_cache",
    "__pycache__",
}

SKIP_CONTENT_FILES = {
    ".dockerignore",
    "uv.lock",  # Большой файл зависимостей
    ".gitignore",
    "alembic.ini",  # Конфиг alembic
    ".md",
    "README.md",
    "notes.txt",
    "README.md",
    # "tree.py",
    "project_structure.md",
    "package-lock.json",
}

# Расширения файлов для копирования
INCLUDE_EXTENSIONS = {
    ".py",
    # ".txt",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".js",
    ".ts",
    ".vue",
    ".html",
    ".css",
    ".env.example",
    ".dockerignore",
    "Dockerfile",
}

OUTPUT_FILE = "project_structure.md"


def get_file_extension(filename):
    """Получить расширение файла для подсветки синтаксиса."""
    ext_map = {
        ".py": "python",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".js": "javascript",
        ".ts": "typescript",
        ".vue": "vue",
        ".html": "html",
        ".css": "css",
        ".md": "markdown",
        ".sh": "bash",
        "Dockerfile": "dockerfile",
        ".dockerignore": "text",
    }

    if filename == "Dockerfile":
        return "dockerfile"

    for ext, lang in ext_map.items():
        if filename.endswith(ext):
            return lang

    return "text"


def should_include_file(filepath):
    """Проверить, нужно ли включать файл."""
    filename = os.path.basename(filepath)

    # Пропускаем файлы из черного списка
    if filename in SKIP_CONTENT_FILES:
        return False

    # Пропускаем файлы без расширения (кроме Dockerfile)
    if filename == "Dockerfile":
        return True

    # Проверяем расширение
    return any(filename.endswith(ext) for ext in INCLUDE_EXTENSIONS)


def is_in_skip_dir(filepath, root_path):
    """Проверить, находится ли файл в директории, которую нужно пропустить."""
    rel_path = os.path.relpath(filepath, root_path)

    for skip_dir in SKIP_CONTENT_DIRS:
        if rel_path.startswith(skip_dir.replace("/", os.sep)):
            return True

    return False


def generate_tree(root_path="."):
    """Генерировать древовидную структуру проекта."""
    tree_lines = []

    for root, dirs, files in os.walk(root_path):
        # Фильтруем директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        dirs.sort()

        level = root.replace(root_path, "").count(os.sep)
        indent = "    " * level
        dirname = os.path.basename(root) or os.path.basename(os.getcwd())
        tree_lines.append(f"{indent}{dirname}/")

        subindent = "    " * (level + 1)
        for f in sorted(files):
            tree_lines.append(f"{subindent}{f}")

    return "\n".join(tree_lines)


def generate_file_contents(root_path="."):
    """Генерировать содержимое файлов."""
    content_lines = []

    for root, dirs, files in os.walk(root_path):
        # Фильтруем директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        dirs.sort()

        for filename in sorted(files):
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, root_path)

            # Проверяем, нужно ли включать файл
            if not should_include_file(filepath):
                continue

            # Проверяем, не в исключенной ли директории
            if is_in_skip_dir(filepath, root_path):
                continue

            # Читаем содержимое файла
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Определяем язык для подсветки
                lang = get_file_extension(filename)

                # Добавляем разделитель и содержимое
                content_lines.append(f"\n## {rel_path}\n")
                content_lines.append(f"```{lang}")
                content_lines.append(content)
                content_lines.append("```\n")

            except Exception as e:
                content_lines.append(f"\n## {rel_path}\n")
                content_lines.append(f"```{lang}")
                content_lines.append(f"Error reading file: {e}")
                content_lines.append("```\n")

    return "\n".join(content_lines)


def main():
    """Главная функция."""
    print("=" * 50)
    print("Generating project structure...")
    print("=" * 50)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Заголовок
        f.write("# Project Structure\n\n")
        f.write("## Directory Tree\n\n")
        f.write("```")

        print("📁 Building directory tree...")
        tree = generate_tree(".")
        f.write(tree)
        f.write("\n```\n\n")

        f.write("---\n\n")
        f.write("# File Contents\n")

        print("Copying file contents...")
        contents = generate_file_contents(".")
        f.write(contents)

    print("=" * 50)
    print("✅ SUCCESS!")
    print(f"File: {OUTPUT_FILE}")

    # Статистика
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"Size: {file_size / 1024:.2f} KB ({file_size:,} bytes)")
    print("=" * 50)


if __name__ == "__main__":
    main()
