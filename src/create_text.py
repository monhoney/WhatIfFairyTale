from openai import OpenAI
client = OpenAI()
import openai
import os
import json

openai.api_key = os.environ['OPENAI_API_KEY']

MODEL = "gpt-3.5-turbo"
#MODEL = "gpt-4"

def gen_text(user_query, filepath, system_query="You are a children's fairy tale writer."):
    try:
        completion = client.chat.completions.create(
          model=MODEL,
          messages=[
            {"role": "system", "content": system_query},
            {"role": "user", "content": user_query}
          ]
        )

        message = completion.choices[0].message.content

        with open(filepath, "w") as f:
            f.write(message)

    except Exception as e:
        print ("critical error")
        print (str(e))


    try:
        data = json.loads(message)
    except:
        data = None

    return data

def make_story(filepath, title="The Little Mermaid", scene_num=10):
    user_query = "Divide the story of %s into %d scenes, and compose each scene with descriptions of the situations, the personas of the characters involved, and a few dialogues they exchange. Please provide a brief description of the situation in 2 to 3 sentences. I would like it to be output in JSON format." % (title, scene_num)
    prompt = "\nThe JSON format must have the following fields:\n" + \
'''
{
  "scenes": [
    {
      "scene_number": 1,
      "situation": "blahblah",
      "characters": [
        {
          "name": "blahblah",
          "persona": "blahblah",
          "dialogue": "blahblah",
        }
      ]
    },
    {
      "scene_number": 2,
      "situation": "blahblah",
      "characters": [
        {
          "name": "blahblah",
          "persona": "blahblah",
          "dialogue": "blahblah",
        },
        {
          "name": "blahblah",
          "persona": "blahblah",
          "dialogue": "blahblah",
        }
      ],
      ...
    }]}
'''
    user_query = user_query + prompt
    return gen_text(user_query, filepath)

def get_gender(title, characters):
    prompt = """
-----------
    The main characters in Snow White are Snow White, the Huntsman, the Queen.
    The genders of the characters in "Snow White" are as follows:
    Snow White: Female
    The Huntsman: Male
    The Queen: Female
----------
"""
    character_prompt = "The main characters in %s are " % title
    for c_idx, character in enumerate(characters):
        if c_idx == 0:
            character_prompt = character_prompt + character
        else:
            character_prompt = ", " + character_prompt + character
    character_prompt = character_prompt + "."

    prompt = prompt + character_prompt
    prompt = prompt + '\nPlease tell me the genders of the characters in "%s"' % title

    completion = client.chat.completions.create(
      model=MODEL,
      messages=[
        {"role": "system", "content": "You are a children's fairy tale writer."},
        {"role": "user", "content": prompt}
      ]
    )


    result = dict()
    for character in characters:
        result[character] = "Male"

    lines = completion.choices[0].message.content.split("\n")
    for line in lines:
        splitted = line.replace("\n", "").split(":")
        if len(splitted) == 2:
            key = splitted[0].strip()
            value = splitted[1].strip()

            if value in ['Female', 'Male'] and key in characters:
                result[key] = value

    print ("result : ", result)
    return result

if __name__ == "__main__":
    data = make_story("hansel_and_gratel.txt", title="Hansel and Gratel")
    print (data)

