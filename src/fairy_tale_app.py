import streamlit as st
import os
import uuid
import random
import json
import tqdm
import pprint
from stqdm import stqdm
import base64
import time
import fcntl

from multiprocessing import Pool
import multiprocessing as mp

from create_image import gen_story_image
from create_speech import gen_speech, VoiceName
from create_text import make_story, get_gender
from create_dialogue import create_dialogue

UUID_MAP_FILE = "asset/db.txt"

USE_AUTOPLAY = False
PROCESS_COUNT = 16

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

def read_from_file_with_lock(file_path):
    with open(file_path, 'r') as file:
        try:
            # 시스템 레벨의 파일 락을 건다
            fcntl.flock(file, fcntl.LOCK_SH | fcntl.LOCK_NB)

            # 파일에서 데이터를 읽는다
            data = file.readlines()
            return data

        except IOError as e:
            return None

        finally:
            # 락을 해제한다
            fcntl.flock(file, fcntl.LOCK_UN)

def write_to_file_with_lock(file_path, data):
    with open(file_path, 'a') as file:
        try:
            # 시스템 레벨의 파일 락을 건다
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # 파일에 데이터를 쓴다
            file.write(data)
            file.write('\n')

        except IOError as e:
            print(f"Unable to acquire lock: {e}")
        finally:
            # 락을 해제한다
            fcntl.flock(file, fcntl.LOCK_UN)


def main():
    st.title("What-If Fairy Tale")

    if "page" not in st.session_state:
        st.session_state.page = 0
        uuid_str = str(uuid.uuid1())
        st.session_state.uuid = uuid_str
        
    if st.session_state.page == 0:
        title = st.text_input("Enter the title of the fairy tale")
        st.session_state.title = title

        if st.button("submit"):
            st.session_state.page = 1

            cache_id = ""
            lines = read_from_file_with_lock(UUID_MAP_FILE)
            for line in lines:
                splitted = line.replace("\n", "").split('\t')
                if len(splitted) != 2:
                    continue 

                db_title, db_uuid = splitted
                if title == db_title:
                    cache_id = db_uuid
                    break

            need_gen_story_file = True
            check_story_filepath = "asset/%s/story.txt" % cache_id
            if os.path.exists(check_story_filepath):
                try:
                    with open(check_story_filepath, "r") as f:
                        data = json.load(f)
                        st.session_state.uuid = cache_id
                        st.session_state.data = data
                        need_gen_story_file = False
                except Exception as e:
                    print ("cannot parse story file(%s)" % check_story_filepath)

            if need_gen_story_file:
                os.makedirs("asset/%s" % st.session_state.uuid)
                story_filepath = "asset/%s/story.txt" % st.session_state.uuid
                for retry in range(2):
                    st.session_state.data = \
                        make_story(story_filepath, title=st.session_state.title)
                    if st.session_state.data is None:
                        print ("retry!! generate story")
                    else:
                        break

                characters_nameset = set()
                for scene in st.session_state.data["scenes"]:
                    for character_info in scene["characters"]:
                        characters_nameset.add(character_info["name"].replace(" ", ""))

                gender_dic = get_gender(st.session_state.title, list(characters_nameset))
             
                pool = Pool(PROCESS_COUNT)
                st_time = time.time()
                for scene_idx, scene_info in enumerate(stqdm(st.session_state.data["scenes"])):
                    scene_image_filepath = "asset/%s/scene_%02d.jpg" % \
                        (st.session_state.uuid, scene_idx+1)
                    pool.apply_async(gen_story_image, (scene_info, 
                        scene_image_filepath))
                    #gen_story_image(scene_info, scene_image_filepath)
                    for character_info in scene_info["characters"]:
                        gender = gender_dic[character_info["name"].replace(" ", "")]

                        mp3_filepath = "asset/%s/voice_%02d_%s.mp3" % \
                            (st.session_state.uuid, scene_idx+1, 
                             character_info["name"].replace(" ", "")) 
                        pool.apply_async(gen_speech,
                            (character_info["dialogue"], 
                            mp3_filepath, gender))
#                       gen_speech(character_info["dialogue"], mp3_filepath, gender)

                pool.close()
                pool.join()
                write_to_file_with_lock(UUID_MAP_FILE, "%s\t%s\n" % (st.session_state.title, st.session_state.uuid))
            st.rerun()

    if st.session_state.page > 0:
        page_no = st.session_state.page
        st.write("current page : %d" % page_no)
        image_path = "asset/%s/scene_%02d.jpg" % \
            (st.session_state.uuid, page_no)
        st.write(st.session_state.data["scenes"][page_no-1]["situation"] + "\n")
        image = st.image(image_path, use_column_width=True)
        for c_info in st.session_state.data["scenes"][page_no-1]["characters"]:
            st.write("%s : %s" % (c_info["name"], c_info["dialogue"]))

            if USE_AUTOPLAY:
                autoplay_audio("asset/%s/voice_%02d_%s.mp3" %\
                    (st.session_state.uuid, page_no, c_info["name"].replace(" ", "")))
            else:
                st.audio("asset/%s/voice_%02d_%s.mp3" %\
                    (st.session_state.uuid, page_no, c_info["name"].replace(" ", "")))

        if st.button("next page"):
            st.session_state.page = st.session_state.page + 1
            st.rerun()

        st.markdown("---")
        st.write("persona")
       
        personas = []
        for c_info in st.session_state.data["scenes"][page_no-1]["characters"]:
            persona = st.text_input(c_info["name"], c_info["persona"])
            personas.append(persona)

        if st.button("what-if"):
            st_time = time.time()
            scene_info = st.session_state.data["scenes"][page_no-1]
            result = create_dialogue(st.session_state.title, scene_info, personas)

            scene_info["situation"] = result["situation"]
            scene_info["characters"] = result["characters"]

            characters_nameset = set()
            for character_info in scene_info["characters"]:
                characters_nameset.add(character_info["name"].replace(" ", ""))

            gender_dic = get_gender(st.session_state.title, list(characters_nameset))

            pool = Pool(PROCESS_COUNT)
            scene_image_filepath = "asset/%s/scene_%02d.jpg" % \
                (st.session_state.uuid, page_no)
            pool.apply_async(gen_story_image, (scene_info, 
                scene_image_filepath))

            for character_info in scene_info["characters"]:
                mp3_filepath = "asset/%s/voice_%02d_%s.mp3" % \
                    (st.session_state.uuid, page_no,
                     character_info["name"].replace(" ", ""))
                gender = gender_dic[character_info["name"].replace(" ", "")]
                pool.apply_async(gen_speech,
                    (character_info["dialogue"], mp3_filepath, gender))

            pool.close()
            pool.join()

            story_filepath = "asset/%s/story.txt" % st.session_state.uuid
            with open(story_filepath, "w") as f:
                json.dump(st.session_state.data, f, indent=4)

            st.rerun()

if __name__ == "__main__":
    main()

