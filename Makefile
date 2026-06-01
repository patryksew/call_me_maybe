install:
	uv sync

run:
	uv run python -m src

run-smol:
	uv run python -m src --model HuggingFaceTB/SmolLM2-1.7B-Instruct

run-smoller:
	uv run python -m src --model HuggingFaceTB/SmolLM2-360M-Instruct

run-liquid:
	uv run python -m src --model LiquidAI/LFM2.5-1.2B-Instruct

run-llama:
	uv run python -m src --model meta-llama/Llama-3.2-1B-Instruct

debug:
	uv run python -m pdb -m src

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
