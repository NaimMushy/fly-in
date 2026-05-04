#-------------------------------- VARIABLES ----------------------------------#

NAME		=	fly_in.py

#-------------------------------- RULES --------------------------------------#

all: $(NAME)

$(NAME): install run

install: 
	poetry install

run:
	@poetry run python3 $(NAME)

debug:
	@poetry run python3 -m pdb $(NAME)

clean:
	find . -name "__pycache__" -type d -exec rm -rf "{}" +
	find . -name ".mypy_cache" -type d -exec rm -rf "{}" +

fclean: clean
	poetry env remove --all

re: fclean all

lint:
	poetry run flake8 .
	poetry run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude .venv

lint-strict:
	poetry run flake8 .
	poetry run mypy . --strict

.PHONY: all install run debug clean fclean re lint lint-strict
