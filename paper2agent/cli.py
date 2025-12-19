import argparse
import sys
import os
from paper2agent.orchestrator import Orchestrator

# Simple .env loader
def load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    print(f"DEBUG: Looking for .env at {env_path}")
    if os.path.exists(env_path):
        print("DEBUG: Found .env file.")
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val.strip('"').strip("'")
                        print(f"DEBUG: Loaded {key}")
                    except ValueError:
                        pass
    else:
        print("DEBUG: .env file NOT found.")

def main():
    load_env()
    parser = argparse.ArgumentParser(description="Paper2Agent CLI: R-ASAA Architecture")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run "query" --paper "path/to/paper.pdf"
    run_parser = subparsers.add_parser("run", help="Execute a query")
    run_parser.add_argument("query", help="The scientific query/task to perform")
    run_parser.add_argument("--paper", help="Path to a paper (PDF) to use as context", default=None)
    run_parser.add_argument("--context", help="Path to a data file (CSV/AnnData) to use as data context", default=None)

    # Command: ui (Interactive Demo)
    ui_parser = subparsers.add_parser("ui", help="Launch Interactive Gradio UI")

    args = parser.parse_args()

    if args.command == "run":
        print(f"--- Paper2Agent: Processing request ---")
        orch = Orchestrator()
        try:
            result_code, execution_output, trace = orch.process_query(args.query, data_context=args.context, paper_path=args.paper)
            
            print("\n=== 🟢 SYSTEM ANSWER / RESULT ===")
            print(execution_output)
            print("==================================")
            
            print("\n--- (Underlying Code) ---")
            print(result_code)
            print("-------------------------")

            print("\n--- [Architecture Trace] ---")
            for k, v in trace.items():
                 print(f"{k.capitalize()}: {v}")
            print("----------------------------")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error: {e}")

    elif args.command == "ui":
        print("--- Launching Interactive UI ---")
        from paper2agent.ui import launch_ui
        launch_ui()

    elif args.command == "ingest":
        orch = Orchestrator()
        if args.paper and os.path.exists(args.paper):
            orch.ingest.process(args.paper)
            markdown_text = orch.ingest.process(args.paper)
            orch.retriever.add_document(markdown_text, source_name=os.path.basename(args.paper))
            print(f"Successfully ingested {args.paper}")
        else:
            print("Error: Paper path invalid.")

    elif args.command == "build":
        print(f"--- Paper2Agent: Building Skills from Codebase ---")
        from paper2agent.modules.scanner import CodeScanner
        
        scanner = CodeScanner()
        files = scanner.scan(args.codebase)
        print(f"Found {len(files)} code files in {args.codebase}")
        
        orch = Orchestrator()
        count = 0
        for file in files:
            print(f"Extracting tools from {os.path.basename(file['path'])}...")
            try:
                tools = orch.synthesizer.extract_tools(file['content'], source_name=os.path.basename(file['path']))
                for tool in tools:
                    orch.skill_registry.store(tool['code'], description=tool['name'], verification_log={"success": True, "source": "extracted"})
                    print(f"  + Stored tool: {tool['name']}")
                    count += 1
            except Exception as e:
                print(f"  x Failed to extract from {file['path']}: {e}")
        
        print(f"\n✅ Build Complete. Extracted {count} tools into Skill Registry.")

    elif args.command == "list-skills":
        orch = Orchestrator()
        print("Listing skills from Registry...")
        # Hacky peek at chroma
        try:
            cnt = orch.skill_registry.collection.count()
            print(f"Total Skills stored: {cnt}")
            # peek = orch.skill_registry.collection.peek()
            # print(peek)
        except:
             print("Could not access registry count.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
