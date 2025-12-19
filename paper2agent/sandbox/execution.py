import subprocess
import tempfile
import os
import sys

class LocalSandbox:
    def run(self, script_content: str):
        """
        Runs the python script content in a subprocess.
        Returns a result object with success, stdout, stderr.
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(script_content)
            temp_file_path = temp_file.name

        try:
            # Run the script
            # We use likely the same python executable
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=10 # Short timeout for safety
            )
            
            success = (result.returncode == 0)
            
            # Create a unified log or separate
            error_log = result.stderr if not success else ""
            
            return ExecutionResult(success, result.stdout, error_log)
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, "", "Execution Timed Out")
        except Exception as e:
            return ExecutionResult(False, "", f"Sandbox Error: {str(e)}")
        finally:
            # Cleanup
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

class ExecutionResult:
    def __init__(self, success, stdout, error_log):
        self.success = success
        self.stdout = stdout
        self.error_log = error_log
