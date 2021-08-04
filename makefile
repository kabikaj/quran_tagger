###################################################################################################################
#
# INSTALLATION AND TESTING FOR DEVELOPMENT
#
# QuranTagger Copyright (C) 2021  Alicia González Martínez (aliciagm85+kabikaj at gmail dot com), Peter Verkinderen
#
###################################################################################################################

.PHONY : help all execute_tests

all: execute_tests

execute_tests:
	@echo "\n>> Executing unittests..."
	python3 test_util.py
	python3 test_quran_tagger.py

help:
	@echo "    all"
	@echo "        execute all tests"
	@echo "    execute_tests"
	@echo "        execute all tests"
	@echo ""
	@echo "usage: make [help] [all] [apply_test]"
