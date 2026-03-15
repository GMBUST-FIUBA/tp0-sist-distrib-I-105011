import yaml

from top_level.generate_top_level import generate_top_level
from services.generate_services import generate_services
from networks.generate_networks import generate_networks

def create_yaml_file(total_clients, file_name):
  top_level_elements = generate_top_level()
  services = generate_services(total_clients)
  networks = generate_networks()

  yaml_file_data = top_level_elements | services | networks

  with open(file_name, "w") as yaml_file:
    yaml.dump(yaml_file_data, yaml_file)