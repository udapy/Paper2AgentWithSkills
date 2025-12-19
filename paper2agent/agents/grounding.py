from paper2agent.llm.client import LLMClient
from paper2agent.llm.config import MODEL_CONFIG
import json

class ScientificGroundingAgent:
    def __init__(self):
        self.llm = LLMClient(model_name=MODEL_CONFIG["grounding"])

    def verify(self, code, result, context):
        prompt = f"""
        Verify if the following result is scientifically plausible for the given context.
        
        Context (User Query): "{context}"
        Code Executed: 
        {code}
        
        Result/Output:
        {result}
        
        Output valid JSON with keys:
        - valid: boolean
        - feedback: string (reasoning)
        
        Do not output markdown blocks. Just JSON.
        """
        
        response = self.llm.generate(prompt, system_prompt="You are a scientific reviewer.")
        
        try:
            # Clean potential markdown
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            return data.get("valid", False), data.get("feedback", "No feedback provided")
        except Exception as e:
            return False, f"Grounding check failed to parse: {str(e)}"
