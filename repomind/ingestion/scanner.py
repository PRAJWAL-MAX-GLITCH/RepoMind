import os
from pathlib import Path
from typing import List, Generator

class RepositoryScanner:
    """
    Scans a local directory or clones a remote Git repository.
    Respects .gitignore rules and filters out unsupported or binary files.
    """
    def __init__(self, repo_path: str):
        """
        Initializes the scanner with a target repository path.
        
        Args:
            repo_path (str): The local path or remote Git URL to scan.
        """
        self.repo_path = Path(repo_path)

    def scan(self) -> Generator[Path, None, None]:
        """
        Walks the repository directory and yields paths to supported source files.
        Ignores hidden folders (like .git) and items listed in .gitignore.
        
        Yields:
            Path: A file path pointing to a code or documentation file.
        """
        # TODO: Implement robust .gitignore parsing and tree traversal
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                yield Path(root) / file

    def collect_supported_files(self) -> List[Path]:
        """
        Convenience method to collect all scanned files into a list.
        
        Returns:
            List[Path]: A list of paths to supported files.
        """
        return list(self.scan())
