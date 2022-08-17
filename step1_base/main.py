# Copyright 2020 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Webhook handler for receiving consumer messages and sending a response
using the Business Messages API.

All incoming messages are echoed back to the end-user.
"""

# [START app]
import json
import uuid

from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask
from flask import request

from businessmessages import businessmessages_v1_client as bm_client
from businessmessages.businessmessages_v1_messages import (
    BusinessmessagesConversationsMessagesCreateRequest,
    BusinessmessagesConversationsEventsCreateRequest, BusinessMessagesEvent,
    BusinessMessagesMessage, BusinessMessagesRepresentative)

# The location of the service account credentials
SERVICE_ACCOUNT_LOCATION = 'resources/bm-agent-service-account-credentials.json'

# The representative type that all messages are sent as
BOT_REPRESENTATIVE = BusinessMessagesRepresentative(
    representativeType=BusinessMessagesRepresentative.RepresentativeTypeValueValuesEnum.BOT,
    displayName='Echo Bot',
    avatarImage='https://storage.googleapis.com/sample-avatars-for-bm/bot-avatar.jpg')

app = Flask(__name__, static_url_path='')
app.config['DEBUG'] = True

@app.route('/callback', methods=['POST'])
def callback():
    """
    Callback URL. Processes messages sent from user.
    """
    request_body = request.json

    app.logger.debug('request_body: %s', json.dumps(request_body))

    # To set a webhook, extract the secret from the request and return it
    if 'secret' in request_body:
        return request_body.get('secret')

    # Extract the conversation id and message text
    conversation_id = request_body['conversationId']
    app.logger.debug('conversation_id: %s', conversation_id)

    # Check that the message and text body exist
    if 'message' in request_body and 'text' in request_body['message']:
        message = request_body['message']['text']

        app.logger.debug('message: %s', message)
        echo_message(message, conversation_id)
    elif 'suggestionResponse' in request_body:
        message = request_body['suggestionResponse']['text']

        app.logger.debug('message: %s', message)
        echo_message(message, conversation_id)
    elif 'userStatus' in request_body:
        if 'isTyping' in request_body['userStatus']:
            app.logger.debug('User is typing')
        elif 'requestedLiveAgent' in request_body['userStatus']:
            app.logger.debug('User requested transfer to live agent')

    return ''

def echo_message(message, conversation_id):
    '''
    Sends the message received from the user back to the user.

    Args:
        message (str): The message text received from the user.
        conversation_id (str): The unique id for this user and agent.
    '''
    message_obj = BusinessMessagesMessage(
        messageId=str(uuid.uuid4().int),
        representative=BOT_REPRESENTATIVE,
        text=message)

    send_message(message_obj, conversation_id)

def send_message(message, conversation_id):
    '''
    Posts a message to the Business Messages API, first sending
    a typing indicator event and sending a stop typing event after
    the message has been sent.

    Args:
        message (obj): The message object payload to send to the user.
        conversation_id (str): The unique id for this user and agent.
    '''
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_LOCATION,
        scopes=['https://www.googleapis.com/auth/businessmessages'])

    client = bm_client.BusinessmessagesV1(credentials=credentials)

    # Send the typing started event
    create_request = BusinessmessagesConversationsEventsCreateRequest(
        eventId=str(uuid.uuid4().int),
        businessMessagesEvent=BusinessMessagesEvent(
            representative=BOT_REPRESENTATIVE,
            eventType=BusinessMessagesEvent.EventTypeValueValuesEnum.TYPING_STARTED
        ),
        parent='conversations/' + conversation_id)

    bm_client.BusinessmessagesV1.ConversationsEventsService(
        client=client).Create(request=create_request)

    # Create the message request
    create_request = BusinessmessagesConversationsMessagesCreateRequest(
        businessMessagesMessage=message,
        parent='conversations/' + conversation_id)

    bm_client.BusinessmessagesV1.ConversationsMessagesService(
        client=client).Create(request=create_request)

    # Send the typing stopped event
    create_request = BusinessmessagesConversationsEventsCreateRequest(
        eventId=str(uuid.uuid4().int),
        businessMessagesEvent=BusinessMessagesEvent(
            representative=BOT_REPRESENTATIVE,
            eventType=BusinessMessagesEvent.EventTypeValueValuesEnum.TYPING_STOPPED
        ),
        parent='conversations/' + conversation_id)

    bm_client.BusinessmessagesV1.ConversationsEventsService(
        client=client).Create(request=create_request)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
