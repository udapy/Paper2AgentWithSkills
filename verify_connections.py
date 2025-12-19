
import os
import requests
from huggingface_hub import InferenceClient

def verify_hf(model_id):
    print(f"--- Verifying HF Model: {model_id} ---")
    token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
    try:
        from huggingface_hub import model_info
        print(f"Checking model info for {model_id}...")
        info = model_info(model_id, token=token)
        print(f"✅ Model Info Retrieved! (Private: {info.private}, Gated: {info.gated})")
        
        # Also try to check if inference is deployed (optional)
        if info.pipeline_tag:
             print(f"Pipeline Tag: {info.pipeline_tag}")
        
        return True
             
    except Exception as e:
        print(f"❌ Verification Exception: {e}")
        # import traceback; traceback.print_exc()
        if "401" in str(e) or "403" in str(e):
             print(f"ℹ️  Access Denied (Gated Check FAILED). Visit https://huggingface.co/{model_id}")
        return False
             
    except Exception as e:
        print(f"❌ Verification Exception: {e}")
        # import traceback; traceback.print_exc()
        if "401" in str(e) or "403" in str(e):
             print(f"ℹ️  Access Denied (Gated Check FAILED). Visit https://huggingface.co/{model_id}")
        return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ HF Verification Failed for {model_id}: {repr(e)}")
        if "401" in str(e) or "403" in str(e):
             print(f"ℹ️  This model might be GATED. Please visit https://huggingface.co/{model_id} to accept the license.")
        return False

def verify_ollama(model_tag):
    print(f"\n--- Verifying Ollama Model: {model_tag} ---")
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/tags")
    try:
        resp = requests.get(url, timeout=2)
        models = [m['name'] for m in resp.json()['models']]
        if model_tag in models:
            print(f"✅ Ollama Model found: {model_tag}")
            return True
        elif any(model_tag.split(':')[0] in m for m in models):
             print(f"✅ Ollama found similar model. (Exact match: {model_tag} not found, but base exists)")
             return True
        print(f"❌ Ollama Model {model_tag} NOT found. Available: {models}")
        return False
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check user requested models
    hf = verify_hf("BioMistral/BioMistral-7B") 
    ollama = verify_ollama("deepseek-r1:8b")
