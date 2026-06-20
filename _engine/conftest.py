import os
import sys

# Rende importabile il package 'ocrsys' e gli entrypoint a prescindere dalla
# cartella da cui si lancia pytest.
sys.path.insert(0, os.path.dirname(__file__))
