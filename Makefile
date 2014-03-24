.PHONY: test

test:
	python -m test.model
	python -m test.persistence
	python -m test.functional
