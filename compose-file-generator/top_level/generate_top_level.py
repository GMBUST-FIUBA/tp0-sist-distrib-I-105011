import yaml

FILE_PATH = "./composite-file-generator/top_level/top_level_config.yaml"

def generate_top_level():
    with open(FILE_PATH, "r") as file:
        top_level = yaml.safe_load(file)
    return top_level