import os

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    new_content = content.replace("private_gpt", "repomind")
    new_content = new_content.replace("PrivateGPT", "RepoMind")
    new_content = new_content.replace("private-gpt", "repomind")
    new_content = new_content.replace("Private GPT", "RepoMind")

    if new_content != content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
        except Exception as e:
            print(f"Error writing {filepath}: {e}")

def main():
    root_dir = r"d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"
    
    # Specific root files
    root_files = ["pyproject.toml", "Makefile", "settings.yaml", "settings-mock.yaml", "settings-test.yaml", "README.md", "uv.lock"]
    for rf in root_files:
        replace_in_file(os.path.join(root_dir, rf))
        
    # Directories to walk
    dirs_to_walk = ["repomind", "tests", "scripts", "ui"]
    for d in dirs_to_walk:
        dir_path = os.path.join(root_dir, d)
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith((".py", ".md", ".html", ".yaml", ".txt", ".json", ".toml", ".sh")):
                    replace_in_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
