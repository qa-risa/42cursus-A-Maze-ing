VENV = .venv
BIN = $(VENV)/bin
PYTHON = $(BIN)/python3
FLAKE8 = flake8
MYPY = mypy

.PHONY: install run debug clean fclean lint lint-strict analyze analyze-bonus review package

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(BIN)/pip install -r requirements.txt

run: $(VENV) install
	$(PYTHON) a_maze_ing.py config.txt

analyze: $(VENV) install
	$(PYTHON) maze_analyzer.py maze.txt

analyze-bonus: $(VENV) install
	$(PYTHON) maze_analyzer.py maze.txt --max-dead-ends 0

debug: $(VENV) install
	$(PYTHON) -m pdb a_maze_ing.py config.txt

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache build dist *.egg-info .mypy_cache*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

fclean: clean
	rm -rf $(VENV)
	rm -rf review/
	rm -f maze.txt

lint: $(VENV) install
	$(BIN)/$(FLAKE8) .
	$(BIN)/$(MYPY) . --exclude '(\.venv|review|build)/' --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: $(VENV) install
	$(BIN)/$(FLAKE8) .
	$(BIN)/$(MYPY) . --exclude '(\.venv|review|build)/' --strict

review: $(VENV) install
	$(PYTHON) -m build
	mkdir review
	cp dist/mazegen-1.0.0-py3-none-any.whl review/
	cp a_maze_ing.py review/
	cp config.txt review/
	python3 -m venv review/.venv
	review/.venv/bin/pip install review/mazegen-1.0.0-py3-none-any.whl
	review/.venv/bin/python3 review/a_maze_ing.py review/config.txt

package: $(VENV) install
	$(PYTHON) -m build
	cp dist/mazegen-1.0.0-py3-none-any.whl dist/mazegen-1.0.0.tar.gz .
