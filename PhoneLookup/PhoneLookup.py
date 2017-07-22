import requests
import datetime

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
  return {
    'outputSpeech': {
      'type': 'PlainText',
      'text': output
    },
    'card': {
      'type': 'Simple',
      'title': title,
      'content': output
    },
    'reprompt': {
      'outputSpeech': {
        'type': 'PlainText',
        'text': reprompt_text
      }
    },
    'shouldEndSession': should_end_session
  }


def build_response(session_attributes, speechlet_response):
  return {
    'version': '1.0',
    'sessionAttributes': session_attributes,
    'response': speechlet_response
  }

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
  """ If we wanted to initialize the session to have some attributes we could
  add those here
  """

  session_attributes = {}
  card_title = "Welcome"
  speech_output = "Welcome to Phone Number locator.  Say any 9 digit U.S. number to get the location of it."
  # If the user either does not reply to the welcome message or says something
  # that is not understood, they will be prompted again with this text.
  reprompt_text = "Say 'Where is 9 digit phone number'"
  should_end_session = False
  return build_response(session_attributes, build_speechlet_response(
    card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
  card_title = "Session Ended"
  speech_output = "Thank you for using Phone Number Locator. " \
          "Have a nice day "
  # Setting this to true ends the session and exits the skill.
  should_end_session = True
  return build_response({}, build_speechlet_response(
    card_title, speech_output, None, should_end_session))


# --------------- Intents ------------------



def handleLookupIntent(intent, old_session):
  output = ""
  should_end_session = True
  session = {}
  if 'PhoneNumber' in intent['slots']:
    print(intent['slots']['PhoneNumber'])
    phrase = intent['slots']['PhoneNumber']
    fullNumber = 5
    if 'value' in phrase and phrase.get("value","") != "" and phrase.get("value","")  is not None :
      fullNumber = int(phrase['value'])
      print("Full Phrase - {}".format(fullNumber))
    else:
      output = "There was no phone number located."
      should_end_session = False
      return build_response(session, build_speechlet_response("No Number Detected", output, output, should_end_session))
    lookup_results = lookupNumber(fullNumber)
    output = lookup_results
  return build_response(session, build_speechlet_response("{} - Phone Number Location".format(fullNumber), output, output, should_end_session))



def lookupNumber(number):
  headers = {"X-Mashape-Key":"QnME8qXj33mshqT4yltM7QQk1Kfjp1vX7zJjsnoN87jXS0bYCf","Accept":"application/json"}
  r = requests.get("https://cosmin-us-phone-number-lookup.p.mashape.com/get.php?phone={}".format(number), headers=headers)
  results = r.json()
  # print(results)
  output = ""
  citylocation = results.get("city", "")
  
  statelocation = results.get("state", "")
  countylocation = results.get("county", "")
  phoneType = results.get("type", "")
  if phoneType != "":
    output = "The {} was found in ".format(phoneType)
  if citylocation != "":
    output += "the city of " + citylocation + ", "
  if countylocation != "":
    output += "in " + countylocation +  " county" + ", "
  if statelocation != "":
    output += "in the state of " + statelocation + "."
  if output == "":
    output = "The location for the number {} could not be found.".format(number)
  return output


# --------------- Events ------------------

def on_session_started(session_started_request, session):
  """ Called when the session starts """

  print("on_session_started requestId=" + session_started_request['requestId']
      + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
  """ Called when the user launches the skill without specifying what they
  want
  """

  print("on_launch requestId=" + launch_request['requestId'] +
      ", sessionId=" + session['sessionId'])
  # Dispatch to your skill's launch
  return get_welcome_response()


def on_intent(intent_request, session):
  """ Called when the user specifies an intent for this skill """

  print("on_intent requestId=" + intent_request['requestId'] +
      ", sessionId=" + session['sessionId'])

  intent = intent_request['intent']
  intent_name = intent_request['intent']['name']
  r = requests.get("http://google.com")
  
  # Dispatch to your skill's intent handlers
  if intent_name == "LookupNumber":
    print("Get information intent detected")
    return handleLookupIntent(intent, session)
  elif intent_name == "AMAZON.HelpIntent":
    return get_welcome_response()
  elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
    return handle_session_end_request()
  else:
    raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
  """ Called when the user ends the session. 

  Is not called when the skill returns should_end_session=true
  """
  print("on_session_ended requestId=" + session_ended_request['requestId'] +
      ", sessionId=" + session['sessionId'])
  # add cleanup logic here

# --------------- Main handler ------------------

def lambda_handler(event, context):
  """ Route the incoming request based on type (LaunchRequest, IntentRequest,
  etc.) The JSON body of the request is provided in the event parameter.
  """
  print("event.session.application.applicationId=" +
      event['session']['application']['applicationId'])

  """
  Uncomment this if statement and populate with your skill's application ID to
  prevent someone else from configuring a skill that sends requests to this
  function.
  """
  # if (event['session']['application']['applicationId'] !=
  #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
  #     raise ValueError("Invalid Application ID")

  if event['session']['new']:
    on_session_started({'requestId': event['request']['requestId']},
               event['session'])

  if event['request']['type'] == "LaunchRequest":
    return on_launch(event['request'], event['session'])
  elif event['request']['type'] == "IntentRequest":
    return on_intent(event['request'], event['session'])
  elif event['request']['type'] == "SessionEndedRequest":
    return on_session_ended(event['request'], event['session'])


