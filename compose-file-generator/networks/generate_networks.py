import yaml

FILE_PATH = "./compose-file-generator/networks/networks_config.yaml"

def generate_networks():
    with open(FILE_PATH, "r") as file:
        networks = yaml.safe_load(file)
    return networks