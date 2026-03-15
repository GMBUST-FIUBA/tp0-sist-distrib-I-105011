import copy
import yaml

# Constants
#
BASE_CLIENT_FILE_PATH = "./compose-file-generator/services/base_client_config.yaml"
SERVER_FILE_PATH = "./compose-file-generator/services/server_config.yaml"

SERVICES_DOCKER_COMPOSE_TAG = "services"
CONTAINER_NAME_DOCKER_COMPOSE_TAG = "container_name"
CLIENT_NAME_START = "client"
ENVIRONMENT_DOCKER_COMPOSE_TAG = "environment"
CLIENT_CLI_ID_DOCKER_COMPOSE_TAG = "CLI_ID="

def generate_services(total_clients):
    server = _generate_server()
    clients = _generate_clients(total_clients)

    return {SERVICES_DOCKER_COMPOSE_TAG : server | clients}

def _generate_clients(total_clients):
    with open(BASE_CLIENT_FILE_PATH, "r") as file:
        base_client = yaml.safe_load(file)

    clients = {}

    for current_client_id in range(1, total_clients+1):
        current_client_elems = copy.deepcopy(base_client)

        # Change client name
        current_client_elems[CONTAINER_NAME_DOCKER_COMPOSE_TAG] += str(current_client_id)

        # Set client ID
        current_client_cli_id = CLIENT_CLI_ID_DOCKER_COMPOSE_TAG + str(current_client_id)
        current_client_elems[ENVIRONMENT_DOCKER_COMPOSE_TAG].append(current_client_cli_id)

        # Store new client
        clients[current_client_elems[CONTAINER_NAME_DOCKER_COMPOSE_TAG]] = current_client_elems


    return clients

def _generate_server():
    with open(SERVER_FILE_PATH, "r") as file:
        server = yaml.safe_load(file)
    return server