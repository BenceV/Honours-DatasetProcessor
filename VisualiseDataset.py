import argparse

from VisualiseDatasetUtils.Visualiser import Visualiser

def main(argv=None):

    parser = argparse.ArgumentParser('process')
    parser.add_argument('-f', '--file', dest='source_file', type=str,
                        required=True,
                        help='The file holding the trajectory.')
    parser.add_argument('-i', '--trajectory-index', dest='traj_index', type=int,
                        required=True,
                        help='The index of the trajectory we want to visualise')

    args = parser.parse_args(argv)

    pre = Visualiser(args)
    pre.visualise()
    

if __name__ == "__main__":
    main()
                    