import os
import re
import fnmatch
from pathlib import Path
from typing import Optional
from langchain.tools import BaseTool

class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Reads the content of a specified file. Optionally use start_line and end_line for targeted reads."

    def _run(self, file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)
            
            return "".join(lines[start:end])
        except Exception as e:
            return f"Error reading file: {e}"

class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "Writes complete content to a file, creating missing parent directories. Overwrites existing files."

    def _run(self, file_path: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

class ReplaceTextTool(BaseTool):
    name: str = "replace"
    description: str = "Replaces exact literal text within a file. Replaces the first exact match of old_string with new_string."

    def _run(self, file_path: str, old_string: str, new_string: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_string not in content:
                return "Error: old_string not found in file (must be an exact match)."
                
            new_content = content.replace(old_string, new_string, 1)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return f"Successfully replaced text in {file_path}"
        except Exception as e:
            return f"Error replacing text: {e}"

class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "Lists the names of files and subdirectories directly within a specified directory path."

    def _run(self, dir_path: str) -> str:
        try:
            items = os.listdir(dir_path)
            return "\n".join(sorted(items)) if items else "(Empty directory)"
        except Exception as e:
            return f"Error listing directory: {e}"

class GlobSearchTool(BaseTool):
    name: str = "glob"
    description: str = "Efficiently finds files matching specific glob patterns (e.g., 'src/**/*.py')."

    def _run(self, pattern: str, dir_path: str = ".") -> str:
        try:
            path = Path(dir_path)
            matches = list(path.rglob(pattern))
            if not matches:
                return "No files matched the pattern."
            return "\n".join(str(p.absolute()) for p in matches[:100])
        except Exception as e:
            return f"Error running glob search: {e}"

class GrepSearchTool(BaseTool):
    name: str = "grep_search"
    description: str = "Searches for a regular expression pattern within file contents across a directory."

    def _run(self, pattern: str, dir_path: str = ".", include_pattern: str = "*") -> str:
        results = []
        try:
            compiled_pattern = re.compile(pattern)
            for root, _, files in os.walk(dir_path):
                # Skip common ignore directories
                if any(ignored in root for ignored in ['.git', '__pycache__', 'venv', 'node_modules']):
                    continue
                    
                for filename in files:
                    if fnmatch.fnmatch(filename, include_pattern):
                        filepath = os.path.join(root, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                for i, line in enumerate(f):
                                    if compiled_pattern.search(line):
                                        results.append(f"{filepath}:{i+1}: {line.strip()}")
                                        if len(results) >= 50: # Limit output for context safety
                                            results.append("... [Results truncated for context safety]")
                                            return "\n".join(results)
                        except (UnicodeDecodeError, PermissionError):
                            continue
                            
            return "\n".join(results) if results else "No matches found."
        except Exception as e:
            return f"Error running grep search: {e}"
