import google.generativeai as genai
import os
import time
import requests
import json
from typing import Optional
from huggingface_hub import InferenceClient

class LLMClient:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model_name = model_name
        self.provider = "gemini"
        
        if model_name.startswith("ollama/"):
            self.provider = "ollama"
            self.model_name = model_name.replace("ollama/", "")
            self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11435/api/chat")
        elif model_name.startswith("huggingface/"):
            self.provider = "huggingface"
            self.model_name = model_name.replace("huggingface/", "")
            self.hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
            if not self.hf_token:
                print("Warning: HF_TOKEN not found. Hugging Face Inference will fail.")
        elif model_name.startswith("openrouter/"):
            self.provider = "openrouter"
            self.model_name = model_name.replace("openrouter/", "")
            self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if not self.openrouter_key:
                print("Warning: OPENROUTER_API_KEY not found. OpenRouter will fail.")
        else:
            self.provider = "gemini"
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                print("Warning: GEMINI_API_KEY not found in environment variables.")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, retries=3) -> str:
        """
        Generates text using the configured LLM provider.
        """
        try:
             if self.provider == "ollama":
                  return self._generate_ollama(prompt, system_prompt, retries)
             elif self.provider == "huggingface":
                  return self._generate_huggingface(prompt, system_prompt, retries)
             elif self.provider == "openrouter":
                  return self._generate_openrouter(prompt, system_prompt, retries)
             else:
                  return self._generate_gemini(prompt, system_prompt, retries)
        except Exception as e:
             print(f"LLM Provider Error ({self.provider}): {e}")
             # Fallback Logic
             if self.provider == "gemini":
                  print("Gemini Failed. Switching to Fallback Provider (OpenRouter)...")
                  # Fallback model for OpenRouter is hardcoded in _generate_openrouter,
                  # so we don't necessarily set self.model_name unless we want to persist it.
                  # But _generate_openrouter handles it.
                  return self._generate_openrouter(prompt, system_prompt, retries)
             elif self.provider != "gemini":
                  # Try Gemini as second fallback
                  print("Switching to Fallback Provider (Gemini)...")
                  try:
                      # Switch internal model state for Gemini
                      self.model_name = "gemini-2.0-flash"
                      self.provider = "gemini"
                      if not hasattr(self, 'model') or self.model.model_name != "models/gemini-2.0-flash":
                           genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                           self.model = genai.GenerativeModel("gemini-2.0-flash")
                           
                      return self._generate_gemini(prompt, system_prompt, retries)
                  except Exception as e2:
                      print(f"Fallback to Gemini also failed: {e2}")
                      pass
             raise e

    def _generate_openrouter(self, prompt: str, system_prompt: Optional[str], retries: int) -> str:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
             raise ValueError("OPENROUTER_API_KEY not found for fallback.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://paper2agent.local", # OpenRouter Requirement
            "X-Title": "Paper2Agent"
        }
        
        # Use the specified model or fallback
        model = self.model_name if hasattr(self, 'model_name') and self.model_name else "google/gemini-2.0-flash-001" 

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        for attempt in range(retries):
            try:
                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"OpenRouter Fallback Error (Attempt {attempt+1}): {e}")
                time.sleep(2)
        
        raise Exception("OpenRouter Fallback Failed.")

    def validate_connection(self) -> bool:
        """
        Simple health check for the configured provider.
        """
        try:
             # Just try a simple generation with 1 token max to test connectivity
             if self.provider == "ollama":
                  slug_model = self.model_name.rsplit(":", 1)[0] # e.g. qwen2.5-coder
                  # Just check if model is available in list
                  resp = requests.get(self.ollama_url.replace("/api/chat", "/api/tags"))
                  return slug_model in resp.text
                  
             elif self.provider == "huggingface":
                  # Verification via Model Info (Auth Check)
                  # Inference might be limited for VLMs, but this proves Access.
                  try:
                       from huggingface_hub import model_info
                       info = model_info(self.model_name.replace("huggingface/", ""), token=self.hf_token)
                       print(f"✅ HF Validation: Model found (Gated: {info.gated})")
                       return True
                  except Exception as e:
                       print(f"HF Validation Failed: {e}")
                       return False
                  
             elif self.provider == "openrouter":
                  if not os.environ.get("OPENROUTER_API_KEY"): return False
                  return True
                  
             else: # Gemini
                  if not os.environ.get("GEMINI_API_KEY"): return False
                  # Minimal gen test
                  self.model.generate_content("Hi")
                  return True
        except:
             return False

    def _generate_huggingface(self, prompt: str, system_prompt: Optional[str], retries: int) -> str:
        # Use huggingface_hub for robust auth (CLI or Token)

        # If model name starts with "huggingface/", strip it if preferred, 
        # but InferenceClient handles standard repo IDs (e.g. google/medgemma-4b-it)
        repo_id = self.model_name.replace("huggingface/", "")
        
        # Token priority: Explicit (self.hf_token) -> Environment -> CLI Cache (Automatic)
        client = InferenceClient(token=self.hf_token or None)

        full_input = prompt
        # MedGemma / Gemma Formatting
        if "gemma" in repo_id.lower():
             # Basic Gemma-IT chat template
             # <start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n
             sys_part = f"System: {system_prompt}\n" if system_prompt else ""
             full_input = f"<start_of_turn>user\n{sys_part}{prompt}<end_of_turn>\n<start_of_turn>model\n"
        elif system_prompt:
             full_input = f"{system_prompt}\n\n{prompt}"

        for attempt in range(retries):
            try:
                # Text Generation
                # We use the generic query or text_generation helper
                # Explicitly pass token to ensure auth for gated models
                # Force provider="hf-inference" to avoid StopIteration on some models
                client = InferenceClient(token=self.hf_token, provider="hf-inference") 
                response = client.text_generation(
                     full_input, 
                     model=repo_id,
                     max_new_tokens=512, 
                     temperature=0.2,
                     return_full_text=False
                )
                return response
                
            except Exception as e:
                error_str = str(e)
                # Handle VLM "image-text-to-text" error or 404/410 for InferenceClient
                if "image-text-to-text" in error_str or "404" in error_str or "410" in error_str:
                     print(f"HF InferenceClient Error ({e}). Falling back to Raw HTTP for VLM/Gated...")
                     # Try Router URL first, then Inference URL
                     token = self.hf_token
                     headers = {"Authorization": f"Bearer {token}"} if token else {}
                     payload = {"inputs": full_input, "parameters": {"max_new_tokens": 512, "temperature": 0.2, "return_full_text": False}}
                     
                     # 1. Try Router
                     router_url = f"https://router.huggingface.co/hf-inference/models/{repo_id}"
                     try:
                          resp = requests.post(router_url, headers=headers, json=payload, timeout=30)
                          if resp.status_code == 200:
                               try:
                                    # Response is list of dicts: [{'generated_text': '...'}]
                                    return resp.json()[0]["generated_text"]
                               except:
                                    return resp.text
                     except Exception as req_e:
                          print(f"HF Router Fallback failed: {req_e}")
                               
                     # 2. Try Standard Inference API
                     api_url = f"https://api-inference.huggingface.co/models/{repo_id}"
                     try:
                          resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
                          if resp.status_code == 200:
                               try:
                                    return resp.json()[0]["generated_text"]
                               except:
                                    return resp.text
                     except Exception as req_e:
                          print(f"HF Inference API Fallback failed: {req_e}")
                               
                     print(f"VLM Fallback Failed for {repo_id}. Last response status: {getattr(resp, 'status_code', 'N/A')} - {getattr(resp, 'text', 'N/A')}")
                     # If fallback also fails, proceed to general error handling
                     
                # Handle 503 (Loading) specially if needed, mostly InferenceClient handles basic retries
                if "503" in error_str:
                     print(f"HF Model Loading ({repo_id})... waiting 20s")
                     time.sleep(20)
                     continue
                     
                print(f"HF Error (Attempt {attempt+1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(2)
        return "Error: HF generation failed."

    def _generate_ollama(self, prompt: str, system_prompt: Optional[str], retries: int) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2  # Low temp for coding/reasoning
            }
        }

        for attempt in range(retries):
            try:
                response = requests.post(self.ollama_url, json=payload, timeout=120)
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
            except Exception as e:
                print(f"Ollama Error (Attempt {attempt+1}/{retries}) for model '{self.model_name}': {e}")
                if attempt == retries - 1:
                    return f"Error: Ollama generation failed. {str(e)}"
                time.sleep(2)
        return f"Error: Ollama failed for model {self.model_name}."

    def _generate_gemini(self, prompt: str, system_prompt: Optional[str], retries: int) -> str:
        # Safety Check: If we ended up here with a huggingface model, redirect or error
        if any(x in self.model_name.lower() for x in ["huggingface", "medgemma", "openbiollm", "llama"]):
             print(f"CRITICAL ERROR: Gemini Provider received non-Gemini model: {self.model_name}")
             return f"Error: Configuration Mismatch. Tried to use Gemini provider for {self.model_name}."

        full_prompt = prompt
        if system_prompt:
             full_prompt = f"System Instruction: {system_prompt}\n\nUser Question: {prompt}"
        
        # Ensure model is configured
        if not hasattr(self, 'model'):
             genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
             # Use 1.5-flash as stable fallback
             self.model = genai.GenerativeModel("gemini-1.5-flash")

        for attempt in range(retries):
            try:
                # 1.5-flash is stable
                response = self.model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"LLM Rate Limit (429). Waiting before retry {attempt + 1}/{retries}...")
                    time.sleep(10 * (attempt + 1)) 
                elif "404" in error_str and "not found" in error_str:
                     # Try Pro if flash fails
                     try:
                         print("Gemini 1.5 Flash not found, trying Pro...")
                         pro_model = genai.GenerativeModel("gemini-pro")
                         return pro_model.generate_content(full_prompt).text
                     except:
                         return f"Error: Model not found."
                else:
                    print(f"LLM Generation Error: {e}")
                    if attempt == retries - 1:
                        return f"Error: {str(e)}"
                    time.sleep(2)
        
        return "Error: Failed to generate after retries."
