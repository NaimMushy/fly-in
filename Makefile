#-------------------------------- VARIABLES ----------------------------------#

NAME		=	fly_in.py
MAP			?=
POETRY		=	poetry

#-------------------------------- RULES --------------------------------------#

all: $(NAME)


$(NAME): install run

install: poetry-check
	poetry install

run: poetry-check
	@poetry run python3 $(NAME) $(MAP)

debug: poetry-check
	@poetry run python3 -m pdb $(NAME)

clean: poetry-check
	find . -name "__pycache__" -type d -exec rm -rf "{}" +
	find . -name ".mypy_cache" -type d -exec rm -rf "{}" +

fclean: clean
	poetry env remove --all

re: fclean all

lint: poetry-check
	@$(MAKE) install >/dev/null
	poetry run flake8 .
	poetry run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude .venv

lint-strict: poetry-check
	@$(MAKE) install >/dev/null
	poetry run flake8 .
	poetry run mypy . --strict

poetry-check:
	@command -v $(POETRY) >/dev/null 2>&1 || { \
		echo "Error: The '$(POETRY)' tool is not installed or not in the PATH." >&2; \
		echo "To install it: 'pip install poetry'" >&2; \
		exit 1; \
	}

.PHONY: all install run debug clean fclean re lint lint-strict poetry-check
