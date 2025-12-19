from paper2agent.skills.registry import SkillRegistry
from paper2agent.agents.synthesizer import SkillSynthesizer
from paper2agent.agents.integrity import IntegrityAgent
from paper2agent.agents.grounding import ScientificGroundingAgent
from paper2agent.sandbox.execution import LocalSandbox
from paper2agent.knowledge.ingest import DoclingIngest
from paper2agent.knowledge.retriever import KnowledgeRetriever
import os

class Orchestrator:
    def __init__(self):
        self.skill_registry = SkillRegistry()
        self.synthesizer = SkillSynthesizer()
        self.sandbox = LocalSandbox()
        self.integrity_agent = IntegrityAgent(self.synthesizer, sandbox=self.sandbox)
        self.grounding_agent = ScientificGroundingAgent()
        
        # Knowledge Components
        self.ingest = DoclingIngest()
        self.retriever = KnowledgeRetriever()

    def process_query(self, user_query, data_context=None, paper_path=None, model_override=None, grounding_override=None):
        print(f"Orchestrator: Processing query '{user_query}'")
        
        # Trace Log
        trace_log = {
             "retriever": "VectorDB (Chroma)",
             "synthesizer": self.synthesizer.llm.model_name,
             "integrity": self.integrity_agent.llm.model_name if hasattr(self.integrity_agent, "llm") else "Unknown",
             "execution": "Local Sandbox"
        }

        # 0. Ingest Paper if provided
        if paper_path:
            print(f"Orchestrator: Ingesting paper {paper_path}...")
            try:
                markdown_text = self.ingest.process(paper_path)
                self.retriever.add_document(markdown_text, source_name=os.path.basename(paper_path))
                print("Orchestrator: Paper ingested.")
            except Exception as e:
                print(f"Orchestrator Warning: Failed to ingest paper: {e}")

        # 1. Memory Lookup
        if not model_override: 
            existing_skill = self.skill_registry.retrieve(user_query)
            if existing_skill:
                print("Orchestrator: Skill hit! Using existing skill.")
                return *self._execute_skill(existing_skill, data_context), trace_log
        
        print("Orchestrator: Skill miss. Initiating synthesis loop.")
        
        # 1.5 Retrieve Context (RAG)
        context_chunks = self.retriever.query(user_query)
        rag_context = "\n\n".join(context_chunks) if context_chunks else ""
        if rag_context:
            print(f"Orchestrator: Retrieved {len(context_chunks)} context chunks.")
        
        # 2. Synthesis & Robustness Loop
        try:
             # Model Override (Persona)
             if model_override:
                  print(f"Orchestrator: Switching Synthesizer to {model_override}...")
                  from paper2agent.llm.client import LLMClient
                  self.synthesizer.llm = LLMClient(model_name=model_override)
                  trace_log["synthesizer"] = model_override + " (Persona Override)"

             # Grounding Override
             if grounding_override:
                  self.integrity_agent.set_model(grounding_override)
                  trace_log["integrity"] = grounding_override + " (Grounding Override)"

             # Draft
             print("Orchestrator: Drafting code...")
             full_context = f"{user_query}\n\nContext:\n{rag_context}\nData: {data_context}"
             draft_code = self.synthesizer.draft(user_query, context=full_context)
             print("Orchestrator: Code drafted.")
             
             # Robustness (Integrity Unit)
             print("Orchestrator: Entering Integrity Loop (Grounding & Validation)...")
             robust_code = self.integrity_agent.run_robustness_loop(draft_code, context=full_context)
             
             # 3. Execute & Answer (Interaction)
             print("Orchestrator: Executing skill to generate answer...")
             result = self.sandbox.run(robust_code)
             
             if not result.success:
                 return robust_code, f"Execution Error: {result.error_log}", trace_log
                 
             return robust_code, result.output, trace_log

        except Exception as e:
            import traceback
            traceback.print_exc()
            return "", f"Orchestrator Error: {str(e)}", trace_log

        finally:
             from paper2agent.llm.config import MODEL_CONFIG
             from paper2agent.llm.client import LLMClient
             
             # Restore Synthesizer 
             if model_override:
                  default_model = MODEL_CONFIG.get("synthesizer", "gemini-1.5-pro")
                  self.synthesizer.llm = LLMClient(model_name=default_model)
             
             # Restore Integrity
             if grounding_override:
                  default_integrity = MODEL_CONFIG.get("integrity", "gemini-1.5-flash")
                  self.integrity_agent.set_model(default_integrity)

    def _execute_skill(self, code, data):
        print("Orchestrator: Executing retrieved skill...")
        result = self.sandbox.run(code)
        if hasattr(result, 'output'):
             return code, result.output
        return code, str(result)
