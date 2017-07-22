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
    speech_output = "Welcome to MIT Dining.  Figure out what is in the dining halls today, by simply saying 'what is in Masseh for dinner?'"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Go ahead and say, 'what's in Baker dining today'"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using MIT Dining. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


# --------------- Intents ------------------


def lookup_dining():
    r = requests.get("http://m.mit.edu/apis/dining/venues/house")
    response = r.json()
    return response

def dining_options():
    options = []
    r = requests.get("http://m.mit.edu/apis/dining/venues/house")
    response = r.json()
    for diningOption in response:
        if diningOption.get("short_name", "") != "":
            options.append(diningOption.get("short_name", ""))
    return options


def lookup_dining_option(dining_halls, dining_meal = ""):
    print("Looking up dining halls {}".format(dining_halls))
    if len(dining_halls) < 1:
        return "Please specify which dining hall you would like to get meals for. Choose one of {}".format(getListString(dining_options(), None, "or"))
    else:
        print("Dining hall selected")
        fullOptions = lookup_dining()
        output = ""
        for hall_name in dining_halls:
            print('Retrieving options for {}'.format(hall_name))
            hallFound = False
            for option in fullOptions:
                if option.get("short_name", "").lower() == hall_name.lower():
                    print("Option found")
                    hallFound = True
                    meals_by_day = option.get("meals_by_day")
                    today_date_string = datetime.datetime.now().strftime("%Y-%m-%d")
                    current_day_meal = None
                    for dining_day in meals_by_day:
                        if dining_day.get('date', '') == today_date_string:
                            current_day_meal = dining_day
                    if current_day_meal is not None:
                        if current_day_meal.get('message', '') != '':
                            output += "{} is {}. ".format(hall_name[:1].capitalize() + hall_name[1:], current_day_meal.get('message').lower())
                        elif len(current_day_meal.get('meals', [])) > 0:
                            meals = current_day_meal.get('meals')
                            meal_names = []
                            for meal in meals:
                                if meal.get("name", "") != "":
                                    meal_names.append(meal.get("name"))
                            output += "{} has the meals {}".format(hall_name[:1].capitalize() + hall_name[1:], meal_names)



                    else:
                        output += "  No meal found in {} for today. ".format(hall_name)
            if hallFound == False:
                output += hall_name[:1].capitalize() + hall_name[1:] + " could not be found as a MIT dining hall"

        return output

# print(lookup_dining_option(["Maseeh"]))


def getListString(listName, function = None, conjunction = "and"):
    output = ""
    if len(listName) == 0:
        return ""
    if len(listName) == 1:
        return "{}.".format(listName[0])
    for i in range(len(listName)):
        if i == len(listName) - 1:
            if function is not None:
                output += "{} {}.".format(conjunction, function(listName[i]))
            else:
                output += "{} {}.".format(conjunction, listName[i])
        else:
            if function is not None:
                output += "{}, ".format(function(listName[i]))
            else:
                output += "{}, ".format(listName[i])
    return output

def handleLookupIntent(intent, old_session):
    output = ""
    should_end_session = True
    session = {}
    if 'DiningHallName' in intent['slots']:
        print(intent['slots']['DiningHallName'])
        diningHallName = intent['slots']['DiningHallName']
        if 'value' in diningHallName and diningHallName.get("value","") != "" and diningHallName.get("value","")  is not None :
            diningHall = diningHallName['value']
            print("Final Dining Hall - {}".format(diningHall))
        else:
            output = "Invalid Dining Hall, please try again with a valid dining hall like 'Baker', 'Maseeh', or 'Simmons'"
            should_end_session = False
            return build_response(session, build_speechlet_response("Lookup Dining Information", output, output, should_end_session))
        mealNameDict = intent['slots'].get("MealName",{})
        mealName = ""
        if mealNameDict != {}:
            mealName = mealNameDict.get("value", "")
        lookup_results = lookup_dining_option([diningHall], mealName)
        output = lookup_results
    return build_response(session, build_speechlet_response("Lookup Dining Information", output, output, should_end_session))

# print(lookup_dining())

# def damerau_levenshtein_distance(s1, s2):
#     d = {}
#     lenstr1 = len(s1)
#     lenstr2 = len(s2)
#     for i in range(-1,lenstr1+1):
#         d[(i,-1)] = i+1
#     for j in range(-1,lenstr2+1):
#         d[(-1,j)] = j+1

#     for i in range(lenstr1):
#         for j in range(lenstr2):
#             if s1[i] == s2[j]:
#                 cost = 0
#             else:
#                 cost = 1
#             d[(i,j)] = min(
#                            d[(i-1,j)] + 1, # deletion
#                            d[(i,j-1)] + 1, # insertion
#                            d[(i-1,j-1)] + cost, # substitution
#                           )
#             if i and j and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
#                 d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition
#     return d[lenstr1-1,lenstr2-1]




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
    if intent_name == "GetInformation":
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


