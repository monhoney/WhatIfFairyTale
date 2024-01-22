import openai
import os
from openai import OpenAI
client = OpenAI()
import requests
from io import BytesIO
from PIL import Image

openai.api_key = os.environ['OPENAI_API_KEY']
GEN_IMAGE_MODEL='dall-e-3'


def save_image_from_url(url, save_path):
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)

def gen_image(prompt, filepath):
    response = client.images.generate(
        model=GEN_IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    save_image_from_url(image_url, filepath)



def gen_story_image(scene_info, filepath):
    page_prompt = "I would like you to draw page number %d at the bottom of the picture." % scene_info['scene_number']

    situation_prompt = "Draw a picture to explain the following situation\n=========================\n" + scene_info["situation"] + "\n=========================\n" 

    character_prompt = ""

    for character_info in scene_info["characters"]:
        character_prompt = character_prompt + 'In the picture, the character %s has a "%s" persona and says "%s"\n' % (character_info["name"], character_info["persona"], character_info["dialogue"])

    last_prompt = page_prompt + " Please draw it in a fairy-tale style."

    is_success = False
    for retry_idx in range(3):
        try:
            if retry_idx == 0:
                prompt = situation_prompt + character_prompt + last_prompt
            elif retry_idx == 1:
                prompt = situation_prompt + last_prompt
            else:
                prompt = situation_prompt

            gen_image(prompt, filepath)
            is_success = True
            break
        except:
            print ("retry")

    if is_success == False:
        print ("failed to generate image")

if __name__ == "__main__":
    gen_image("In the underwater kingdom, King Neptune and his playful daughters, including the protagonist, Ariel, are frolicking and exploring the ocean depths.", "mermaid1.jpg")

