
from paper2agent.llm.client import LLMClient
from paper2agent.llm.config import MODEL_CONFIG

def test_ollama_client():
    print(f"Testing Synthesizer Model: {MODEL_CONFIG['synthesizer']} (Provider: Ollama)")
    client = LLMClient(model_name=MODEL_CONFIG["synthesizer"])
    
    if client.provider != "ollama":
        print("FAIL: Provider should be ollama")
        return

    print("Attempting to generate (expecting connection error if Ollama not running)...")
    response = client.generate("Hello world", retries=1)
    print(f"Response: {response}")

def test_gemini_client():
    print(f"\nTesting Grounding Model: {MODEL_CONFIG['grounding']} (Provider: Gemini)")
    client = LLMClient(model_name=MODEL_CONFIG["grounding"])
    
    if client.provider != "gemini":
        print("FAIL: Provider should be gemini")
        return

    # Don't actually call API to save quota/time, just check logic
    print("Provider check passed.")

if __name__ == "__main__":
    test_ollama_client()
    test_gemini_client()
