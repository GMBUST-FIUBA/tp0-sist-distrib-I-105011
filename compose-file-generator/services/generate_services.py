import copy
import yaml

# Constants
#
BASE_CLIENT_FILE_PATH = "./compose-file-generator/services/base_client_config.yaml"
SERVER_FILE_PATH = "./compose-file-generator/services/server_config.yaml"
ENV_FILE_PATH = "./client/data/test_client_bet.env"
BASE_BETS_FILE_PATH = "./.data/"
BASE_BETS_FILE_NAME = "agency-"
BASE_BETS_FILE_TYPE = ".csv"
BASE_BETS_CONTAINER_FILE_PATH = "/volumes/"

SERVICES_DOCKER_COMPOSE_TAG = "services"
CONTAINER_NAME_DOCKER_COMPOSE_TAG = "container_name"
CLIENT_NAME_START = "client"
ENVIRONMENT_DOCKER_COMPOSE_TAG = "environment"
ENVIRONMENT_FILE_DOCKER_COMPOSE_TAG = "env_file"
VOLUMES_DOCKER_COMPOSE_TAG = "volumes"
CLIENT_CLI_ID_DOCKER_COMPOSE_TAG = "CLI_ID="
AGENCY_NUMBER_DOCKER_COMPOSE_TAG = "AGENCY="

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

        # Set client ID and agency number
        current_client_cli_id = CLIENT_CLI_ID_DOCKER_COMPOSE_TAG + str(current_client_id)
        current_client_agency_number = AGENCY_NUMBER_DOCKER_COMPOSE_TAG + str(current_client_id)

        if ENVIRONMENT_DOCKER_COMPOSE_TAG not in current_client_elems:
            current_client_elems[ENVIRONMENT_DOCKER_COMPOSE_TAG] = []
        current_client_elems[ENVIRONMENT_DOCKER_COMPOSE_TAG].append(current_client_cli_id)
        current_client_elems[ENVIRONMENT_DOCKER_COMPOSE_TAG].append(current_client_agency_number)

        # Set environment file
        current_client_elems[ENVIRONMENT_FILE_DOCKER_COMPOSE_TAG] = ENV_FILE_PATH

        # Store new client
        clients[current_client_elems[CONTAINER_NAME_DOCKER_COMPOSE_TAG]] = current_client_elems

        # Set volumes files
        if VOLUMES_DOCKER_COMPOSE_TAG not in current_client_elems:
            current_client_elems[VOLUMES_DOCKER_COMPOSE_TAG] = []

        # Add bets files
        ## Bets file in project
        current_bets_file_name = BASE_BETS_FILE_NAME + str(current_client_id) + BASE_BETS_FILE_TYPE
        ## Bets file path in project
        current_project_bets_file_path = BASE_BETS_FILE_PATH + current_bets_file_name

        ## Bets file path in container
        current_container_bets_file_path = BASE_BETS_CONTAINER_FILE_PATH + current_bets_file_name

        ## Add volume list element
        volumes_list_element_bets_file = current_project_bets_file_path + ":" + current_container_bets_file_path
        current_client_elems[VOLUMES_DOCKER_COMPOSE_TAG].append(volumes_list_element_bets_file)

    return clients

def _generate_server():
    with open(SERVER_FILE_PATH, "r") as file:
        server = yaml.safe_load(file)
    return server