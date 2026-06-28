from pathlib import Path
from typing import Optional

class LanguageParser:
    """
    Provides language-aware parsing helpers. Maps file extensions to specific 
    parsing strategies or syntax tools (e.g., Python vs TypeScript).
    """
    
    EXTENSION_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".md": "markdown"
    }

    @classmethod
    def get_language(cls, file_path: Path) -> Optional[str]:
        """
        Determines the programming language based on the file extension.
        
        Args:
            file_path (Path): Path to the source file.
            
        Returns:
            Optional[str]: The identified language string, or None if unsupported.
        """
        return cls.EXTENSION_MAP.get(file_path.suffix.lower())
