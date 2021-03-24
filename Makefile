PYTHON = python3
TESTFILE = test.sh

.PHONY: test clean

# If the first argument is "run"...
ifeq (run,$(firstword $(MAKECMDGOALS)))
  # use the rest as arguments for "run"
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  # ...and turn them into do-nothing targets
  $(eval $(RUN_ARGS):;@:)
endif

clean-build:
	@find $(PKGDIR) -name '*.pyc' -delete
	@find $(PKGDIR) -name '__pycache__' -delete
	-@rm -rf __pycache__ 

clean: clean-build
	@rm -f *.o *~ tmp* *.c *.txt

check:
	@$(PYTHON) --version

test: clean-build check
	@echo "running test script"

	./${TESTFILE}

