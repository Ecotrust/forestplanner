echo "manage.py test trees..."
coverage run manage.py test trees --noinput -v 2 2>&1 | tee ../mediaroot/tests/test_results.txt 
echo "coverage html..."
coverage html -d ../mediaroot/tests/test_coverage --include "trees/*"
