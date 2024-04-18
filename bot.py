from __future__ import print_function  # Needed if you want to have console output using Flask
from webexteamssdk import WebexTeamsAPI
from webexteamssdk.models.cards import AdaptiveCard, TextBlock, Text
from webexteamssdk.models.cards.actions import Submit
from admin import Admin
import json


# Creates the adaptive card that will be sent to users to fill in information.
# Activation code will be generated based on the user input in this card
def make_code_card() -> AdaptiveCard:
    greeting = TextBlock("Get an activation code:")
    workspace = Text('workspace', placeholder="Enter Workspace Name")
    # model = Text('model', placeholder="Enter Device Model (Optional)")
    submit = Submit(title="Provision")

    card = AdaptiveCard(
        body=[greeting, workspace], actions=[submit]
    )
    return card


def make_init_card() -> AdaptiveCard:
    greeting = TextBlock("Please initialize bot for this space:")
    org_id = Text('org_id', placeholder="Enter organization ID")
    access_token = Text('access_token', placeholder="Enter your personal access token")
    submit = Submit(title="Init")

    card = AdaptiveCard(
        body=[greeting, org_id, access_token], actions=[submit]
    )
    return card


def create_admin(admin_token, org_id):
    admin = Admin(admin_token, org_id)
    print("Admin created")
    return admin


# Adds readability to the activation code
def split_code(code) -> str:
    return code[:4] + '-' + code[4:8] + '-' + code[8:12] + '-' + code[12:]


# The entity communicating with the user
class Bot:

    def __init__(self, data):
        self.name = data["bot_name"]
        self.bot_token = data["bot_token"]
        self.api = WebexTeamsAPI(access_token=self.bot_token)
        self.id = self.api.people.me().id
        self.email = data["bot_email"]
        self.code_card = make_code_card()
        self.init_card = make_init_card()

        self.https_tunnel = None
        self.webhooks = []

        self.orgs = data["orgs"]
        self.org_admin = {}
        self.room_to_org = data["room_to_org"]
        for org in data["org_admin"].keys():
            admin = create_admin(data["org_admin"][org]["my_token"], data["org_admin"][org]["org_id"])
            if admin.my_id == "":
                for room in self.room_to_org.keys():
                    if self.room_to_org[room] == org:
                        self.reinit(room)
            else:
                self.org_admin[org] = admin
        self.org_allowed_users = data["org_allowed_users"]
        self.org_id_to_email = data["org_id_to_email"]

    def startup(self) -> None:
        webhooks = self.api.webhooks.list()
        for webhook in webhooks:
            self.webhooks.append(webhook)
        if len(self.webhooks) < 4:
            print("Don't have all webhooks. Please verify")

    def save(self):
        admins_saved = {}
        for org in self.org_admin.keys():
            admins_saved[org] = self.org_admin[org].save()
        data = {
            "bot_name": self.name,
            "bot_token": self.bot_token,
            "bot_email": self.email,
            "orgs": self.orgs,
            "org_admin": admins_saved,
            "org_allowed_users": self.org_allowed_users,
            "room_to_org": self.room_to_org,
            "org_id_to_email": self.org_id_to_email
        }
        with open("bot_data.json", "w") as file:
            json.dump(data, file)

    def teardown(self) -> None:
        self.save()

    def reinit(self, room_id):
        self.api.messages.create(roomId=room_id, text="Access token expired or not valid. Reinitializing...")
        self.api.messages.create(room_id, text="Please initialize", attachments=[self.init_card])

    def init_org(self, org_id, access_token, room_id, user_id):
        try:
            admin = self.org_admin[org_id]
            print("Org exists")
            if admin.my_id == "":
                admin_id = admin.update_token(access_token)
                if admin_id == "":
                    self.reinit(room_id)
                    return None
            if user_id not in self.org_allowed_users[org_id]:
                print("Adding user to allowed")
                self.org_allowed_users[org_id].append(user_id)
        except KeyError:
            print("Org doesn't exist. Creating")
            admin = create_admin(access_token, org_id)
            if not admin.check_org_connectivity():
                del admin
                return None
            self.org_admin[org_id] = admin
            self.org_allowed_users[org_id] = [user_id]
            self.org_id_to_email[org_id] = {}
        email = admin.get_email_from_id(user_id)
        self.org_id_to_email[org_id][user_id] = email
        self.room_to_org[room_id] = org_id
        return admin

    def remove_room_from_org(self, room_id):
        del self.room_to_org[room_id]

    def add_allowed_user(self, org_id, email):
        admin = self.org_admin[org_id]
        user_id = admin.get_id_from_email(email)
        if user_id != "" and user_id not in self.org_allowed_users[org_id]:
            self.org_allowed_users[org_id].append(user_id)
        return user_id

    def remove_allowed_user(self, org_id, email):
        admin = self.org_admin[org_id]
        user_id = admin.get_id_from_email(email)
        if user_id != "" and user_id in self.org_allowed_users[org_id]:
            self.org_allowed_users[org_id].remove(user_id)
            return user_id
        else:
            return ""

    def handle_added(self, room_id):
        self.api.messages.create(room_id, text="Hello! I'm here to help you provision Webex Boards for your "
                                               "organization. Please provide me with your organization ID and an "
                                               "admin's access token.")
        self.api.messages.create(room_id, text="Please initialize", attachments=[self.init_card])

    def handle_removed(self, room_id):
        org_id = self.room_to_org[room_id]
        self.remove_room_from_org(room_id)
        if org_id not in self.room_to_org.values():
            del self.org_admin[org_id]
            del self.org_allowed_users[org_id]
            del self.org_id_to_email[org_id]

    # Is called when card was submitted. Asks Admin to create activation code and sends it in the chat
    def handle_card(self, attachment_id, room_id, actor_id):
        card_input = self.api.attachment_actions.get(id=attachment_id)
        try:
            org_id = self.room_to_org[room_id]
            admin = self.org_admin[org_id]
        except KeyError:
            try:
                org_id = card_input.inputs["org_id"]
                access_token = card_input.inputs["access_token"]
                admin = self.init_org(org_id, access_token, room_id, actor_id)
                if admin:
                    self.api.messages.create(room_id, text="Initialization success.")
                else:
                    self.api.messages.create(room_id, text="Initialization unsuccessful. Please check your "
                                                           "organization ID and access token or contact "
                                                           "agrobys@cisco.com for assistance.")
            except KeyError:
                self.api.messages.create(room_id, text="Please initialize", attachments=[self.init_card])
                return
        if actor_id in self.org_allowed_users[org_id]:
            print(f"User {self.org_id_to_email[org_id][actor_id]} allowed.")
            try:
                workspace_name = card_input.inputs["workspace"]
            except KeyError:
                self.api.messages.create(room_id, text="Bot initialized. If you need to update the access token, "
                                                       "please use the 'reinit' command, or type "
                                                       "'help' to view all available commands.")
                return
            # model = card_input.inputs["model"]
            # if model != "":
            #     activation_code = get_activation_code(workspace_name, model=model)
            activation_code = admin.get_activation_code(workspace_name)
            if activation_code == "":
                self.api.messages.create(room_id,
                                         text="Something went wrong. Please check if you need to update the access "
                                              "token.")
            activation_code = split_code(activation_code)
            print(f"Sending activation code.")
            self.api.messages.create(room_id, text=f"Here's your activation code: {activation_code}")
        else:
            print(f"User {self.org_id_to_email[org_id][actor_id]} unauthorized.")
            self.api.messages.create(room_id, text=f"You're unauthorized. Please contact the person who initialized "
                                                   f"the bot if you require access.")

    # Is called when bot is mentioned. Checks for commands (if no special command is detected, it will send the
    # adaptive card)
    def handle_command(self, message, room_id, actor_id) -> None:
        # Ignore @All mentions
        if message.split()[0] == "All":
            return
        # Make sure bot is initialized for this room
        try:
            org_id = self.room_to_org[room_id]
            admin = self.org_admin[org_id]
        except KeyError:
            self.api.messages.create(room_id, text="Please initialize", attachments=[self.init_card])
            return

        # Strips bot mention from command
        if message.split()[0] == self.name:
            command = message.split()[1:]
        else:
            command = message.split()
        print(f"Command: {' '.join(command)}")

        if len(command) > 1 and command[0] == "token" and actor_id in self.org_allowed_users[org_id]:
            admin_id = admin.update_token(command[1])
            if admin_id == "":
                self.api.messages.create(room_id, text=f"Token invalid. Please double check and try again.")
            else:
                self.api.messages.create(room_id, text=f"Access token successfully updated.")

        elif len(command) > 0 and command[0] == "reinit" and actor_id in self.org_allowed_users[org_id]:
            self.remove_room_from_org(room_id)
            self.api.messages.create(room_id, text="Please initialize", attachments=[self.init_card])

        elif len(command) > 0 and command[0] == "help":
            self.api.messages.create(room_id, text=f"To initialize the bot, please fill out the card. If you don't "
                                                   f"see the card, mention the bot to receive it. If the bot is "
                                                   f"already initialized, mention the bot to receive a card to fill "
                                                   f"out to get an activation code.\n\nOther commands include:\n- "
                                                   f"add [email]: add an authorized user to your organization; add "
                                                   f"several at once separated with a space\n- "
                                                   f"remove [email]: remove an authorized user from your organization; "
                                                   f"remove several at once separated with a space\n- "
                                                   f"token [token]: update the access token\n- reinit: reinitialize "
                                                   f"the bot (if you would like to change the organization for this "
                                                   f"room).\n\nIf you require further assistance, please contact me "
                                                   f"at agrobys@cisco.com.")

        # Adds allowed users on "add" command
        elif len(command) > 1 and command[0] == "add" and actor_id in self.org_allowed_users[org_id]:
            print(f"User {self.org_id_to_email[org_id][actor_id]} allowed.")
            for email in command[1:]:
                user_id = self.add_allowed_user(org_id, email)
                # Empty user_id means provided email was not found
                if user_id == "":
                    self.api.messages.create(room_id, text=f"Please provide a valid email as a second argument. If {email} was valid, check if you need to update your access token.")
                else:
                    self.api.messages.create(room_id, text=f"User {email} added successfully.")

        # Removes allowed users on "remove" command
        elif len(command) > 1 and command[0] == "remove" and actor_id in self.org_allowed_users[org_id]:
            print(f"User {self.org_id_to_email[org_id][actor_id]} allowed.")
            for email in command[1:]:
                user_id = self.remove_allowed_user(org_id, email)
                # Empty user_id means provided email was not found
                if user_id == "":
                    self.api.messages.create(room_id,
                                                 text=f"User not found in allowed list. If {email} was valid, check if you need to update your access token.")
                else:
                    self.api.messages.create(room_id, text=f"User {email} removed successfully.")

        # Sends card if no special command is detected
        else:
            print(f"Sending card (No special command detected or user unauthorized).")
            self.api.messages.create(room_id, text="Here's your card", attachments=[self.code_card])
