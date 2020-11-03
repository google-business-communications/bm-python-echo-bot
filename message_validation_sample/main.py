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

The following commands are supported:
- card - Sends a sample rich card
- carousel - Sends a sample carousel
- chips - Sends a message with suggested replies

Any other incoming message is echoed back to the end-user.
"""

# [START app]
import json
import hmac
import uuid
import base64
import hashlib

from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask
from flask import request

from businessmessages import businessmessages_v1_client as bm_client
from businessmessages.businessmessages_v1_messages import (
    BusinessMessagesCarouselCard, BusinessMessagesCardContent, BusinessMessagesContentInfo,
    BusinessMessagesDialAction, BusinessmessagesConversationsMessagesCreateRequest,
    BusinessmessagesConversationsEventsCreateRequest, BusinessMessagesEvent,
    BusinessMessagesOpenUrlAction, BusinessMessagesMedia, BusinessMessagesMessage,
    BusinessMessagesRepresentative, BusinessMessagesRichCard, BusinessMessagesStandaloneCard,
    BusinessMessagesSuggestion, BusinessMessagesSuggestedAction, BusinessMessagesSuggestedReply)

# The location of the service account credentials
SERVICE_ACCOUNT_LOCATION = 'resources/bm-agent-service-account-credentials.json'

# Set of commands the bot understands
CMD_RICH_CARD = 'card'
CMD_CAROUSEL_CARD = 'carousel'
CMD_SUGGESTIONS = 'chips'

# Images used in cards and carousel examples
SAMPLE_IMAGES = [
    'https://storage.googleapis.com/kitchen-sink-sample-images/cute-dog.jpg',
    'https://storage.googleapis.com/kitchen-sink-sample-images/elephant.jpg',
    'https://storage.googleapis.com/kitchen-sink-sample-images/adventure-cliff.jpg',
    'https://storage.googleapis.com/kitchen-sink-sample-images/sheep.jpg',
    'https://storage.googleapis.com/kitchen-sink-sample-images/golden-gate-bridge.jpg',
]

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
    app.logger.debug(request_body)

    # Calculate the signature to validate the message is from Google
    partner_key = 'YOUR_PARTNER_KEY'
    generated_signature = base64.b64encode(hmac.new(partner_key.encode(), msg=request.get_data(), digestmod=hashlib.sha512).digest()).decode('UTF-8')
    # Grab the x-goog-signature from the request header
    google_signature = request.headers.get('x-goog-signature')

    app.logger.debug('x-goog-signature: %s', google_signature)
    app.logger.debug('Generated Signature: %s', generated_signature)

    # Compare x-goog-signature with locally generated signature
    if generated_signature == google_signature:
        app.logger.debug("Signature match.")
    else:
        app.logger.debug("Signature mismatch, do not trust this message.")

    app.logger.debug('request_body: %s', json.dumps(request_body))

    # Extract the conversation id and message text
    conversation_id = request_body['conversationId']
    app.logger.debug('conversation_id: %s', conversation_id)

    # Check that the message and text body exist
    if 'message' in request_body and 'text' in request_body['message']:
        message = request_body['message']['text']

        app.logger.debug('message: %s', message)
        route_message(message, conversation_id)
    elif 'suggestionResponse' in request_body:
        message = request_body['suggestionResponse']['text']

        app.logger.debug('message: %s', message)
        route_message(message, conversation_id)
    elif 'userStatus' in request_body:
        if 'isTyping' in request_body['userStatus']:
            app.logger.debug('User is typing')
        elif 'requestedLiveAgent' in request_body['userStatus']:
            app.logger.debug('User requested transfer to live agent')

    return ''

def route_message(message, conversation_id):
    '''
    Routes the message received from the user to create a response.

    Args:
        message (str): The message text received from the user.
        conversation_id (str): The unique id for this user and agent.
    '''
    normalized_message = message.lower()

    if normalized_message == CMD_RICH_CARD:
        send_rich_card(conversation_id)
    elif normalized_message == CMD_CAROUSEL_CARD:
        send_carousel(conversation_id)
    elif normalized_message == CMD_SUGGESTIONS:
        send_message_with_suggestions(conversation_id)
    else:
        echo_message(message, conversation_id)

def send_rich_card(conversation_id):
    '''
    Sends a sample rich card to the user.

    Args:
        conversation_id (str): The unique id for this user and agent.
    '''
    fallback_text = ('Business Messages!!!\n\n'
                     + 'This is an example rich card\n\n' + SAMPLE_IMAGES[0])

    rich_card = BusinessMessagesRichCard(
        standaloneCard=BusinessMessagesStandaloneCard(
            cardContent=BusinessMessagesCardContent(
                title='Business Messages!!!',
                description='This is an example rich card',
                suggestions=get_sample_suggestions(),
                media=BusinessMessagesMedia(
                    height=BusinessMessagesMedia.HeightValueValuesEnum.MEDIUM,
                    contentInfo=BusinessMessagesContentInfo(
                        fileUrl=SAMPLE_IMAGES[0],
                        forceRefresh=False
                    ))
                )))

    message_obj = BusinessMessagesMessage(
        messageId=str(uuid.uuid4().int),
        representative=BOT_REPRESENTATIVE,
        richCard=rich_card,
        fallback=fallback_text)

    send_message(message_obj, conversation_id)

def send_carousel(conversation_id):
    '''
    Sends a sample rich card to the user.

    Args:
        conversation_id (str): The unique id for this user and agent.
    '''
    rich_card = BusinessMessagesRichCard(carouselCard=get_sample_carousel())

    fallback_text = ''

    # Construct a fallback text for devices that do not support carousels
    for card_content in rich_card.carouselCard.cardContents:
        fallback_text += (card_content.title + '\n\n' + card_content.description
                          + '\n\n' + card_content.media.contentInfo.fileUrl
                          + '\n---------------------------------------------\n\n')

    message_obj = BusinessMessagesMessage(
        messageId=str(uuid.uuid4().int),
        representative=BOT_REPRESENTATIVE,
        richCard=rich_card,
        fallback=fallback_text)

    send_message(message_obj, conversation_id)

def send_message_with_suggestions(conversation_id):
    '''
    Sends a message with a suggested replies.

    Args:
        conversation_id (str): The unique id for this user and agent.
    '''
    message_obj = BusinessMessagesMessage(
        messageId=str(uuid.uuid4().int),
        representative=BOT_REPRESENTATIVE,
        text='Message with suggestions',
        fallback='Your device does not support suggestions',
        suggestions=get_sample_suggestions())

    send_message(message_obj, conversation_id)

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

def get_sample_carousel():
    '''
    Creates a sample carousel rich card.

    Returns:
       A :obj: A BusinessMessagesCarouselCard object with three cards.
    '''
    card_content = []

    for i, sample_image in enumerate(SAMPLE_IMAGES):
        card_content.append(BusinessMessagesCardContent(
            title='Card #' + str(i),
            description='This is a sample card',
            suggestions=get_sample_suggestions(),
            media=BusinessMessagesMedia(
                height=BusinessMessagesMedia.HeightValueValuesEnum.MEDIUM,
                contentInfo=BusinessMessagesContentInfo(
                    fileUrl=sample_image,
                    forceRefresh=False))))

    return BusinessMessagesCarouselCard(
        cardContents=card_content,
        cardWidth=BusinessMessagesCarouselCard.CardWidthValueValuesEnum.MEDIUM)

def get_sample_suggestions():
    '''
    Creates a list of sample suggestions that includes a
    suggested reply and two actions.

    Returns:
       A :list: A list of sample BusinessMessagesSuggestions.
    '''
    return [
        BusinessMessagesSuggestion(
            reply=BusinessMessagesSuggestedReply(
                text='Sample Chip',
                postbackData='sample_chip')
            ),
        BusinessMessagesSuggestion(
            action=BusinessMessagesSuggestedAction(
                text='URL Action',
                postbackData='url_action',
                openUrlAction=BusinessMessagesOpenUrlAction(
                    url='https://www.google.com'))
            ),
        BusinessMessagesSuggestion(
            action=BusinessMessagesSuggestedAction(
                text='Dial Action',
                postbackData='dial_action',
                dialAction=BusinessMessagesDialAction(
                    phoneNumber='+12223334444'))
            ),
        ]

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
