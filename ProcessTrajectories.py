import argparse

from ProcessTrajectoriesUtils.TrajectoryProcessor import TrajectoryProcessor

def main(argv=None):

    parser = argparse.ArgumentParser('process')
    parser.add_argument('-s', '--source-dir', dest='source_dir', type=str,
                        required=True,
                        help='Directory holding the h5 or json files.')
    parser.add_argument('-o', '--out-dir', dest='out_dir', type=str,
                        help='Where to store results. If omitted, results ' +
                            'will be stored into the source directory.')
    parser.add_argument('-b', '--base-out-filename', dest='base_fileName', type=str,
                        help='The base name of all the output files.')
    parser.add_argument('-n', '--number-of-steps-in-one-example', dest='number_of_steps', type=int,
                        help='The number of consecutive states that each example of made of.'+
                             'The number of written files is also determined by this number.')
    parser.add_argument('-v', '--mixed-velocity', dest='mixed_vel', type=bool,
                        help='Should trajectories with different end-effector velocities be in the same output.')
    parser.add_argument('-a', '--mixed-acceleration', dest='mixed_acc', type=bool,
                        help='Should trajectories with different end-effector accelerations be in the same output')


    args = parser.parse_args(argv)


    pre = TrajectoryProcessor(args)
    pre._process_trajectories()
    

if __name__ == "__main__":
    main()
                    