import os

ROOT = r"d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"

MAPPINGS = [
    ("repomind.server", "repomind.api"),
    ("repomind.settings", "repomind.core.settings"),
    ("repomind.di", "repomind.core.di"),
    ("repomind.launcher", "repomind.core.launcher"),
    ("repomind.initialize", "repomind.core.initialize"),
    ("repomind.components.ingest", "repomind.ingestion.ingest"),
    ("repomind.core.ingestion", "repomind.ingestion"),
    ("repomind.components.readers", "repomind.parsers.readers"),
    ("repomind.components.chunk", "repomind.rag.chunk"),
    ("repomind.components.prompts", "repomind.rag.prompts"),
    ("repomind.components.synthesizer", "repomind.rag.synthesizer"),
    ("repomind.components.context", "repomind.rag.context"),
    ("repomind.components.engines", "repomind.rag.engines"),
    ("repomind.components.postprocessor", "repomind.rag.postprocessor"),
    ("repomind.components.memory", "repomind.rag.memory"),
    ("repomind.core.retrieval", "repomind.rag"),
    ("repomind.components.workflows", "repomind.services.workflows"),
    ("repomind.components.chat", "repomind.services.chat"),
    ("repomind.core.analysis", "repomind.analyzers"),
    ("repomind.components.llm", "repomind.models.llm"),
    ("repomind.components.embedding", "repomind.models.embedding"),
    ("repomind.components.model_discovery", "repomind.models.model_discovery"),
    ("repomind.components.database", "repomind.data.database"),
    ("repomind.components.postgres", "repomind.data.postgres"),
    ("repomind.components.sqlite", "repomind.data.sqlite"),
    ("repomind.components.vector_store", "repomind.vector_store.vector_store"),
    ("repomind.components.node_store", "repomind.vector_store.node_store"),
    ("repomind.components.concurrency", "repomind.utils.concurrency"),
    ("repomind.utils", "repomind.utils"), # No-op for utils, but catches if anything changed
]

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    new_content = content
    for old, new in MAPPINGS:
        # Import matching like `from x import` or `import x`
        # To avoid partial matches, we could replace ' ' + old + '.' and ' ' + old + ' '
        # But a simple string replace might be enough if we order them carefully.
        # Actually, python imports can be `from repomind.server...`
        new_content = new_content.replace(old + ".", new + ".")
        new_content = new_content.replace(old + " ", new + " ")
        new_content = new_content.replace(old + "\n", new + "\n")
        new_content = new_content.replace("'" + old + "'", "'" + new + "'")
        new_content = new_content.replace('"' + old + '"', '"' + new + '"')

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        # print(f"Updated {filepath}")

def main():
    target_dirs = ["repomind", "scripts", "ui"]
    for d in target_dirs:
        dir_path = os.path.join(ROOT, d)
        if not os.path.exists(dir_path):
            continue
        for r, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith((".py", ".toml", ".yaml", "Makefile")):
                    process_file(os.path.join(r, file))
                    
    # Also process root files
    root_files = ["pyproject.toml", "Makefile", "settings.yaml"]
    for rf in root_files:
        if os.path.exists(os.path.join(ROOT, rf)):
            process_file(os.path.join(ROOT, rf))

if __name__ == "__main__":
    main()
