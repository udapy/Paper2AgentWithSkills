import os
import sys
from paper2agent.orchestrator import Orchestrator

def run_demo():
    """
    Runs the end-to-end R-ASA flow with IntentRecs.pdf.
    """
    print("=== Starting R-ASAA Demo with IntentRecs.pdf ===")
    
    # 1. Setup
    paper_path = "demos/IntentRecs.pdf"
    if not os.path.exists(paper_path):
        print(f"❌ Error: {paper_path} not found.")
        sys.exit(1)

    # 2. Orchestration
    orch = Orchestrator()
    
    # 3. Query
    # A generic query to test the paper's content
    query = "What is the core algorithm of IntentRecs and how does it calculate user intent?"
    print(f"\n[User Query]: {query}")
    
    try:
        # We pass the paper path so it ingests it
        result_code, result_output = orch.process_query(query, paper_path=paper_path)
        
        print("\n[Result Code]:")
        print(result_code)
        print("\n[Execution Output]:")
        print(result_output)
        
        # We can't easily assert the text output of a real paper without knowing it, 
        # but we check if we got a non-empty answer.
        if len(result_output) > 50:
             print("\n✅ SUCCESS: Validation output received.")
        else:
             print("\n⚠️ WARNING: Output seems too short.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    run_demo()
