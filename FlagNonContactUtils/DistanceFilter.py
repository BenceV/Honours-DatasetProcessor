import os
import sys
import numpy as np
import pandas as pd
import zipfile
import shutil
import logging
import csv

from os import listdir
from os.path import isfile, join

from FlagNonContactUtils.FileManipulationTools import read_file

class DistanceFilter:
    def __init__(self, args):    
        # Set source_dir
        self.source_dir = args.source_dir
        # Set out_dir
        self.out_dir = 'processed_dataset'
        if not args.out_dir == None:
            self.out_dir = args.out_dir
        # Set threshold
        self.threshold = 0.05
        if not args.threshold == None:
            self.threshold = args.threshold
        
        # Create out_dir if it doesn't exist
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        # If source directiory doesn't exist throw an error        
        if not os.path.exists(self.source_dir):
            raise ValueError('source directory does not exist: ' +
                             self.source_dir)

    def filterStates(self):
        # Collect all the files in the directory.
        files = [f for f in listdir(self.source_dir) if isfile(join(self.source_dir, f))]
        
        for f in files:
            read_file(self.source_dir, f)
            break

    def update_file(self):
        print("Hello")

    