
.PHONY: list
list:
	@$(MAKE) -pRrq -f $(firstword $(MAKEFILE_LIST)) : 2>/dev/null | \
		awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' |\
		sort | \
		egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | \
		xargs

####################################################################################################
#  vvv                                                                                             #
####################################################################################################
.PHONY: clean
clean:
	@find . -name .cache        -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name __pycache__   -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name .pytest_cache -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name dist          -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name build         -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name htmlcov       -type d -exec rm -rf {} \; 2>/dev/null ; true
	@find . -name ".coverage"   -type f -exec rm -r  {} \; 2>/dev/null ; true

.PHONY: test
test:
	PYTHONPATH=. py.test \
		--cov-report term:skip-covered \
		--cov-report html \
		--cov sanic_openapi3e --cov tests \
		--verbose --verbose \
		--maxfail 1

.PHONY: dist
dist:
	python setup.py bdist_wheel
	python setup.py sdist

.PHONY: pypi
pypi: clean dist
	twine upload -r pypi dist/*
