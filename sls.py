from collections import defaultdict
import requests
import urllib3
import sys
from kubernetes import client, config
import base64
import json

def pull_sls_networks():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    debug = False

    def on_debug(debug=False, message=None):
        if debug:
            print("DEBUG: {}".format(message))

    #
    # Convenience wrapper around remote calls
    #
    def remote_request(
        remote_type, remote_url, headers=None, data=None, verify=True, debug=False
    ):
        remote_response = None
        while True:
            try:
                response = requests.request(
                    remote_type, url=remote_url, headers=headers, data=data, verify=verify
                )
                on_debug(debug, "Request response: {}".format(response.text))
                response.raise_for_status()
                remote_response = json.dumps({})
                if response.text:
                    remote_response = response.json()
                break
            except Exception as err:
                message = "Error calling {}: {}".format(remote_url, err)
                raise SystemExit(message)
        return remote_response

    #
    # Get the admin client secret from Kubernetes
    #
    secret = None
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        secret_obj = v1.list_namespaced_secret(
            "default", field_selector="metadata.name=admin-client-auth"
        )
        secret_dict = secret_obj.to_dict()
        secret_base64_str = secret_dict["items"][0]["data"]["client-secret"]
        on_debug(debug, "base64 secret from Kubernetes is {}".format(secret_base64_str))
        secret = base64.b64decode(secret_base64_str.encode("utf-8"))
        on_debug(debug, "secret from Kubernetes is {}".format(secret))
    except Exception as err:
        print("Error collecting secret from Kubernetes: {}".format(err))
        sys.exit(1)

    #
    # Get an auth token by using the secret
    #
    token = None
    try:
        token_url = "https://api-gw-service-nmn.local/keycloak/realms/shasta/protocol/openid-connect/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": "admin-client",
            "client_secret": secret,
        }
        token_request = remote_request("POST", token_url, data=token_data, debug=debug)
        token = token_request["access_token"]
        on_debug(
            debug=debug,
            message="Auth Token from keycloak (first 50 char): {}".format(token[:50]),
        )
    except Exception as err:
        print("Error obtaining keycloak token: {}".format(err))
        sys.exit(1)


    #
    # Get existing SLS data for comparison (used as a cache)
    #
    sls_cache = None
    sls_url = "https://api_gw_service.local/apis/sls/v1/networks"
    auth_headers = {"Authorization": "Bearer {}".format(token)}
    try:
        sls_cache = remote_request("GET", sls_url, headers=auth_headers, verify=False)
        on_debug(debug=debug, message="SLS data has {} records".format(len(sls_cache)))
    except Exception as err:
        print("Error requesting Networks from SLS: {}".format(err))
        sys.exit(1)
    on_debug(debug=debug, message="SLS records {}".format(sls_cache))

    return(sls_cache)

def parse_sls_file():
    """Parse the `sls_input_file.json` file or the JSON from SLS `/networks` API for config variables.
    
    Args:
        input_json: JSON from the SLS `/networks` API

    Returns:
        sls_variables: Dictionary containing SLS variables.
    """
    networks_list = []
    input_json = pull_sls_networks()
    sls_variables = {
        "CAN": None,
        "HMN": None,
        "MTL": None,
        "NMN": None,
        "HMN_MTN": None,
        "NMN_MTN": None,
        "CAN_IP_GATEWAY": None,
        "HSN_IP_GATEWAY": None,
        "HMN_IP_GATEWAY": None,
        "MTL_IP_GATEWAY": None,
        "NMN_IP_GATEWAY": None,
        "ncn_w001": None,
        "ncn_w002": None,
        "ncn_w003": None,
        "CAN_IP_PRIMARY": None,
        "CAN_IP_SECONDARY": None,
        "HMN_IPs": defaultdict(),
        "MTL_IPs": defaultdict(),
        "NMN_IPs": defaultdict(),
        "NMN_MTN_CABINETS": [],
        "HMN_MTN_CABINETS": [],
    }

    for sls_network in input_json:
        name = sls_network.get("Name", "")

        if name == "CAN":
            sls_variables["CAN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):
                if subnets["Name"] == "bootstrap_dhcp":
                    sls_variables["CAN_IP_GATEWAY"] = subnets["Gateway"]
                    for ip in subnets["IPReservations"]:
                        if ip["Name"] == "can-switch-1":
                            sls_variables["CAN_IP_PRIMARY"] = ip["IPAddress"]
                        elif ip["Name"] == "can-switch-2":
                            sls_variables["CAN_IP_SECONDARY"] = ip["IPAddress"]

        elif name == "HMN":
            sls_variables["HMN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):
                if subnets["Name"] == "network_hardware":
                    sls_variables["HMN_IP_GATEWAY"] = subnets["Gateway"]
                    for ip in subnets["IPReservations"]:
                        sls_variables["HMN_IPs"][ip["Name"]] = ip["IPAddress"]
        
        elif name == "HSN":
            sls_variables["HSN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):
                if subnets["Name"] == "hsn_base_subnet":
                    sls_variables["HSN_IP_GATEWAY"] = subnets["Gateway"]

        elif name == "MTL":
            sls_variables["MTL"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):
                if subnets["Name"] == "network_hardware":
                    sls_variables["MTL_IP_GATEWAY"] = subnets["Gateway"]
                    for ip in subnets["IPReservations"]:
                        sls_variables["MTL_IPs"][ip["Name"]] = ip["IPAddress"]

        elif name == "NMN":
            sls_variables["NMN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):
                if subnets["Name"] == "bootstrap_dhcp":
                    for ip in subnets["IPReservations"]:
                        if ip["Name"] == "ncn-w001":
                            sls_variables["ncn_w001"] = ip["IPAddress"]
                        elif ip["Name"] == "ncn-w002":
                            sls_variables["ncn_w002"] = ip["IPAddress"]
                        elif ip["Name"] == "ncn-w003":
                            sls_variables["ncn_w003"] = ip["IPAddress"]
                elif subnets["Name"] == "network_hardware":
                    sls_variables["NMN_IP_GATEWAY"] = subnets["Gateway"]
                    for ip in subnets["IPReservations"]:
                        sls_variables["NMN_IPs"][ip["Name"]] = ip["IPAddress"]

        elif name == "NMN_MTN":
            sls_variables["NMN_MTN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            sls_variables["NMN_MTN_CABINETS"] = [
                subnet
                for subnet in sls_network.get("ExtraProperties", {}).get("Subnets", {})
            ]
        elif name == "HMN_MTN":
            sls_variables["HMN_MTN"] = sls_network.get("ExtraProperties", {}).get(
                "CIDR", ""
            )
            sls_variables["HMN_MTN_CABINETS"] = [
                subnet
                for subnet in sls_network.get("ExtraProperties", {}).get("Subnets", {})
            ]

        for subnets in sls_network.get("ExtraProperties", {}).get("Subnets", {}):

            vlan = subnets.get("VlanID", "")
            networks_list.append([name, vlan])

    networks_list = set(tuple(x) for x in networks_list)

    return sls_variables