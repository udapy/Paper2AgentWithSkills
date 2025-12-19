import ast
import re
from paper2agent.llm.client import LLMClient
from paper2agent.llm.config import MODEL_CONFIG

class IntegrityAgent:
    def __init__(self, synthesizer, sandbox=None):
        self.synthesizer = synthesizer
        self.sandbox = sandbox 
        # Integrity needs reasoning capabilities (e.g., deepseek-r1)
        self.llm = LLMClient(model_name=MODEL_CONFIG["integrity"])
        self.test_generator = TestGenerator(self.llm)
        self.reflector = Reflector(self.llm)

    def set_model(self, model_name):
        """Swaps the underlying LLM for the Integrity components."""
        print(f"IntegrityAgent: Switching model to {model_name}")
        new_client = LLMClient(model_name=model_name)
        self.llm = new_client
        self.test_generator.llm = new_client
        self.reflector.llm = new_client

    def static_check(self, code):
        """
        Parses AST to check for dangerous operations.
        (Remains largely same as before, but ensure it's robust)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name in ['subprocess', 'sys', 'shutil']:
                        return False

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'system':
                        return False
                    if node.func.attr == 'rmtree':
                        return False
        
        if re.search(r"['\"]/[a-zA-Z]", code):
            # Check for absolute paths
            pass

        return True

    def run_robustness_loop(self, code, context):
        attempts = 0
        max_attempts = 3
        
        current_code = code

        while attempts < max_attempts:
            if not self.static_check(current_code):
                print("Static Check Failed: Unsafe code detected.")
                critique = "Code failed static safety check (e.g., restricted imports like subprocess or unsafe calls). Please rewrite safely."
                current_code = self.synthesizer.fix(current_code, critique)
                attempts += 1
                continue
            
            test_case = self.test_generator.create(context)
            
            # Use the passed sandbox or mock
            if self.sandbox:
                full_script = f"{current_code}\n\n{test_case}"
                result = self.sandbox.run(full_script)
            else:
                # Still support mock if sandbox is None for now (until next step)
                print(f"Mocking execution for attempt {attempts}")
                result = MockResult(success=(attempts > 0), error_log="Mock Error: KeyError" if attempts == 0 else "")

            if result.success:
                return current_code
            
            critique = self.reflector.analyze(current_code, result.error_log)
            print(f"Critique: {critique}")
            current_code = self.synthesizer.fix(current_code, critique)
            attempts += 1
            
        raise Exception("Failed to generate robust code after max attempts.")

class TestGenerator:
    def __init__(self, llm_client=None):
        self.llm = llm_client if llm_client else LLMClient()

    def create(self, context):
        prompt = f"""
        Generate a python usage example / text case for a function described as:
        "{context}"
        
        Requirements:
        1. It should assert the expected output.
        2. It should print "TEST PASSED" if successful, enabling stdout checks.
        3. Do NOT define the function, assume it is already defined in the scope.
        4. Return ONLY the code.
        """
        response = self.llm.generate(prompt, system_prompt="You are a QA engineer.")
        return self._clean_response(response)

    def _clean_response(self, text):
        # Remove <think>...</think> blocks from DeepSeek-R1
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return self._clean_code(text)

    def _clean_code(self, text):
        text = text.strip()
        # Find first code block if present
        match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback for simple backticks
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
        return text.strip()

class Reflector:
    def __init__(self, llm_client=None):
        self.llm = llm_client if llm_client else LLMClient()

    def analyze(self, code, error_log):
        prompt = f"""
        Analyze the following error given the code:
        
        Code:
        {code}
        
        Error Traceback:
        {error_log}
        
        Explain why it failed and suggest a specific fix. Be concise.
        """
        raw_response = self.llm.generate(prompt, system_prompt="You are an expert debugger.")
        # Clean thinking tags here too
        return re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()

class MockResult:
    def __init__(self, success, error_log):
        self.success = success
        self.error_log = error_log
