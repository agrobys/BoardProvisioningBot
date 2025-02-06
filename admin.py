from __future__ import print_function  # Needed if you want to have console output using Flask
import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError
import helper


# The entity making calls on the organization
class Admin:

    def __init__(self, my_token: str, org_id: str, room_id: str):
        self.my_token = my_token
        self.org_id = org_id
        self.room_id = room_id
        self.api = WebexTeamsAPI(access_token=self.my_token)
        self.headers = self.get_headers()
        try:
            self.my_id = self.api.people.me().id
        except ApiError:
            self.my_id = ""

    def token_is_valid(self):
        response = requests.get(
            url=f'https://webexapis.com/v1/workspaces?orgId={self.org_id}',
            headers=self.headers)
        response = helper.load_text(response)
        if isinstance(response, dict) and "items" in response.keys():
            print("Token valid.")
            return True
        else:
            print(f"Token assumed invalid. Response received: {response}")
            return False

    def update_token(self, token):
        self.my_token = token
        self.headers = self.get_headers()
        try:
            self.my_id = self.api.people.me().id
        except ApiError:
            self.my_id = ""
        return self.my_id

    def get_headers(self) -> dict:
        headers = {
            "Authorization": "Bearer " + self.my_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        return headers

    # Need to use requests library here since Webex SDK doesn't yet support workspaces & devices
    # Is called by get_activation_code. Checks if workspace name exists, creates workspace if not and returns ID
    def get_workspace_id(self, workspace_name) -> str:
        workspace_id = ""
        # Get ID for specified workspace name
        try:
            response = requests.get(
                url=f'https://webexapis.com/v1/workspaces?orgId={self.org_id}&displayName={workspace_name}',
                headers=self.headers)
        except ApiError:
            return ""
        if helper.is_json(response) and "items" in response.json().keys():
            for workspace in response.json()["items"]:
                workspace_id = workspace["id"]
        else:
            print(f"Something went wrong. Response: {helper.load_text(response)}")
            return ""
        # Create workspace if it doesn't exist
        if workspace_id == "":
            print(f"Creating workspace {workspace_name}.")
            payload = {
                "displayName": workspace_name,
                "orgId": self.org_id
            }
            try:
                response = requests.post(url="https://webexapis.com/v1/workspaces",
                                     data=json.dumps(payload), headers=self.headers)
            except ApiError:
                return ""
            # print(response.content)
            if helper.is_json(response):
                workspace_id = json.loads(response.content)["id"]
            else:
                print(f"Something went wrong. Response: {helper.load_text(response)}")
                return ""
        else:
            print(f"Workspace {workspace_id} exists.")
        return workspace_id

    # Need to use requests library here since Webex SDK doesn't yet support workspaces & devices
    # Gets activation code for a workspace
    def get_activation_code(self, workspace_name, model=None) -> str:
        # check if token is valid
        if not self.token_is_valid():
            return ""
        # Get ID for specified workspace name
        workspace_id = self.get_workspace_id(workspace_name)
        if workspace_id == "":
            return ""
        payload = {"workspaceId": workspace_id}
        if model:
            payload["model"] = model
        # Create activation code
        try:
            response = requests.post(url="https://webexapis.com/v1/devices/activationCode?orgId=" + self.org_id,
                                 data=json.dumps(payload), headers=self.headers)
        except ApiError:
            return ""
        if helper.is_json(response):
            activation_code = json.loads(response.content)["code"]
            return activation_code
        else:
            print(f"Something went wrong. Response: {helper.load_text(response)}")
            return ""

    def save(self):
        data = {
            "admin_token": self.my_token,
            "org_id": self.org_id
        }
        return data

