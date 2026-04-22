#-------------------------------- VARIABLES ----------------------------------#

NAME		=	fly_in.py

#-------------------------------- INSTALLS -----------------------------------#

INSTALLS	=	pydantic 							\
				flake8								\
				mypy

#-------------------------------- RULES --------------------------------------#

all: $(NAME)

$(NAME): install run

install: 
	python3 -m pip install $(INSTALLS)

run:
	@python3 $(NAME)

debug:
	@python3 -m pdb $(NAME)

clean:
	find . -name "__pycache__" -type d -exec rm -rf "{}" +
	find . -name ".mypy_cache" -type d -exec rm -rf "{}" +

lint:
	python3 -m flake8 . --exclude .venv
	python3 -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude .venv

lint-strict:
	python3 -m flake8 . --exclude .venv
	python3 -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude .venv --strict
