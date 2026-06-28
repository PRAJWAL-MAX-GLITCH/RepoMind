import os

def search_project():
    root_dir = r"d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"
    terms = ["PrivateGPT", "private_gpt", "private-gpt", "Private GPT"]
    found = []
    for root, _, files in os.walk(root_dir):
        # Skip node_modules, .git, etc if they exist
        if '.git' in root or '.venv' in root or '.uv-cache' in root:
            continue
        for file in files:
            if file.endswith((".py", ".md", ".html", ".yaml", ".txt", ".json", ".toml", ".sh")):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for term in terms:
                            if term in content:
                                found.append(f"{term} found in {filepath}")
                                break
                except:
                    pass
    for f in found:
        print(f)
    if not found:
        print("No remaining references found.")

if __name__ == "__main__":
    search_project()
