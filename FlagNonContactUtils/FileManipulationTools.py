import sys
import os
import csv
from tempfile import NamedTemporaryFile
import shutil
import numpy as np

def read_file(source_dir, f):
    dict_obj = {}
    if f.endswith('.csv'):
        try:
            with open(os.path.join(source_dir, f), newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=',')
                for row in spamreader:
                    print(row)
                    break

        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
            print()
    else:
        raise NotImplementedError('The file: '+ str(f)+ ' is not supported! Please use files with extensions: .csv')

