import os
import shutil
import re

ROOT = r"d:\Project Aiml\RepoMind\private-gpt-main\private-gpt-main"
REPOMIND = os.path.join(ROOT, "repomind")

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        init_py = os.path.join(path, "__init__.py")
        if not os.path.exists(init_py):
            with open(init_py, 'w', encoding='utf-8') as f:
                pass

def move_path(src_rel, dst_rel):
    src = os.path.join(ROOT, src_rel)
    dst = os.path.join(ROOT, dst_rel)
    if not os.path.exists(src):
        return
    ensure_dir(os.path.dirname(dst))
    try:
        shutil.move(src, dst)
        print(f"Moved {src_rel} to {dst_rel}")
    except Exception as e:
        print(f"Failed to move {src_rel} to {dst_rel}: {e}")

def main_movements():
    # Target directories
    targets = ["api", "core", "ingestion", "parsers", "rag", "services", "analyzers", "models", "data", "vector_store", "tests", "utils"]
    for t in targets:
        ensure_dir(os.path.join(REPOMIND, t))

    # Move server to api
    move_path(r"repomind\server", r"repomind\api")
    
    # Core
    move_path(r"repomind\settings", r"repomind\core\settings")
    move_path(r"repomind\di.py", r"repomind\core\di.py")
    move_path(r"repomind\launcher.py", r"repomind\core\launcher.py")
    move_path(r"repomind\initialize.py", r"repomind\core\initialize.py")

    # Ingestion
    move_path(r"repomind\components\ingest", r"repomind\ingestion\ingest")
    # Existing core/ingestion moving up
    move_path(r"repomind\core\ingestion\git_parser.py", r"repomind\ingestion\git_parser.py")
    move_path(r"repomind\core\ingestion\code_splitter.py", r"repomind\ingestion\code_splitter.py")

    # Parsers
    move_path(r"repomind\components\readers", r"repomind\parsers\readers")

    # RAG
    move_path(r"repomind\components\chunk", r"repomind\rag\chunk")
    move_path(r"repomind\components\prompts", r"repomind\rag\prompts")
    move_path(r"repomind\components\synthesizer", r"repomind\rag\synthesizer")
    move_path(r"repomind\components\context", r"repomind\rag\context")
    move_path(r"repomind\core\retrieval\synthesizer.py", r"repomind\rag\code_synthesizer.py")

    # Services
    move_path(r"repomind\components\workflows", r"repomind\services\workflows")

    # Analyzers
    move_path(r"repomind\core\analysis\dependency.py", r"repomind\analyzers\dependency.py")

    # Models
    move_path(r"repomind\components\llm", r"repomind\models\llm")
    move_path(r"repomind\components\embedding", r"repomind\models\embedding")
    move_path(r"repomind\components\model_discovery", r"repomind\models\model_discovery")

    # Data
    move_path(r"repomind\components\database", r"repomind\data\database")
    move_path(r"repomind\components\postgres", r"repomind\data\postgres")
    move_path(r"repomind\components\sqlite", r"repomind\data\sqlite")

    # Vector Store
    move_path(r"repomind\components\vector_store", r"repomind\vector_store\vector_store")
    move_path(r"repomind\components\node_store", r"repomind\vector_store\node_store")

    # Tests
    move_path(r"tests", r"repomind\tests")

    # Utils
    move_path(r"repomind\utils", r"repomind\utils\utils")
    move_path(r"repomind\components\concurrency", r"repomind\utils\concurrency")

    # Remaining components that might not fit perfectly but need moving to avoid components dir
    # we'll place them in services or utils for now.
    move_path(r"repomind\components\chat", r"repomind\services\chat")
    move_path(r"repomind\components\engines", r"repomind\rag\engines")
    move_path(r"repomind\components\postprocessor", r"repomind\rag\postprocessor")
    move_path(r"repomind\components\memory", r"repomind\rag\memory")

    # Try to safely remove old components dir
    try:
        shutil.rmtree(os.path.join(REPOMIND, "components"))
    except:
        pass
    try:
        # the old core/ingestion and core/analysis might be empty
        os.rmdir(os.path.join(REPOMIND, "core", "ingestion"))
        os.rmdir(os.path.join(REPOMIND, "core", "analysis"))
        os.rmdir(os.path.join(REPOMIND, "core", "retrieval"))
    except:
        pass

if __name__ == "__main__":
    main_movements()
    print("Movements complete.")
