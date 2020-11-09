import os
import sys
import numpy as np
import csv
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Polygon

from os import listdir
from os.path import isfile, join


class Visualiser:
    
    def __init__(self, args):
        # Set file to be visualised
        self.file = args.source_file
        # Set index of trajectory to visualise
        self.index = args.traj_index

    def visualise_trajectory(self, trajectory_dict):
        fig, ax = plt.subplots()

        # ------------------Extraction------------------
        # Extract object pose
        obj_np = trajectory_dict["obj"]
        # Extract tip pose
        tip_np = trajectory_dict["tip"]
        # Extract force/torque
        ft_np = trajectory_dict["ft"]
        # Extract nodes
        nodes_np = trajectory_dict["nodes"][:, :-2]
        nodes_np = np.reshape(nodes_np, (len(nodes_np), 4, 2))
        # Extract contact
        contact_np = trajectory_dict["contact"]

        center_loc_x = np.mean(obj_np[:, 0])
        center_loc_y = np.mean(obj_np[:, 1])

        zoom_out = 0.3

        ax.axis('equal')
        ax.set_xlim(center_loc_x-zoom_out,center_loc_x+zoom_out)
        ax.set_ylim(center_loc_y-zoom_out,center_loc_y+zoom_out)


        #Rectangle
        rect = Polygon(self.order_vertices(nodes_np[0]), closed=False, animated=False, alpha=0.5, color='b')
        ax.add_patch(rect)

        nodes, = ax.plot([], [], 'bo',label="Corners")
        end_effector, = ax.plot([], [], 'ro',label="End-Effector Tip")
        tip_orientation_indicator, = ax.plot([], [], '--r',label="Tip Orientation")
        force_indicator, = ax.plot([], [], ':g',label="Force")
        values_at_i = ax.text(center_loc_x - zoom_out*0.95, center_loc_y - zoom_out*0.7, "", size=10,
                va="baseline", ha="left", multialignment="left",
                bbox=dict(fc="none"))


        fig.suptitle("Visualisation of trajectory")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.legend(loc=2)

        def init():
            nodes.set_data([], [])
            end_effector.set_data([], [])
            tip_orientation_indicator.set_data([], [])
            force_indicator.set_data([], [])
            rect.set_xy(self.order_vertices(nodes_np[0]))
            return (nodes, end_effector, tip_orientation_indicator, force_indicator, values_at_i, rect)

        def animate(i):
            nodes_pos_i = nodes_np[i]
            tip_pos_i   = tip_np[i]
            
            # Corners
            x_cors = nodes_pos_i[:, 0]
            y_cors = nodes_pos_i[:, 1]    
            nodes.set_data(x_cors, y_cors)
            
            # End-effector Tip: Position
            x_tip = tip_pos_i[0]
            y_tip = tip_pos_i[1]
            end_effector.set_data(x_tip, y_tip)
            
            # End-effector Tip: Orientation
            en = np.array([x_tip, y_tip]) + np.array([0, 0.05])
            en = self.rotate_point(en, tip_pos_i[2])
            tip_orientation_indicator.set_data([x_tip, en[0]], [y_tip,en[1]])
            
            # Force Torque Sensor:  Forces
            ft = (np.array([x_tip, y_tip]) + (ft_np[i,:2]/10.0))
            force_indicator.set_data([x_tip, ft[0]], [y_tip, ft[1]])
            
            # Force Torque Sensor: Values
            ft_i = np.around(ft_np[i],4)
            str_to_disp = "\n".join(['FT Sensor:',
                                        'Force x: '+str(ft_i[0])+' N', 
                                        'Force y: '+str(ft_i[1])+' N', 
                                        'Torque: ' +str(ft_i[2])+' Nm',
                                    'In contact: ' +str(bool(contact_np[i]))])
            values_at_i.set_text(str_to_disp)
            
            # Rectangle
            nods = np.copy(nodes_pos_i)
            nods = self.order_vertices(nods)
            rect.set_xy(nods)
            
            # Update title
            ax.set_title("Current timestep: "+str(i))
            
            return (nodes, end_effector, tip_orientation_indicator, force_indicator, values_at_i, rect)

        anim = animation.FuncAnimation(fig, animate, init_func=init, frames=obj_np.shape[0], interval=20, blit=False)
        
        plt.show()

    
    
    def rotate_point(self, point,angle):
        mat = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        point = np.dot(mat, point)
        return point

    def order_vertices(self, ray):
        """
        This function reorders the vertices in an array for polygon vertices.
        We do this by:
            1. Compute the centroid of the "polygon"
            2. Compute the rays from the centroid to each of your "vertices".
            3. Use atan2 to compute the angle of this ray from the horizontal
            4. Sort the vertices according to this angle.
            ------------
            Source: https://uk.mathworks.com/matlabcentral/answers/366317-how-to-correctly-order-polygon-vertices , 
                    by Matt J
        
        Parameters
        ----------
        ray : np.array ,
            A numpy array of 2D points.
        
        Raises
        ------
        ValueError, 
            If ray is not a ndarray of 2D points 
            
        Returns
        -------
        sorted_ray : np.array ,
            Numpy array but sorted.
        
        """
        if (not len(ray.shape) == 2) or (not ray.shape[1] == 2):
            raise ValueError()
        try:
            center = np.mean(ray,axis=0)
            vectors = ray - center
            angles = np.arctan2(vectors[:,1],vectors[:,0])
            arr1inds = angles.argsort()
            sorted_ray = ray[arr1inds[::-1]]
        except Exception as e:
            print("Oops!", e.__class__, "occurred.")
            print()
        return sorted_ray

    def extract_trajectory(self, file, index):
        
        trajectory = np.array([])
        in_contact = np.array([])
        header = 0
        found_index = False
        #read csv, and split on "," the line
        with open(file, mode ='r') as fl: 
            # reading the CSV file 
            csv_file = csv.reader(fl, delimiter=",") 
            
            # displaying the contents of the CSV file 
            for row in csv_file:
                try:
                    traj_index = int(float(row[-2]))
                    if traj_index == index:
                        row[:-1] = [float(ele) for ele in row[:-1]]
                        row[-1] = row[-1] in ["True"]
                        found_index = True
                        # Append to trajectory
                        if len(trajectory) == 0:
                            trajectory = np.array([row])
                        else:
                            trajectory = np.append(trajectory, [row], axis=0)

                    if traj_index != index and found_index:
                        break
                except:
                    header = np.array(row)
                    #print(header)
                
        return trajectory

    def create_dictionary(self, trajectory):

        traj_dict = {}

        traj_dict["obj"] = trajectory[:, 11:14]

        traj_dict["tip"] = trajectory[:, 14:17]

        traj_dict["ft"] = trajectory[:, 17:20]

        traj_dict["nodes"] = trajectory[:, 1:11]
        
        traj_dict["contact"] = trajectory[:, -1]
        
        return traj_dict

    def visualise(self):
        # Extract trajectory
        trajectory = self.extract_trajectory(self.file, self.index)
        # Create dictionary
        traj_dict = self.create_dictionary(trajectory)
        # Visualise
        animation = self.visualise_trajectory(traj_dict)

