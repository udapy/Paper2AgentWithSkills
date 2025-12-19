import os
import glob

class CodeScanner:
    def scan(self, directory):
        """
        Scans a directory for Python files and Jupyter notebooks.
        Returns a list of dicts: {'path': str, 'content': str, 'type': str}
        """
        results = []
        if not os.path.exists(directory):
            print(f"Scanner Warning: Directory {directory} does not exist.")
            return results

        # Scan .py
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py") or file.endswith(".ipynb"):
                    full_path = os.path.join(root, file)
                    content = self._read_file(full_path)
                    if content:
                        results.append({
                            "path": full_path,
                            "content": content,
                            "type": "python" if file.endswith(".py") else "notebook"
                        })
        return results

    def _read_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return None
