import argparse

from FlagNonContactUtils.DistanceFilter import DistanceFilter

def main(argv=None):

    parser = argparse.ArgumentParser('process')
    parser.add_argument('-s', '--source-dir', dest='source_dir', type=str,
                        required=True,
                        help='The directory holding the state file tuples.')
    parser.add_argument('-o', '--out-dir', dest='out_dir', type=str,
                        help='The directory where we output the filtered state file tuples.')
    parser.add_argument('-t', '--contact-distance-threshold', dest='threshold', type=float,
                        help='The distance at and beyond which the end effector is no longer considered to be in contact.')

    args = parser.parse_args(argv)

    pre = DistanceFilter(args)
    pre.flag_contacts()
    

if __name__ == "__main__":
    main()
                    