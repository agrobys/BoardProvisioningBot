import os
import webexteamssdk

URL = os.environ.get("BOT_URL")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BOT_ID = os.environ.get("BOT_ID")
BOT_PORT = os.environ.get("BOT_PORT")
api = webexteamssdk.WebexTeamsAPI(access_token=BOT_TOKEN)


def create_webhooks() -> None:
    webhooks = []
    print("Creating webhooks")
    webhooks.append(
        api.webhooks.create(
            name="MentionWebhook",
            targetUrl=URL + BOT_PORT + "/mention",
            resource="messages",
            event="created",
        )
    )
    print("Webhook created")
    webhooks.append(
        api.webhooks.create(
            name="CardWebhook",
            targetUrl=URL + BOT_PORT + "/card",
            resource="attachmentActions",
            event="created",
        )
    )
    print("Webhook created")
    webhooks.append(
        api.webhooks.create(
            name="AddedToRoomWebhook",
            targetUrl=URL + BOT_PORT + "/added",
            resource="memberships",
            event="created",
            filter="personId=" + BOT_ID
        )
    )
    print("Webhook created")
    webhooks.append(
        api.webhooks.create(
            name="RemovedFromRoomWebhook",
            targetUrl=URL + BOT_PORT + "/removed",
            resource="memberships",
            event="deleted",
            filter="personId=" + BOT_ID
        )
    )
    print("Webhook created")


def delete_webhooks() -> None:
    webhooks = api.webhooks.list()
    print("Deleting webhooks")
    for webhook in webhooks:
        api.webhooks.delete(webhook.id)
        print("Webhook deleted")


def print_webhooks() -> None:
    webhooks = api.webhooks.list()
    for webhook in webhooks:
        print(webhook)
