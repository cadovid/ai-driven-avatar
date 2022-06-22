.PHONY: os-info list-packages clean update-env refresh-env conda-path update-conda create-env initial-setup

# External variables
VENV := venv
SHELL := /bin/bash
MAIN := $(wildcard ./TMK/*.py)
SOURCE := $(wildcard ./TMK/src/*.py)
UTILS := $(wildcard ./TMK/utils/*.py)

# Check for OS
ifdef OS
   RMV = del /Q
   FixPath = $(subst /,\,$1)
   RFR = findstr 
else
   ifeq ($(shell uname), Linux)
      RMV = rm -rf
      FixPath = $1
	  RFR = grep
	  CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
   endif
endif


# Outputs OS system information
os-info:
	@echo $(shell uname)

# Lists all of the installed packages in your virtual environment
list-packages:
	@$(CONDA_ACTIVATE) ./$(VENV); conda list

# Removes cache and current enviroment
clean:
	$(RMV) __pycache__
	$(RMV) ./$(VENV)

# Updates your enviroment with the latest information from .yml file
update-env: update-conda
	conda env update --prefix ./$(VENV) --file environment.yml  --prune

# Export all the local changes from your system to the .yml file
refresh-env: update-conda
	conda env export --from-history | $(RFR) -v "^prefix: " | $(RFR) -v "^name: " > environment.yml

# Shows anaconda installation path
conda-path:
	@echo $$(conda info --base)

# Updates conda to latest version
update-conda:
	conda update -n base -c defaults conda

# Creates the virtual environment from .yml file
create-env: update-conda
	conda env create --prefix ./$(VENV) -f environment.yml

# Initialization of virtual environment (do not use)
initial-setup: update-conda
	conda create -y --prefix ./$(VENV) python=3.9
	@$(CONDA_ACTIVATE) ./$(VENV); conda env export --from-history -f environment.yml

# Check for style, best practices
check-code:
	@mkdir -p ./reports
	@echo "Generating pylint report for main scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); pylint $(MAIN) --output-format=text:./reports/pylint-report-MAIN.text
	@echo "Generating pylint report for src scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); pylint $(SOURCE) --output-format=text:./reports/pylint-report-SOURCE.text
	@echo "Generating pylint report for utils scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); pylint $(UTILS) --output-format=text:./reports/pylint-report-UTILS.text
	@echo "Generating flake8 report for main scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); flake8 $(MAIN) --output-file=./reports/flake8-report-MAIN.text
	@echo "Generating flake8 report for src scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); flake8 $(SOURCE) --output-file=./reports/flake8-report-SOURCE.text
	@echo "Generating flake8 report for utils scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); flake8 $(UTILS) --output-file=./reports/flake8-report-UTILS.text
	@echo "Generating bandit report for main scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); bandit -r $(MAIN) -f txt -o ./reports/bandit-report-MAIN.text
	@echo "Generating bandit report for src scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); bandit -r $(SOURCE) -f txt -o ./reports/bandit-report-SOURCE.text
	@echo "Generating bandit report for utils scripts"
	-@$(CONDA_ACTIVATE) ./$(VENV); bandit -r $(UTILS) -f txt -o ./reports/bandit-report-UTILS.text

# Correct style, best practices
correct-code:
	@$(CONDA_ACTIVATE) ./$(VENV); black $(MAIN) --diff
	@$(CONDA_ACTIVATE) ./$(VENV); black $(SOURCE) --diff
	@$(CONDA_ACTIVATE) ./$(VENV); black $(UTILS) --diff

# Creates pylint general settings file by default
default-pylint-settings:
	@pylint --generate-rcfile > .pylintrc

# Add channels to conda environment
conda-channels: update-conda
	@conda config --add channels conda-forge
