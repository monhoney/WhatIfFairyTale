from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import os
from io import StringIO
import sys
import autogen

USE_CHATGPT = True

if USE_CHATGPT == True:
    config_list = [
        {
#'model': 'gpt-4',
            'model': 'gpt-4-1106-preview',
            'api_key' : os.environ['OPENAI_API_KEY'],
        }
    ]
else:
    config_list = [
        {
            "base_url": "http://localhost:1234/v1",
            "api_key": "not-needed",
        }
    ]

llm_config = {
    "timeout": 600,
    "seed": 42,
    "config_list": config_list,
    "temperature": 0.2
}

CRITIC_IDX_MAP = {
    0 : "1st-Editor",
    1 : "2nd-Editor",
    2 : "3rd-Editor",
    3 : "4th-Editor",
    4 : "5th-Editor",
    5 : "6th-Editor",
    6 : "7th-Editor",
    7 : "8th-Editor",
    8 : "9th-Editor",
    9 : "10th-Editor"}

MAX_CRITIC_COUNT = 10

def generate_play_script(title, scene_info):
    situation = scene_info["situation"]
    characters = scene_info["characters"]

    message="""The following is a play script for the story %s. I wish critics would change the dialogue in the play script appropriately.
    ===================================
    [play script]
      %s\n""" % (title, situation)

    for character in characters:
        message = message + \
            """      %s : %s\n""" % (character["name"], character["dialogue"])
    message = message + """    ==================================
"""

    return message
    
def generate_critics(critic_idx, name, new_persona):
    critic_name = CRITIC_IDX_MAP[critic_idx]
    system_message="""%s thought that character %s is '%s'. %s want to change the play script of character %s to fit that. Modifications made by other editors are reflected.""" % (critic_name, name, new_persona, critic_name, name)
    agent = AssistantAgent(
        name=critic_name,
        system_message=system_message,
        llm_config=llm_config)
    return agent

def generate_user():
    return UserProxyAgent(
        name="user_proxy",
        system_message="""Merge the editors' opinions based on the changed dialogues, and Request reviewers to evaluate the editors' changed play scripts, and reflect the evaluations received from the editors. if the reviewer gives a rating of 5 starts, TERMINATE""",
        llm_config=llm_config,
        human_input_mode="NEVER"
    )

def generate_reviewer():
    return AssistantAgent(
        name="Reviewer",
        system_message="The reviewer evaluates how creatively the story has changed compared to the existing play script on a 5-point scale. The higher the score, the better you are.",
        llm_config=llm_config,
    )
def parse_dialogue(message, characters, personas):
    state = -1
    last_situation = ""
    last_dialogues = []

    print ("message : ", message)

    for line in message.split('\n'):
        if state == 0:
            last_dialogues = []
            last_situation = line
            state = state + 1
            if len(characters) < state:
                state = -1

        elif state > 0:
            splitted = line.split(":")
            if len(splitted) != 2:
                continue

            last_dialogues.append(line.split(":")[1]) 
            state = state + 1
            if len(characters) < state:
                state = -1

        elif "[play script]" in line:
            state = 0

    characters_data = []
    for c_idx, character in enumerate(last_dialogues):
        c_name = characters[c_idx]["name"]
        characters_data.append({"name" : c_name, 
                "persona" : personas[c_idx],
                "dialogue" : last_dialogues[c_idx]})
    result = {"situation" : last_situation,
        "characters" : characters_data}

    return result

def create_dialogue(title, scene_info, personas):
    situation = scene_info["situation"]
    characters = scene_info["characters"]

    assert len(characters) < MAX_CRITIC_COUNT
    assert len(characters) == len(personas)

    user_proxy = generate_user()
    reviewer = generate_reviewer()

    agents = [user_proxy]

    for critic_idx, (character, persona) in enumerate(zip(characters, personas)):
        critic = generate_critics(critic_idx, character["name"], persona)
        agents.append(critic)

    agents.append(reviewer)

    groupchat = GroupChat(
        agents=agents, messages=[],
        allow_repeat_speaker=False
    )
    manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    message = generate_play_script(title, scene_info)

    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    user_proxy.initiate_chat(manager, message=message)
    sys.stdout = old_stdout

    return parse_dialogue(mystdout.getvalue(), characters, personas)
