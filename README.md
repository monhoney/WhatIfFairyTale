# What-if-fairytale
This project is composed of 10 scenes based on well-known fairytales, exploring how the narrative transforms when altering the personas of the characters.

## Features
### Story Generation in 10 Scenes
![story_gen](https://github.com/monhoney/What-If-FairyTale/assets/1555360/d16bd354-bb68-43ab-b0ca-8eb149ad2400)
### What-If Story Regeneration
![what_if](https://github.com/monhoney/What-If-FairyTale/assets/1555360/d8b2bfda-3ffc-408e-96df-ae877beb2f0a)

## Prerequisites for Installation
* install `anaconda`
* make cache directory and meta file
```
$ mkdir src/asset
$ touch src/asset/db.txt
```
* prepare `OPENAI_API_KEY` and set it as an environment variable
```
$ export OPENAI_API_KEY=abcdfefa-afsadfje-fasfasfasf
```

## Installation
``` 
$ conda create -n what-if-fairytale python=3.10
$ conda activate what-if-fairytale
$ pip install -r requirements.txt
```

## Run
* run `fairy_tale_app`
```
$ cd src
$ streamlit run src/fairy_tale_app.py
```
* when running the `fairy_tale_app`, connect to the address printed in the console using a web browser

## Video Clip
show video_clip/WhatIfFairyTale.mp4

## Notebook for overall story transformation
run `notebook/Autogen_WhatIf.ipynb`
