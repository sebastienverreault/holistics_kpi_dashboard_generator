setup: requirements.txt
	# python -m venv env
	# source env/bin/activate
	pip install -r requirements.txt

run:
	python3 ./main.py test.csv
