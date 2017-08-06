from __future__ import print_function
import requests
import json
import sys


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
    speech_output = "Welcome to MIT People.  Look up any people affiliated with MIT and get their information"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Go ahead and say, Look up and the person's name"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using MIT People. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session =n True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))



# --------------- Intents ------------------
def handleConfirmIntent(intent, old_session):
    output = ""
    should_end_session = False
    session = {}
    print("Confirming person Intent running")
    if 'PersonName' in intent['slots']:
        print(intent['slots']['PersonName'])
        personName = intent['slots']['PersonName']
        if 'value' in personName:
            personName = stripUnlikelyWords(personName['value'])
            print("Confirming person name {}".format(personName))
        else:
            output = "Invalid name, please try again"
            should_end_session = False
            return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))
        print(session)
        if "LookingForComfirmation" in old_session["attributes"]:
            print("Looking for Comfirmation found")
            if old_session["attributes"]["LookingForComfirmation"]:
                print("Looking for Comfirmation true")
                if "Current_Query_Results" in old_session["attributes"] and len(old_session["attributes"]["Current_Query_Results"]) > 1:
                    print("Multiple results found")
                    query_results = old_session["attributes"]["Current_Query_Results"]
                    min_score = damerau_levenshtein_distance(personName,query_results[0]['name'])
                    min_person = query_results[0]
                    for result in query_results:
                        print("Name - {}, Score - {}".format(result['name'], damerau_levenshtein_distance(personName,result['name'])))
                        if damerau_levenshtein_distance(personName,result['name']) < min_score:
                            min_score = damerau_levenshtein_distance(personName,result['name'])
                            min_person = result
                    print(min_person)
                    setSessionValue(session, "Found_Person",True)
                    # setSessionValue(session, "Current_Query_Results",None)
                    # setSessionValue(session, "LookingForComfirmation",False)
                    setSessionValue(session, "CurrentPerson",min_person)
                    output = "{} confirmed.  ".format(min_person['name'])
                    output += choose_person_output(min_person, session)
                    return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))
            else:
                return handleLookupIntent(intent, session)
        else:
            return handleLookupIntent(intent, session)
    print(output)
    return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))

def handleLookupIntent(intent, old_session):
    output = ""
    should_end_session = True
    session = {}
    print("Lookup intent running")
    if 'PersonName' in intent['slots']:
        print(intent['slots']['PersonName'])
        personName = intent['slots']['PersonName']
        if 'value' in personName:
            personName = stripUnlikelyWords(personName['value'])
            print("Final PersonName - {}".format(personName))
        else:
            output = "Invalid name, please try again"
            should_end_session = False
            return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))
        if len(personName) < 3:
            output = "Invalid name, please try again"
            should_end_session = False
            return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))
        else:
            response = lookup_person(personName)
            if response is None:
                print("No results found")
                output = "No results found for {}.  Try looking up someone else or retrying.".format(personName)
                should_end_session = False
            elif len(response) > 1:
                print("Multiple results found")
                # print(response)
                should_end_session = False
                output = "{} people found. ".format(len(response))
                def nameField(a):
                    return a["name"]
                if len(response) > 6:
                    output += "The first six are... " 
                    output += getListString(response[:6], nameField)
                    fullQuery = []
                    fullSize = sys.getsizeof(fullQuery)
                    for item in response:
                        if fullSize < 20000:
                            fullQuery.append(item)
                            fullSize += sys.getsizeof(item)
                        
                        print(sys.getsizeof(fullQuery))
                    session["Current_Query_Results"] = fullQuery
                    session["Found_Person"] = False
                    session["LookingForComfirmation"] = True
                    print("full session size {}".format(sys.getsizeof(session)))
                else:
                    output += getListString(response, nameField)
                    session["Current_Query_Results"] = response
                    session["Found_Person"] = False
                    session["LookingForComfirmation"] = True
                output += "  Please specify further who you wanted to look up by saying, Confirm, then the person's name."
            elif len(response) == 1:
                print("One results found")
                should_end_session = False
                personName = response[0]['name']
                output = "{} found.  ".format(personName)
                person = response[0]
                output += choose_person_output(person, session)

                setSessionValue(session, "Found_Person",True)
                # setSessionValue(session, "Current_Query_Results",None)
                # setSessionValue(session, "LookingForComfirmation",False)
                setSessionValue(session, "CurrentPerson",person)
                # session["Found_Person"] = True
                # session["Current_Query_Results"] = {}
                # session["LookingForComfirmation"] = False
                # session["CurrentPerson"] = person
    print(output)
    return build_response(session, build_speechlet_response("Lookup Person", output, output, should_end_session))

def setSessionValue(session, key, value):
    session[key] = value
    # if key in session['attributes']:
    #     session['attributes'][key] = value

def handleGetInfoIntent(intent, old_session):
    output = ""
    should_end_session = True
    contractions = {"EARTH, ATMOS & PLANETARY SCI": "Earth, Atmosphere, and Planetary Science","Dept of Electrical Engineering & Computer Science":"Department of Electrical Engineering & Computer Science", "ELECTRICAL ENG & COMPUTER SCI":"Electrical Engineering and Computer Science", "20":"Biological engineering"}
    session = old_session.get('attributes', {})
    if "CurrentPerson" in session and "Found_Person" in session and session["Found_Person"] and "CurrentInformationOptions" in session:
        currentPerson = session["CurrentPerson"]
        typeOptions = session["CurrentInformationOptions"]
        if 'value' in intent['slots']["Information_Type"]:
            infoKey = intent['slots']["Information_Type"]['value']
            if infoKey == "all":
                output = ''
                for item in typeOptions.items():
                    if item[1] in contractions:
                        output += "{}'s {} is {}.  ".format(currentPerson["name"], item[0], contractions[item[1]])
                    else:
                        output += "{}'s {} is {}.  ".format(currentPerson["name"], item[0], item[1])
            elif infoKey in typeOptions:
                if typeOptions[infoKey] in contractions:
                    output = "{}'s {} is {}.  ".format(currentPerson["name"], infoKey, contractions[typeOptions[infoKey]])
                else:
                    output = "{}'s {} is {}.  ".format(currentPerson["name"], infoKey, typeOptions[infoKey])
            else:
                output = "{} not found inside {}'s records.  {} only has information, including. {}".format(infoKey, currentPerson["name"], currentPerson["name"], getListString(typeOptions.keys()))
        else:
            output = "No informational type detected.  {} has different types of information, including. {}".format(currentPerson["name"], getListString(typeOptions.keys()))
            
    else:
        output = "No one currently selected.  Say find, then the person's name to get their information"
        should_end_session = False
    print(output)
    return build_response(session, build_speechlet_response("Get Person Information", output, output, should_end_session))

def stripUnlikelyWords(personName):
    words = ['find ', 'get ', 'lookup', 'look ', 'a ', 'up ', 'for ', 'info ', 'ask ', 'get ', 'information ', 'finds ', 'or ', 'the ', '.', 'search ', 'about ']
    output = personName
    for word in words:
        output = output.replace(word,'')
    return output


def lookup_person(personName):
    r = requests.get("http://m.mit.edu/apis/people?q={}".format(personName))
    response = r.json()
    if "error" in response:
        return None
    if len(response) == 0:
        return None
    else:
        return response

def choose_person_output(person, session):
    options = {}
    if "title" in person:
        options["title"] = person["title"]
    if "dept" in person:
        options["department"] = person["dept"]
    if "id" in person:
        options["kerberos"] = person["id"]
    if "phone" in person and len(person["phone"]) > 0:
        options["phone"] = person["phone"][0]
    if "email" in person and len(person["email"]) > 0:
        options["email"] = person["email"][0]
    if "office" in person and len(person["office"]) > 0:
        options["office"] = person["office"][0]
    if "website" in person and len(person["website"]) > 0:
        options["website"] = person["website"][0]
    session["CurrentInformationOptions"] = options
    if len(options) > 1:
        return "{} has {} options. {}  Or say all?  What information do you want?".format(person['name'], len(options), getListString(options.keys()))
    else:
        return "{} has {} option. {}  What information do you want?".format(person['name'], len(options), options.keys()[0])

def getListString(listName, function = None):
    output = ""
    for i in range(len(listName)):
        if i == len(listName) - 1:
            if function is not None:
                output += " and {}.".format(function(listName[i]))
            else:
                output += " and {}.".format(listName[i])
        else:
            if function is not None:
                output += "{}, ".format(function(listName[i]))
            else:
                output += "{}, ".format(listName[i])
    return output

def damerau_levenshtein_distance(s1, s2):
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in range(-1,lenstr2+1):
        d[(-1,j)] = j+1

    for i in range(lenstr1):
        for j in range(lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i,j)] = min(
                           d[(i-1,j)] + 1, # deletion
                           d[(i,j-1)] + 1, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                          )
            if i and j and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition

    return d[lenstr1-1,lenstr2-1]
  
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
    if intent_name == "LookUp":
        return handleLookupIntent(intent, session)
    elif intent_name == "ConfirmPerson":
        return handleConfirmIntent(intent, session)
    elif intent_name == "GetInfo":
        return handleGetInfoIntent(intent, session)
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
