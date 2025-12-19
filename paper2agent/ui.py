import gradio as gr
import os
import sys
from dotenv import load_dotenv
load_dotenv() # Ensure env vars are loaded early
from paper2agent.orchestrator import Orchestrator

# Global Orchestrator instance
orch = None

def init_system(pdf_file, persona_prompt):
    """
    Initialize the R-ASA system with the uploaded PDF and Persona.
    """
    global orch
    if pdf_file is None:
        return "⚠️ Please upload a PDF first."
    
    paper_path = pdf_file.name
    
    # Initialize Orchestrator
    # Note: in a real app, we might restart or re-ingest here.
    orch = Orchestrator()
    
    # Ingest the paper immediately to prepare the RAG DB
    try:
        orch.ingest.process(paper_path)
        # Hacky re-ingest trigger if needed, or just let process_query handle it.
        # process_query handles ingestion if paper_path is passed, but for Chat 
        # we want it pre-loaded.
        # Let's trust Orchestrator logic.
    except Exception as e:
        return f"❌ Error Ingesting Paper: {e}"

    return f"✅ System Initialized with {os.path.basename(paper_path)}.\nPersona: {persona_prompt or 'Default'}"

def chat_response(message, history, pdf_file, domain, grounding_override=None):
    """
    Handle chat messages.
    """
    global orch
    if orch is None or pdf_file is None:
        if pdf_file:
             init_system(pdf_file, f"Domain: {domain}")
        else:
             return "Please upload a paper first."
             
    paper_path = pdf_file.name
    
    # Determine Model based on Domain
    # Determine Model based on Domain
    model_override = None
    if "Biomedical" in domain:
         if "Gemma-2" in domain:
             model_override = "openrouter/google/gemma-2-9b-it"
         elif "Llama-3.1" in domain:
             model_override = "openrouter/meta-llama/llama-3.1-8b-instruct"
         elif "Mistral" in domain:
             model_override = "openrouter/mistralai/mistral-7b-instruct"
         else:
             model_override = "gemini-2.0-flash"  # Default fallback
         
         message = f"DOMAIN CONTEXT: You are a Clinical Decision Support System. Use the provided research paper logic to analyze this clinical case: {message}"

    try:
        # Execute
        result_code, result_output, trace = orch.process_query(message, paper_path=paper_path, model_override=model_override, grounding_override=grounding_override)
        return result_output, trace
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Agent Error: {e}", {"error": str(e)}

def verify_hf_token(token):
    # Use huggingface_hub to check identity.
    # It automatically checks env/cache if token is None, 
    # but here we might want to be explicit if token is passed.
    try:
         from huggingface_hub import whoami
         # If token is None/Empty, whoami checks local cache
         user_info = whoami(token=token or None) 
         return True, f"Authenticated as {user_info.get('name', 'User')} (via {user_info.get('auth', {}).get('type', 'Token')})"
    except Exception as e:
         return False, f"Auth Failed: {e}"

def init_system(pdf_file, domain):
    """
    Initialize the R-ASA system with the uploaded PDF and Persona.
    """
    global orch
    if pdf_file is None:
        return "⚠️ Please upload a PDF first."
    
    paper_path = pdf_file.name
    
    # Initialize Orchestrator
    orch = Orchestrator()
    
    start_msg = ""
    # Check Connectivity if Biomedical
    if "Biomedical" in domain:
         token = os.environ.get("HF_TOKEN") or os.environ.get("HF_API_KEY")
         success, msg = verify_hf_token(token)
         if success:
              start_msg = f"✅ HF Connection Verified: {msg}\n"
         else:
              start_msg = f"⚠️ HF Connection Warning: {msg}\n"

    try:
        orch.ingest.process(paper_path)
    except Exception as e:
        return f"{start_msg}❌ Error Ingesting Paper: {e}"

    return f"{start_msg}✅ System Initialized with {os.path.basename(paper_path)}.\nDomain: {domain}"

def check_ollama():
    """Checks if Ollama is running, attempts to guide user if not."""
    import requests
    try:
        requests.get("http://localhost:11434", timeout=2)
        return True, "✅ Ollama Online"
    except:
        return False, "⚠️ Ollama Offline (Run 'ollama serve')"

# Check Gradio Version for Compatibility
# Gradio 4.x+ uses messages format, 3.x uses tuples
GRADIO_VERSION = gr.__version__
IS_GRADIO_4_PLUS = int(GRADIO_VERSION.split('.')[0]) >= 4
if IS_GRADIO_4_PLUS:
    print(f"Detected Gradio {GRADIO_VERSION}: Using Messages format.")
else:
    print(f"Detected Gradio {GRADIO_VERSION}: Using Tuple format.")

def launch_ui():
    with gr.Blocks(title="Paper2Agent: Clinical Decision Support") as demo:
        gr.Markdown("# 🏥 Clinical Decision Support Agent (Paper2Agent Demo)")
        gr.Markdown("Upload a paper and ask for a diagnosis based on symptoms. Configure the **Reasoning Architecture** below.")
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="Upload Research Paper (PDF)", file_types=[".pdf"])
                
                # Domain / Synthesizer
                domain_input = gr.Dropdown(
                     choices=[
                         "General (Gemini 2.0 Flash)", 
                         "Biomedical (Gemma-2 9B - OpenRouter)",
                         "Biomedical (Llama-3.1 8B - OpenRouter)",
                         "Biomedical (Mistral 7B - OpenRouter)"
                      ], 
                     value="General (Gemini 2.0 Flash)", 
                     label="Synthesizer (Writer) Model"
                )
                
                # Grounding / Critic
                grounding_input = gr.Dropdown(
                     choices=[
                         "Fast Critic (Gemini 2.0 Flash)",
                         "Deep Reflector (Gemini Pro Latest)",
                         "Local Reasoner (DeepSeek-R1:8b)",
                         "Claude Haiku (OpenRouter)",
                         "Llama-3.1 8B (OpenRouter)"
                     ],
                     value="Local Reasoner (DeepSeek-R1:8b)",
                     label="Integrity (Critic) Model"
                )

                init_btn = gr.Button("Initialize Agent")
                status_out = gr.Textbox(label="System Status", interactive=False)
                trace_out = gr.JSON(label="Multi-Model Architecture Trace")
                
            with gr.Column(scale=2):
                # Gradio 6.x automatically uses messages format, no type parameter needed
                chatbot = gr.Chatbot(label="Agent Trace", elem_id="chatbot", height=600)
                    
                msg = gr.Textbox(label="Patient Symptoms / Query", placeholder="Patient is 45yo male...")
                clear = gr.Button("Clear Context")

        # Initialize Action
        def init_wrapper(pdf, domain):
             ollama_status, ollama_msg = check_ollama()
             
             # Validation Check
             from paper2agent.llm.client import LLMClient
             from paper2agent.llm.config import MODEL_CONFIG
             
             val_msg = "✅ Models Validated"
             
             # Determine actual synthesizer model based on dropdown
             target_model = MODEL_CONFIG["synthesizer"] # Default
             if "BioMistral" in domain:
                 target_model = MODEL_CONFIG["medgemma"] # Mapped to BioMistral
             elif "OpenBioLLM" in domain:
                 target_model = MODEL_CONFIG["openbiollm"]
             
             # Validate the SELECTED model
             if not LLMClient(target_model).validate_connection():
                 val_msg += f"\n⚠️ Synthesizer ({target_model}) Connectivity Check Failed."
             else:
                 val_msg += f"\n✅ Synthesizer ({target_model}) Online."
             
             # Check OpenRouter Fallback
             if not os.environ.get("OPENROUTER_API_KEY"):
                 val_msg += "\nℹ️ OpenRouter Fallback not configured."
             else:
                  val_msg += "\n✅ OpenRouter Fallback Configured."
             
             sys_msg = init_system(pdf, domain)
             return f"{ollama_msg}\n{val_msg}\n{sys_msg}"

        init_btn.click(init_wrapper, [pdf_input, domain_input], status_out)

            # Chat Action
        def respond(message, chat_history, pdf_file, domain, grounding):
            # Ensure history list exists
            if not chat_history: chat_history = []
            
            if not pdf_file:
                 warning_txt = "⚠️ Please upload a paper first."
                 if IS_GRADIO_4_PLUS:
                     # Messages format
                     chat_history.append({"role": "user", "content": message})
                     chat_history.append({"role": "assistant", "content": warning_txt})
                 else:
                     # Tuples format
                     chat_history.append((message, warning_txt))
                 return "", chat_history, {}

            # Map Grounding Selection
            grounding_map = {
                "Fast Critic (Gemini 2.0 Flash)": "gemini-2.0-flash",
                "Deep Reflector (Gemini Pro Latest)": "gemini-pro-latest",
                "Local Reasoner (DeepSeek-R1:8b)": "ollama/deepseek-r1:8b",
                "Claude Haiku (OpenRouter)": "openrouter/anthropic/claude-3-haiku",
                "Llama-3.1 8B (OpenRouter)": "openrouter/meta-llama/llama-3.1-8b-instruct"
            }
            grounding_model = grounding_map.get(grounding)
            
            # Add user message and thinking placeholder
            if IS_GRADIO_4_PLUS:
                # Messages format
                chat_history.append({"role": "user", "content": message})
                chat_history.append({"role": "assistant", "content": "Thinking..."})
            else:
                # Tuples format
                chat_history.append((message, "Thinking..."))
            
            yield "", chat_history, {} # Yield immediately

            # Get response
            try:
                bot_message_text, trace = chat_response(message, chat_history, pdf_file, domain, grounding_override=grounding_model)
                
                # Update history with actual response
                if IS_GRADIO_4_PLUS:
                    # Messages format - update the last assistant message
                    chat_history[-1] = {"role": "assistant", "content": bot_message_text}
                else:
                    # Tuples format
                    chat_history[-1] = (message, bot_message_text)
                
                yield "", chat_history, trace
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_txt = f"❌ Error: {str(e)}"
                
                if IS_GRADIO_4_PLUS:
                    # Messages format - update the last assistant message
                    chat_history[-1] = {"role": "assistant", "content": error_txt}
                else:
                    # Tuples format
                    chat_history[-1] = (message, error_txt)
                
                yield "", chat_history, {"error": str(e)}

        msg.submit(respond, [msg, chatbot, pdf_input, domain_input, grounding_input], [msg, chatbot, trace_out])
        clear.click(lambda: (None, []), None, [msg, chatbot], queue=False)

    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)

if __name__ == "__main__":
    launch_ui()
