# BUSINESS MESSAGES: Echo Bot

This sample demonstrates how to receive a message from the [Business Messages](https://developers.google.com/business-communications/business-messages/reference/rest)
platform and echo the same message back to the user using the
[Business Messages Python client library](https://github.com/google-business-communications/python-businessmessages).

The sample also supports the following commands:
* `card` - The bot responds with a sample rich card
* `carousel` - The bot responds with a sample carousel
* `chips` - The bot responds with sample suggested replies

This sample runs on the Google App Engine.

See the Google App Engine (https://cloud.google.com/appengine/docs/python/) standard environment
documentation for more detailed instructions.

## Documentation

The documentation for the Business Messages API can be found [here](https://developers.google.com/business-communications/business-messages/reference/rest).

## Prerequisite

You must have the following software installed on your machine:

* [Google Cloud SDK](https://cloud.google.com/sdk/) (aka gcloud)
* [Python](https://www.python.org/downloads/) - version 3.0 or above

## Before you begin

1.  [Register with Business Messages](https://developers.google.com/business-communications/business-messages/guides/set-up/register).
1.  Once registered, follow the instructions to [enable the APIs for your project](https://developers.google.com/business-communications/business-messages/guides/set-up/register#enable-api).
1. Open the [Create an agent](https://developers.google.com/business-communications/business-messages/guides/set-up/agent)
guide and follow the instructions to create a Business Messages agent.

## Deploy the sample

1.  In a terminal, navigate to this sample's root directory.

1.  Run the following commands:

    ```bash
    gcloud config set project PROJECT_ID
    ```

    Where PROJECT_ID is the project ID for the project you created when you registered for
    Business Messages.

    ```base
    gcloud app deploy
    ```

1.  On your mobile device, use the test business URL associated with the
    Business Messages agent you created. Open a conversation with your agent
    and type in "Hello". Once delivered, you should receive "Hello" back
    from the agent.

    Try entering "card", "carousel", and "chips" separately to explore other
    functionality.

    See the [Test an agent](https://developers.google.com/business-communications/business-messages/guides/set-up/agent#test-agent) guide if you need help retrieving your test business URL.
