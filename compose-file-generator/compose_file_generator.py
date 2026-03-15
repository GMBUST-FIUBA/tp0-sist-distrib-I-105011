from create_yaml_file import create_yaml_file

import sys

TOTAL_CLIENTS_ARG_POSITION = 2
FILE_NAME_ARG_POSITION = 1

def read_inv_arguments():
  return int(sys.argv[TOTAL_CLIENTS_ARG_POSITION]), sys.argv[FILE_NAME_ARG_POSITION]

if __name__ == "__main__":
  total_clients, file_name = read_inv_arguments()
  create_yaml_file(total_clients, file_name)