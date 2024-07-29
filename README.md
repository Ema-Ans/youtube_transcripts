
# Generating Newletters

This is a quick guide on how you could generate the Newletters using code in the following repo.

### Getting the youtube video link

Relevant excel sheets and transcripts are in the following google drive folder: https://drive.google.com/drive/folders/1cdxwcNOrXYqBvUNvN_URNMyS1jselgej?usp=sharing

- Based on the topic you are searching for, you do a quick youtube search and get all the relevant url links of the relevant youtube videos, and put those in the excel sheet __youtube top topics__ for easy reference.

### Getting the youtube video transcripts
- After you have a list of urls you are interested in, you will get the jupyter notebook named "transcripts.ipynb" from the __Youtube_analysis__ gtihub repository.
- In that notebook, you are meant to install some dependencies which can be done so using the pip install command.
- After the imports go smoothly, you just have to get the video_id from the url, which is found at the end of the url link.
- You will input that into the get_caption function in a string format, and the function should output the video caption for you.

### Generating the newsletters from video transcripts
- This can be done by utilizing the function in the file __search_pubmed.py__ to get the articles/scientific evidence on the topic of your interest.
- Using these, prompt chatgpt or any other LLM to generate the news articles using the transcript and references.
- Samples of prompts that have been used before can be found in the newsletters in the _Newsletters_ folder in the google drive.

  
