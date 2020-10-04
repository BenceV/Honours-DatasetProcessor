import h5py
import sys
import os
import csv
import numpy as np

def read_file(source_dir, f):
    dict_obj = {}
    if f.endswith('.h5'):
        #print(str(f)+' is an .h5 file!')
        try:
            dict_obj = h5py.File(os.path.join(source_dir,f), "r")

        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
            print()

    elif f.endswith('.json'):
        #print(str(f)+' is an .json file!')
        try:
            with open(os.path.join(source_dir,f)) as fl:
                dict_obj = json.load(fl)
        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
            print()
    else:
        raise NotImplementedError('The file: '+ str(f)+ ' is not supported! Please use files with extensions: .h5 or .json')

    return dict_obj

# Creating the output files, and initialising the headers on the first rows
def output_file_creation(name):
    file_names = []
    headers = [
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
        "e_x",
        "e_y"]
    # Add name to the list file names
    file_names = file_names + [name]
    # Open file and write header  
    with open(name, 'w', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["id"] + headers)
    
    return file_names

# Returning the correct file name, used in output_file_creation and _create_examples_and_write_file 
def create_name_based_on_mixing(part_index, number_of_parts, base_fileName, out_dir, shape, vel = None, acc = None):

    if vel is None and acc is None:
        name = str(base_fileName) + "_" + shape + "_" + str(part_index) + "_of_" + str(number_of_parts)+".csv"
    
    elif vel is None and acc is not None:
        name = str(base_fileName) + "_" + shape + "_" +str(part_index) + "_of_" + str(number_of_parts) +"_acc="+str(acc)+".csv"
    
    elif vel is not None and acc is None:
        name = str(base_fileName) + "_" + shape + "_" +str(part_index) + "_of_" + str(number_of_parts) +"_vel="+str(vel)+".csv"

    elif vel is not None and acc is not None:
        name = str(base_fileName) + "_" + shape + "_" +str(part_index) + "_of_" + str(number_of_parts) +"_vel="+str(vel)+"_acc="+str(acc)+".csv"
    
    return os.path.join(out_dir, name)

# Collect the properties of the files by extracting parameters of the trajectory from the name
def collect_trajectory_properties(f):
    properties = {}

    v_ind = f.find('_v=') + 3
    vel = int(float(f[v_ind:f.find('_', v_ind)]))
    properties['vel'] = vel

    a_ind = f.find('_a=') + 3
    acc = int(float(f[a_ind:f.find('_', a_ind)]))
    properties['acc'] = acc

    t_ind = f.find('_t=') + 3
    ang = float(f[t_ind:f.find('.h5')])
    properties['push_angle'] = ang * 180 / np.pi

    i_ind = f.find('_i=') + 3
    side = int(float(f[i_ind:f.find('_', i_ind)]))
    properties['push_side'] = side

    s_ind = f.find('_s=') + 3
    point = float(f[s_ind:f.find('_', s_ind)])
    properties['push_point'] = point

    return properties


# Based on the mixed parameters we want to create datasets of different distribution
# -Mixing the velocity
# -Mixing the acceleration
# -Mixing both
# For example if mixing_vel is True, 
# then the output files will contain example tuples 
# from trajectories with different velocities.
def _setup_output(base_fileName, number_of_parts, out_dir, shape, mixed_vel, mixed_acc):
    # Possible velocities and accelerations
    possible_vels = [10, 20, 50, 75, 100, 150, 200, 300, 400, 500] 
    possible_accs = [0, 0.1, 0.2, 0.5, 0.75, 1, 1.5, 2, 2.5]


    if mixed_vel and mixed_acc:
        # Set up file names and the headers
        for i in range(1, number_of_parts+1):
            name = create_name_based_on_mixing(
                part_index = i,
                number_of_parts = number_of_parts,
                base_fileName = base_fileName,
                out_dir = out_dir,
                shape = shape)

            output_file_creation(name)

    elif not mixed_vel and mixed_acc:
        # Set up file names and the headers
        for i in range(1, number_of_parts+1):
            for vel in possible_vels:
                name = create_name_based_on_mixing(
                    part_index = i,
                    number_of_parts = number_of_parts,
                    base_fileName = base_fileName,
                    out_dir = out_dir,
                    shape = shape,
                    vel = vel)
                    
                output_file_creation(name)
    
    elif mixed_vel and not mixed_acc:
        # Set up file names and the headers
        for i in range(1, number_of_parts+1):
            for acc in possible_accs:
                name = create_name_based_on_mixing(
                    part_index = i,
                    number_of_parts = number_of_parts,
                    base_fileName = base_fileName,
                    out_dir = out_dir,
                    shape = shape,
                    acc = acc)

                output_file_creation(name)
    
    elif not mixed_vel and not mixed_acc:
        # Set up file names and the headers
        for i in range(1, number_of_parts+1):
            for acc in possible_accs:
                for vel in possible_vels:
                    name = create_name_based_on_mixing(
                        part_index = i,
                        number_of_parts = number_of_parts,
                        base_fileName = base_fileName,
                        out_dir = out_dir,
                        shape = shape,
                        vel = vel,
                        acc = acc)

                    output_file_creation(name)

    