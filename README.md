# Webex Board Provisioning Bot

>This README has not yet been fully updated from the test version. Please wait or contact me for assistance.

Credits go to @schachem for his echo bot which I used as a skeleton to build the test version for this bot! Find it at: https://github.com/schachem/EchoBot.

### Why use this bot?

- Do you have a Control Hub instance that you use to add Webex devices? 
- Do you have a space of people who you'd like to retrieve activation codes without having to ask you to do it for them? 
- Do you simply want to create a device activation code from the Webex App?

If any of those are true, this bot could make your life a bit easier. 

### How to interact with the bot:

- Add it to a Webex space or direct message it (email: **board-provisioning@webex.bot**).
- It will send you an initialization card. Fill it out with your organization ID and personal Webex API access token (you have to be admin for that organization). You can find your personal temporary access token on developer.webex.com under Documentation -> Access The API and your organization ID on the Webex Control Hub under Account. To get the organization ID usable with the API, send a GET to https://webexapis.com/v1/organizations/{orgId}. You can do this easily at https://developer.webex.com/docs/api/v1/organizations/get-organization-details. The ID you need will be in the response payload.
- After initialization, mention the bot and it will send you a card. Fill out the card with a workspace name, submit, and get your code!
- Remember to mention the bot when in a space, it cannot see your message otherwise. In direct messages, this is not necessary.

### Other commands:

- ```help```: Print all available commands
- ```add [email]```: Add an authorized user to your organization. You can provide several at once separated by a space. Provided emails must be in your organization.  By default, **only the admin** can perform operations using the bot. If you have the bot in several spaces for the same organization, the list of authorized users will be **the same** for each space.
- ```remove [email]```: Remove a user from your organization's authorized list.
- ```token [token]```: Update your access token. If you're using a temporary token, it is only valid for 48hrs. If you do not wish to expose your access token to everyone in a message, use the ```reinit``` command instead.
- ```reinit```: Reinitialize the bot. Do this if you wish to use it for a different organization in this room or if you need to update your token.

### Be aware that:

- Anyone who has the admin's access token can perform any API operations on your organization's Control Hub. Don't paste it in the chat carelessly.

>If you have any questions, contact me at agrobys@cisco.com. 

### Do you want your own bot?

To run this code in your own environment, you need to:

1. Create your own bot at https://developer.webex.com/my-apps/new/bot. Make sure to save the name, email, id and token somewhere.
2. Have somewhere to run it. Mine runs on a Debian Linux VM, but anything with Python should work. Create a directory with the code.
3. Create an environment and export the variables BOT_URL, BOT_PORT, BOT_TOKEN, BOT_ID, BOT_NAME, and BOT_EMAIL (all strings). 
4. Please note: 
   - **BOT_URL should include 'https://' or 'http://'**.
   - BOT_PORT is the port you'd like Flask to run on.
   - The remaining values are your bot's attributes.
5. Install Python3 and the packages defined in ```requirements.txt```. 
6. You should now be ready to run scripts.
   - First, run the ```create_webhooks()``` function in ```webhooks.py```. You can do this with the following bash command: ```python3 -c "from webhooks import create_webhooks; print(create_webhooks())"```. (**NOTE**: There is currently still an error with the personId. The first two webhooks should be created though.)
   - Check webhooks: ```python3 -c "from webhooks import list_webhooks; print(list_webhooks())"```
   - (Optional if something goes wrong) Delete webhooks: ```python3 -c "from webhooks import delete_webhooks; print(delete_webhooks())"```
   - Finally, run the app: ```python3 app.py```
