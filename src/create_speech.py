from pathlib import Path
from openai import OpenAI
import openai
import os
from enum import Enum
import re
import random

openai.api_key = os.environ['OPENAI_API_KEY']
#SPEECH_MODEL = "tts-1"
SPEECH_MODEL = "tts-1-hd"

client = OpenAI()

def remove_strings_in_parentheses(input_string):
    # 정규 표현식을 사용하여 괄호와 그 안의 문자열을 제거
    result_string = re.sub(r'\([^)]*\)', '', input_string)
    return result_string


class VoiceName(Enum):
    MALE0 = 'alloy'
    MALE1 = 'echo'
    MALE2 = 'fable'
    MALE3 = 'onyx'
    FEMALE0 = 'nova'
    FEMALE1 = 'shimmer'

class MaleVoiceName(Enum):
    MALE0 = 'alloy'
    MALE1 = 'echo'
    MALE2 = 'fable'
    MALE3 = 'onyx'

class FemaleVoiceName(Enum):
    FEMALE0 = 'nova'
    FEMALE1 = 'shimmer'

def gen_speech(prompt, filepath, gender):
    prompt = remove_strings_in_parentheses(prompt)

    if gender == 'Male':
        voice_name = random.choice(list(MaleVoiceName))
    else:
        voice_name = random.choice(list(FemaleVoiceName))

    response = client.audio.speech.create(
        model=SPEECH_MODEL,
        voice=voice_name.value,
        input=prompt
    )

    response.stream_to_file(filepath)

if __name__ == "__main__":
    gen_speech("(laughs) Father, look at the colorful fish! Can we join them?", "1.mp3", "Female")
    gen_speech("(smiling) Go ahead, my child. But remember, stay away from the surface!", "2.mp3", "Male")


