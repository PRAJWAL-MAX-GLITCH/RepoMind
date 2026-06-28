import os
import re

ROOT = r"d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"

SUBMODULES_TO_FIX = [
    "embeddings", "health", "ingest", "models", "primitives", "utils",
    "chat", "chat_async", "completion", "content", "mcp", "skills", "tools"
]

def fix_imports(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return

    new_content = content
    # Replace repomind.api.{submodule} with repomind.api.server.{submodule}
    for sub in SUBMODULES_TO_FIX:
        # Match repomind.api.embeddings, but not repomind.api.server.embeddings
        # Use negative lookbehind or simple string replacement
        # Let's replace 'repomind.api.submodule' where it's not preceded by '.server'
        # To be safe, we can replace repomind.api.{sub} -> repomind.api.server.{sub}
        # and then clean up double server, or do it with regex.
        pattern = r"\brepomind\.api\." + sub + r"\b"
        new_content = re.sub(pattern, "repomind.api.server." + sub, new_content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed imports in: {filepath}")

def main():
    for r, _, files in os.walk(os.path.join(ROOT, "repomind")):
        for file in files:
            if file.endswith(".py"):
                fix_imports(os.path.join(r, file))

if __name__ == "__main__":
    main()
