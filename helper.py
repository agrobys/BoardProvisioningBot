from webexteamssdk.models.cards import AdaptiveCard, TextBlock, Text
from webexteamssdk.models.cards.actions import Submit
from admin import Admin
from json import JSONDecodeError
import json


# Creates the adaptive card for getting activation code
def make_code_card() -> AdaptiveCard:
    greeting = TextBlock("Get an activation code:")
    workspace = Text('workspace', placeholder="Enter Workspace Name")
    # model = Text('model', placeholder="Enter Device Model (Optional)")
    submit = Submit(title="Provision")

    card = AdaptiveCard(
        body=[greeting, workspace], actions=[submit]
    )
    return card


# Creates the adaptive card for initializing a space for an organization
def make_init_card() -> AdaptiveCard:
    greeting = TextBlock("Please initialize bot for this space:")
    org_id = Text('org_id', placeholder="Enter organization ID")
    access_token = Text('access_token', placeholder="Enter your personal access token")
    submit = Submit(title="Init")

    card = AdaptiveCard(
        body=[greeting, org_id, access_token], actions=[submit]
    )
    return card


# creates an admin for an organization. Each space has one admin using the user specified token to
# perform actions on an organization.
def create_admin(admin_token, org_id, room_id):
    admin = Admin(admin_token, org_id, room_id)
    print("Admin created")
    return admin


# Adds readability to the activation code
def split_code(code) -> str:
    return code[:4] + '-' + code[4:8] + '-' + code[8:12] + '-' + code[12:]


def load_text(text):
    try:
        text = json.loads(text.content)
        return text
    except JSONDecodeError:
        return text


def is_json(text):
    try:
        text.json()
        return True
    except JSONDecodeError:
        return False
