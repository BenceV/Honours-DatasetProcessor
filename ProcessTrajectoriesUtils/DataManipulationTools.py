import numpy as np

# Based on the type of rigidbody extrapolate the corners of the object from its position and orientation
def get_node_positions(obj_name, obj_pd):
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
    
    # Convert dataframe to numpy 
    obj_np = obj_pd.to_numpy()
    cents = obj_np[:, 0:2]
    angles = obj_np[:, 2]
    # List of supported shapes
    supported_shapes = ["rect1","rect2","rect3"]
    
    
    # Get the dimensions of the rectangle
    a = 0
    b = 0
    if obj_name not in supported_shapes:
        raise NotImplementedError("The shapes supported are: ", [str(a) for a in supported_shapes])
    else:
        if obj_name == "rect1":
            a = 0.0450
            b = 0.0450

        if obj_name == "rect2":
            a = 0.0450
            b = 0.0563

        if obj_name == "rect3":
            a = 0.0675
            b = 0.0450
    
    # t_r: top-right corner
    # t_l: top-left corner
    # b_r: bottom-right corner
    # b_l: bottom-left corner
    t_r = np.zeros((cents.shape[0],2)) + [a,b]
    t_l = np.zeros((cents.shape[0],2)) + [-a,b]
    b_r = np.zeros((cents.shape[0],2)) + [a,-b]
    b_l = np.zeros((cents.shape[0],2)) + [-a,-b]
    
    # for all center locations rotate the corner by the corresponding angle
    for i, angle in zip(range(cents.shape[0]), angles):        
        t_r[i] = rotate_point(t_r[i], angle)
        t_l[i] = rotate_point(t_l[i], angle) 
        b_r[i] = rotate_point(b_r[i], angle)  
        b_l[i] = rotate_point(b_l[i], angle)
    
    # Corners are calculated by adding the center locations to them
    t_r = np.copy(cents) + t_r
    t_l = np.copy(cents) + t_l
    b_r = np.copy(cents) + b_r
    b_l = np.copy(cents) + b_l
    
    # Create a single numpy collection 
    corns_np = np.append(t_r,t_l,axis=1)
    corns_np = np.append(corns_np,b_r,axis=1)
    corns_np = np.append(corns_np,b_l,axis=1)
    corns_np = np.append(corns_np,cents,axis=1)
    
    
    corns_np = corns_np.reshape((corns_np.shape[0],5,2))

    return corns_np

def get_states(nodes_np, object_pd, endeffector_pd, forceTorque_pd, velocity, acceleration, traj_index):
    # Convert dataframe to numpy 
    object_np      = np.array([object_pd.to_numpy()])
    endeffector_np = np.array([endeffector_pd.to_numpy()])
    forceTorque_np = np.array([forceTorque_pd.to_numpy()])
    # Broacastable scalars
    velocity_np = np.tile(velocity, (1, object_np.shape[1], 1))
    acceleration_np = np.tile(acceleration, (1, object_np.shape[1], 1))
    traj_index_np = np.tile(traj_index, (1, object_np.shape[1], 1))

    # Uniform obj_nps
    if len(nodes_np.shape) == 3:
        # Flatten into a vector
        nodes_np = nodes_np.reshape((len(nodes_np), 10))
        nodes_np = np.array([nodes_np])
    elif len(nodes_np.shape) == 4:
        nodes_np = nodes_np.reshape((len(nodes_np), nodes_np.shape[1], 10))

    # Append previous values
    states_np = np.append(nodes_np, object_np, axis=2)
    states_np = np.append(states_np, endeffector_np, axis=2)
    states_np = np.append(states_np, forceTorque_np, axis=2)
    # Append scalars
    states_np = np.append(states_np, velocity_np, axis=2)
    states_np = np.append(states_np, acceleration_np, axis=2)
    states_np = np.append(states_np, traj_index_np, axis=2)
    return states_np



# Rotate the corners according to the orientation of the object
def rotate_point(point, angle):
    mat = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    point = np.dot(mat, point)
    return point

# Resample the dataset so that measurement frequency inconsistencies are accounted for
def sample_dataset(string_amount, obj_pd, tip_pd, ft_pd):
    # Resample and interpolate using the mean
    # TODO : Cut the list into two consequtive timesteps are too far apart
    obj_pd = obj_pd.resample(string_amount).mean()
    tip_pd = tip_pd.resample(string_amount).mean()
    ft_pd = ft_pd.resample(string_amount).mean()

    return obj_pd, tip_pd, ft_pd
    
# Remove any none, null, infinite and any other kind of problematic values
def clear_dataset(obj_pd, tip_pd, ft_pd):

    latest_start = max(min(list(obj_pd.index.values)), min(list(tip_pd.index.values)), min(list(ft_pd.index.values)))
    earliest_end = min(max(list(obj_pd.index.values)), max(list(tip_pd.index.values)), max(list(ft_pd.index.values)))
    
    # Drop rows where the earliest end is sooner
    earliest_obj = obj_pd[obj_pd.index.values >= earliest_end].index
    earliest_tip = tip_pd[tip_pd.index.values >= earliest_end].index
    earliest_ft = ft_pd[ft_pd.index.values >= earliest_end].index

    obj_pd.drop(earliest_obj , inplace=True, errors = 'ignore')
    tip_pd.drop(earliest_tip , inplace=True, errors = 'ignore')
    ft_pd.drop(earliest_ft , inplace=True, errors = 'ignore')

    # Drop rows where the latest start is later
    latest_obj = obj_pd[obj_pd.index.values <= latest_start].index
    latest_tip = tip_pd[tip_pd.index.values <= latest_start].index
    latest_ft = ft_pd[ft_pd.index.values <= latest_start].index
    
    obj_pd.drop(latest_obj , inplace=True, errors = 'ignore')
    tip_pd.drop(latest_tip , inplace=True, errors = 'ignore')
    ft_pd.drop(latest_ft , inplace=True, errors = 'ignore')

    # Drop nan rows
    inds_obj = obj_pd[obj_pd.isnull().any(1)]
    inds_tip = tip_pd[tip_pd.isnull().any(1)]
    inds_ft  = ft_pd[ft_pd.isnull().any(1)]

    con_inds = list(inds_obj.index.values) + list(inds_tip.index.values) + list(inds_ft.index.values)
    obj_pd.drop(con_inds, inplace=True, errors = 'ignore')
    tip_pd.drop(con_inds, inplace=True, errors = 'ignore')
    ft_pd.drop(con_inds, inplace=True, errors = 'ignore')

    return obj_pd, tip_pd, ft_pd