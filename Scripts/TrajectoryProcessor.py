import os
import sys
import numpy as np
import h5py
import pandas as pd
import zipfile
import shutil
import logging
import csv

from os import listdir
from os.path import isfile, join

from Scripts.FileManipulationTools import read_file, create_name_based_on_mixing, collect_trajectory_properties, _setup_output
from Scripts.DataManipulationTools import get_corner_positions, get_node_positions, sample_dataset, clear_dataset


class TrajectoryProcessor:
    
    def __init__(self, args):    
        # Setup logging
        self.setup_logging(args)

        # Set source_dir
        self.source_dir = args.source_dir
        # Set out_dir
        self.out_dir = 'processed_dataset'
        if not args.out_dir == None:
            self.out_dir = args.out_dir
        # Set base file name 
        self.base_fileName = "MIT_Push_state_tuple_part"
        if not args.base_fileName == None:
            self.base_fileName = args.base_fileName
        # Set number of steps variable
        self.number_of_steps = 2
        if not args.number_of_steps == None:
            self.number_of_steps = args.number_of_steps
        # Mix velocities
        self.mixed_vel = True
        if not args.mixed_vel == None:
            self.mixed_vel = args.mixed_vel
        # Mix accelerations
        self.mixed_acc = True
        if not args.mixed_acc == None:
            self.mixed_acc = args.mixed_acc
        
        # Create out_dir if it doesn't exist
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        # If source directiory doesn't exist throw an error        
        if not os.path.exists(self.source_dir):
            raise ValueError('source directory does not exist: ' +
                             self.source_dir)


    def setup_logging(self, args):
        # setup logging
        self.log = logging.getLogger('data_parser')
        self.log.setLevel(logging.DEBUG)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s: [%(name)s] ' +
                                      '[%(levelname)s] %(message)s')

        # create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        self.log.addHandler(ch)

        # create file handler which logs warnings errors and criticals
        if os.path.exists(os.path.join(args.source_dir,'logs', 'error.log')):
            os.remove(os.path.join(args.source_dir,'logs', 'error.log'))
        else:
            os.makedirs(os.path.join(args.source_dir,'logs'))

        fh = logging.FileHandler(os.path.join(args.source_dir,'logs', 'error.log'))
        fh.setLevel(logging.WARNING)
        fh.setFormatter(formatter)
        self.log.addHandler(fh)

    # Create pandas dataframe from the dictionary supplied from the read 
    def create_pandas_dataframes(self, dict_obj):
        """Given a dictionary object dict_obj

        If the argument `sound` isn't passed in, the default Animal
        sound is used.

        Parameters
        ----------
        dict_obj : dict ,
            A dictionary with 3 keys: object_pose, tip_pose, ft_wrench
            For each key, there is a collection of 4D vectors.

        Raises
        ------
        ValueError
            If no dict_obj is supplied to the function
        
        Returns
        -------
        obj_pd, tip_pd, ft_pd : pandas.dataframe ,
            3 pandas DataFrames one for the object, one for tip and one for the force/torque sensor
            Each dataframe has the time as its key/index
    
        """
        if dict_obj is None:
            raise ValueError("The file supplied is none!")
    
        try:
            obj_pd = pd.DataFrame(dict_obj['object_pose'], columns=['time', 'x', 'y', 'orientation'])
            tip_pd = pd.DataFrame(dict_obj['tip_pose']   , columns=['time', 'x', 'y', 'orientation'])
            ft_pd  = pd.DataFrame(dict_obj['ft_wrench']  , columns=['time','force_x', 'force_y','torque'])

            obj_pd["time"] = pd.to_datetime(obj_pd["time"], unit='s')
            tip_pd["time"] = pd.to_datetime(tip_pd["time"], unit='s')
            ft_pd["time"]  = pd.to_datetime(ft_pd["time"] , unit='s')

            obj_pd = obj_pd.set_index('time')
            tip_pd = tip_pd.set_index('time')
            ft_pd  = ft_pd.set_index('time')
            
            return (obj_pd, tip_pd, ft_pd)

        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
            print()

    # From a list of corner positions (states) create examples (state tuples)
    def _create_examples_and_write_file(self, cr_eg_index, traj, props, shape):
        vel = None
        acc = None
        if not self.mixed_vel:
            vel = props['vel']
        if not self.mixed_acc:
            acc = props['acc']


        tr_ind = list(range(len(traj)))
        
        # Create example pair indeces
        if self.number_of_steps == 2:
            example_inds = list(zip(tr_ind, tr_ind[1:] + tr_ind[:1]))
            example_inds = example_inds[:-(self.number_of_steps-1)]
            
        elif self.number_of_steps == 3:
            example_inds = list(zip(tr_ind, tr_ind[1:] + tr_ind[:1], tr_ind[2:] + tr_ind[:2]))
            example_inds = example_inds[:-(self.number_of_steps-1)]
            
        elif self.number_of_steps == 4:
            example_inds = list(zip(tr_ind, tr_ind[1:] + tr_ind[:1], tr_ind[2:] + tr_ind[:2], tr_ind[3:] + tr_ind[:3]))
            example_inds = example_inds[:-(self.number_of_steps-1)]
            
        else:
            raise ValueError("number_of_steps has to be either 2, 3, or 4!!! Value you supplied was: "+ str(self.number_of_steps))
        
        
        examples_collected = {} 
        # Get the states at these indeces
        for example_indexes in example_inds:
            eg = traj[list(example_indexes)]
            """
            Each example has number_of_steps states,
            each state is written to a file that contains 
            states at the same timesteps compared to 
            the first state in the example.
            """
            
            for example, eg_ind in zip(eg, range(1,len(eg)+1)):
                if eg_ind in examples_collected:
                    current = examples_collected[eg_ind]
                    examples_collected[eg_ind] = np.vstack((current,example))
                else:
                    examples_collected[eg_ind] = np.array(example)

        #print("---------------------")
        #print(examples_collected)
        #print("---------------------")
        
        cr_eg_index_alt = 0
        for eg_ind in examples_collected:      
            #Write the datasets
            cr_eg_index_alt = cr_eg_index
            with open(
                    create_name_based_on_mixing(
                        part_index = eg_ind,
                        number_of_parts = self.number_of_steps,
                        base_fileName = self.base_fileName,
                        out_dir = self.out_dir,
                        shape = shape,
                        vel = vel,
                        acc = acc),
                    'a', newline='') as file:
                    
                csv_writer = csv.writer(file)
                for example in examples_collected[eg_ind]:
                    lin = np.concatenate(([cr_eg_index_alt], example))
                    csv_writer.writerow(lin)
                    # Update the index so that the each example in the dataset is uniquely indexed
                    cr_eg_index_alt = cr_eg_index_alt + 1
            
        return cr_eg_index_alt
    
    # From a list of lists of corner positions create examples 
    # (This additional loop is required to account for the removed datapoints,
    # as they are not simply removed by splitted upon.)
    # This function ensures that there are no jumps between incosequtive states
    def _create_list_of_examples(self, processed_nps, cr_eg_index, props, shape):
        """
        This function takes in a list of numpy arrays. 
        Each ndarray in the list is an unbroken (no jumps) trajectory where
        the delta time between any two consequtive states is a constant.

        Besides the list we also take a number_of_steps parameter, 
        which defines how many consequtive states are in every example.

        An example in our case is a n = number_of_steps long list of consequtive states.

        This function will do as the following:
        Lets assume that we have the following indeces in one of the ndarrays inside the processed_nps:
        | 1 2 3 4 5 6 7 |
        Furthermore, assume that number_of_steps = 2, then l_examples is going to be extended by the following examples list:
        [| 1 2 |, | 2 3 |, | 3 4 |, | 4 5 |, | 5 6 |, | 6 7 |]


        Parameters
        ----------
        processed_nps : list ,
            A list of ndarrays.
        cr_eg_index: int ,
            The current index inside the output files.
        props: dictionary,
            The properties of the trajectory: velocity and acceleration of the end effector

        Raises
        ------
        ValueError
            If number_of_steps is not 2, 3, 4, or 5
            If processed_nps is not a list or elements of processed_nps are not ndarrays

        Returns
        -------
        the current example index, but writes a csv document at the out_dir folder

        """
        # For each of the 
        for traj in processed_nps:
            cr_eg_index = self._create_examples_and_write_file(cr_eg_index, traj, props, shape)
        
        return cr_eg_index

    # Process the contents of a single file 
    def _process_trajectory(self, dict_obj, shape):
        # Convert to dataframe
        obj_pd, tip_pd, ft_pd = self.create_pandas_dataframes(dict_obj)
        # Get rid of redundant entries and ensuring temporal ordering

        # Treat orientation jumps, limit the range of orientation values

        # Downsample
        obj_pd_sampled, tip_pd_sampled, ft_pd_sampled = sample_dataset('10ms', obj_pd, tip_pd, ft_pd)
        # Drop nan values
        obj_pd_dropped, tip_pd_dropped, ft_pd_dropped = clear_dataset(obj_pd_sampled, tip_pd_sampled, ft_pd_sampled)
        # Get Corner Positions
        obj_np = get_corner_positions(shape, obj_pd_dropped)
        # Add the end-effector to the corner positions
        nodes_np = get_node_positions(obj_np, tip_pd_dropped)
        

        # Uniform obj_nps
        if len(nodes_np.shape) == 3:
            # Flatten into a vector
            nodes_np = nodes_np.reshape((len(nodes_np), 12))
            nodes_np = np.array([nodes_np])
        elif len(nodes_np.shape) == 4:
            nodes_np = nodes_np.reshape((len(nodes_np), nodes_np.shape[1], 12))

        return nodes_np

    # Process all the files in the folder
    def _process_trajectories(self):
        # Collect all the files in the directory.
        files = [f for f in listdir(self.source_dir) if isfile(join(self.source_dir, f))]

        # Get shape of processed objects
        shape = os.path.split(self.source_dir)[1]


        _setup_output(
            base_fileName=self.base_fileName,
            number_of_parts=self.number_of_steps,
            out_dir=self.out_dir,
            shape = shape,
            mixed_acc=self.mixed_acc,
            mixed_vel=self.mixed_vel)

        # Set index to 0
        cr_eg_index = 0
        for f in files:
            # Read file
            dict_obj = read_file(self.source_dir, f)
            # Get properties:
            properties = collect_trajectory_properties(f)
            # Process file
            processed_nps = self._process_trajectory(dict_obj, shape)
            # Write example tuple following multi 
            cr_eg_index = self._create_list_of_examples(processed_nps, cr_eg_index, properties, shape)