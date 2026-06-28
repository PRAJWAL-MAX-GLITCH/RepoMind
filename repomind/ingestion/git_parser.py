import os
import subprocess

class GitParser:
    """
    Handles cloning, fetching, and traversing local Git repositories.
    It respects .gitignore rules and filters out binary/media files,
    focusing purely on source code and markdown documentation.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def clone_or_fetch(self, url: str):
        # TODO: Implement git clone/fetch logic
        pass

    def get_source_files(self):
        # TODO: Implement tree traversal respecting .gitignore
        return []
