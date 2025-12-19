from paper2agent.llm.client import LLMClient
from paper2agent.llm.config import MODEL_CONFIG
import re

class SkillSynthesizer:
    def __init__(self):
        # Use specialized coding model (e.g., qwen2.5-coder)
        self.llm = LLMClient(model_name=MODEL_CONFIG["synthesizer"])

    def draft(self, query, context=""):
        """
        Drafts a function based on the query and optional RAG context.
        """
        context_block = ""
        if context:
            context_block = f"\nReference Context from Papers/Domain:\n{context}\n"

        prompt = f"""
        You are an Expert Research Scientist and Domain Expert.
        The user has a question: "{query}"

        {context_block}

        Your Goal is to **BRIDGE** the Research Paper concepts to the Target Domain.
        
        Step 1: **Concept Mapping**
        - Identify key algorithms/concepts in the Paper (e.g., "User Intent", "Collaborative Filtering").
        - Map them to the Target Domain (e.g., "Patient Diagnosis", "Symptom Correlation").
        
        Step 2: **Reasoning**
        - Explain WHY the paper's logic applies here.
        - e.g. "Just as we predict next-item based on history, we predict next-treatment based on symptom history."

        Step 3: **Implementation**
        - Write a Python script that:
            1. Prints the "Concept Mapping" and "Reasoning" clearly to stdout.
            2. Simulates/Calculates the final recommendation using this logic.
            3. Prints the **FINAL ANSWER**.

        Requirements:
        1. The script must be self-contained.
        2. It MUST print the Explanation/Reasoning first, then the Result.
        3. Return ONLY the code.
        """
        
        response = self.llm.generate(prompt, system_prompt="You are a Scientific Reasoning Agent.")
        return self._clean_code(response)

    def fix(self, code, critique):
        """
        Fixes the code based on critique.
        """
        prompt = f"""
        The following Python code has issues:
        
        {code}
        
        Critique/Error:
        "{critique}"
        
        Please rewrite the code to fix the issues. Return only the fixed code.
        """
        
        response = self.llm.generate(prompt, system_prompt="You are a code debugger.")
        return self._clean_code(response)

    def extract_tools(self, code_content, source_name="Unknown"):
        """
        Analyzes raw codebase content and extracts reusable tools (functions).
        Returns a list of (function_name, function_code, description) tuples.
        """
        prompt = f"""
        You are a Code Archival Agent.
        
        Source: {source_name}
        
        Raw Code Content:
        {code_content[:8000]} # Truncated if too long
        
        Your Task:
        1. Identify reusable, independent utility functions or classes in this code.
        2. Clean them up (add docstrings, types).
        3. Output each function separated by a delimiter "### FUNCTION ###".
        
        Format:
        ### FUNCTION ###
        def function_name(...):
            '''Docstring'''
            ...
        
        ### FUNCTION ###
        ...
        """
        
        response = self.llm.generate(prompt, system_prompt="You are a code extractor.")
        
        # Parse response
        tools = []
        raw_functions = response.split("### FUNCTION ###")
        for func_block in raw_functions:
            clean_func = self._clean_code(func_block)
            if len(clean_func) > 20 and "def " in clean_func:
                # Extract simple name (regex or just first line)
                name_match = re.search(r"def\s+([a-zA-Z0-9_]+)", clean_func)
                name = name_match.group(1) if name_match else "unknown_tool"
                tools.append({
                    "name": name,
                    "code": clean_func,
                    "description": f"Extracted tool from {source_name}"
                })
        
        return tools

    def _clean_code(self, text):
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
        return text.strip()
