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
        self.headers = [
            "id",
            "o_t_r_x",
            "o_t_r_y",
            "o_t_l_x",
            "o_t_l_y",
            "o_b_r_x",
            "o_b_r_y",
            "o_b_l_x",
            "o_b_l_y",
            "o_m_m_x",
            "o_m_m_y",
            "o_pos_x",
            "o_pos_y",
            "o_angle",
            "e_pos_x",
            "e_pos_y",
            "e_angle",
            "force_x",
            "force_y",
            "torque",
            "base_vel",
            "base_acc",
            "in_contact",
            "trajectory"]

    def extract_trajectory(self, file, index):
        
        trajectory = np.array([])
        header = 0
        #read csv, and split on "," the line
        with open(file, mode ='r') as fl: 
            # reading the CSV file 
            csv_file = csv.reader(fl, delimiter=",")

            # displaying the contents of the CSV file 
            for row in csv_file:
                try:
                    traj_index = int(float(row[-1]))
                    row = [float(ele) for ele in row] 
                    if traj_index == index:
                        # Append to trajectory
                        if len(trajectory) == 0:
                            trajectory = np.array([row])
                        else:
                            trajectory = np.append(trajectory, [row], axis=0)

                except:
                    header = np.array(row)
                
        return trajectory

    def update_line(self, line, flag):
        line = np.array(line)
        lin = np.concatenate((line[:-1],[str(flag)],[line[-1]]))
        return lin

    def update_file(self, file, flags):
        counter = 0
        with open(os.path.join(self.source_dir, file)) as inf, open(os.path.join(self.out_dir, "Flagged"+file), 'a', newline='') as outf:
            reader = csv.reader(inf, delimiter=",")
            writer = csv.writer(outf)
            for line in reader:
                if line[0] =='id':
                    pass
                else:
                    try:
                        line_id = int(float(line[0]))
                        flag_id = int(flags[counter, 0])
                        if line_id == flag_id:
                            flag = flags[counter, 1]
                            line = self.update_line(line, flag)
                            writer.writerow(line)
                            counter += 1
                        else:
                            pass
                    except:
                        break    

    def extract_max_traj_index(self, file):
        max_traj_index = -1
        with open(file, mode ='r') as fl:
            csv_file = csv.reader(fl, delimiter=",")
            last_row = None
            for last_row in csv_file:
                pass
            try:
                max_traj_index = int(float(last_row[-1]))
            except:
                max_traj_index = -1

        return max_traj_index

    def create_dictionary(self, trajectory):
        traj_dict = {}
        traj_dict["ind"] = trajectory[:, 0]
        
        traj_dict["obj"] = trajectory[:, 11:14]

        traj_dict["tip"] = trajectory[:, 14:17]

        traj_dict["ft"] = trajectory[:, 17:20]

        traj_dict["nodes"] = trajectory[:, 1:11]

        return traj_dict

    def get_closest_points(self, np_nodes, np_tip):
        # Find two closest points
        np_tip = np_tip[:, :2]
        np_nodes = np_nodes[:, :8]

        # Closeness
        np_tip = np.tile(np_tip,(1,4))
        diff = np_nodes - np_tip
        diff = diff.reshape((len(diff), 4, 2))
        pow2s = np.power(diff, 2)

        # No sqrt because we don't care about actual values, we just want to compare them
        sums = np.sum(pow2s, axis=2)
        idx = np.argpartition(sums, 2, axis=1)

        bools = np.zeros(idx.shape)
        bools[:,:2] = 1
        
        # Boolean indexing
        closest_nodes = np_nodes.reshape((len(np_nodes), 4, 2))
        bools = np.reshape(bools, (len(bools), closest_nodes.shape[1], 1))
        bools = np.repeat(bools, 2, axis=2)
        bools = bools > 0
        
        closest_nodes = closest_nodes[bools]
        closest_nodes = closest_nodes.reshape((len(bools), 2, 2))

        return closest_nodes
    
    def calculate_distance(self, closest_np, np_tip):
        n_not_unit = closest_np[:, 0, :] - closest_np[:, 1, :]
        l = np.linalg.norm(n_not_unit, axis=1, keepdims=True)
        n = n_not_unit / l
        
        p = np_tip[:, :2]

        a = closest_np[:, 0]

        b = (a - p) - ((a - p) * n) * n

        distance = np.linalg.norm(b, axis=1)

        return distance

    def create_output_file(self, f):
        with open(os.path.join(self.out_dir, "Flagged"+f), 'w', newline='') as outf:
            writer = csv.writer(outf)
            writer.writerow(self.headers)


    def flag_contacts(self):
        files = [f for f in listdir(self.source_dir) if isfile(join(self.source_dir, f))]

        for f in files:
            f_path = os.path.join(self.source_dir, f)
            max_traj_index = self.extract_max_traj_index(f_path)
            
            self.create_output_file(f)

            for index in range(max_traj_index+1):
                trajectory = self.extract_trajectory(f_path, index)
                
                traj_dict = self.create_dictionary(trajectory)

                closest_np = self.get_closest_points(traj_dict["nodes"], traj_dict["tip"])

                distance = self.calculate_distance(closest_np, traj_dict["tip"])
                
                in_contact = distance<=self.threshold

                in_contact = np.reshape(in_contact, (len(in_contact), 1))
                inds = np.reshape(traj_dict["ind"], (len(in_contact), 1))

                in_contact = np.append(inds, in_contact, axis=1)
                self.update_file(f, in_contact)

    