.PHONY: install test demo clean build

install:
	uv venv
	@echo "Virtual environment created. Run 'source .venv/bin/activate' to activate."
	uv pip install -e .

test:
	export PYTHONPATH=$PYTHONPATH:. && pytest tests/

demo:
	@echo "Running End-to-End Demo..."
	export PYTHONPATH=$PYTHONPATH:. && python tests/test_e2e.py

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf skills_db
	rm -rf knowledge_db
	rm -f demos/demo_paper.pdf
