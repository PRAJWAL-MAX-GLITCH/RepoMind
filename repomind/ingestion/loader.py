from pathlib import Path
from typing import Optional

class FileLoader:
    """
    Handles reading the raw content of code and documentation files.
    """
    def __init__(self):
        pass

    def load_content(self, file_path: Path) -> Optional[str]:
        """
        Reads a file's content as a UTF-8 string.
        Gracefully handles encoding errors for unsupported file types.
        
        Args:
            file_path (Path): Path to the file.
            
        Returns:
            Optional[str]: The raw file content, or None if the file could not be read.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Likely a binary file that slipped through the scanner
            return None
        except Exception as e:
            # Log error
            return None
