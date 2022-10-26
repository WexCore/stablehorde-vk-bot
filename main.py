#!/bin/env python

from PIL import Image
import time
import os
import random
import requests
import json
import subprocess
import googletrans
import vk_api
import re
from datetime import datetime, timedelta

# Указываем ключи доступа, id группы и версию API
VK_API_ACCESS_TOKEN = '***'
VK_API_VERSION = '5.95'
GROUP_ID = 123
# session = vk.Session(access_token = VK_API_ACCESS_TOKEN)
# api = vk.API(session, v = VK_API_VERSION)


def AppendImages(images, direction='horizontal',
                  bg_color=(255, 255, 255), aligment='center'):
    """
    Appends images in horizontal/vertical direction.
    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'
    Returns:
        Concatenated image as a new PIL image object.
    """
    widths, heights = zip(*(i.size for i in images))
    if direction == 'horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)
    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)
    offset = 0
    for im in images:
        if direction == 'horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]
    return new_im

def imageCollage():
    # images_top    = map(Image.open, ["tmp/1.png", "tmp/2.png"])
    # images_bottom = map(Image.open, ["tmp/3.png", "tmp/4.png"])

    # combo_1 = AppendImages(images_top, direction='horizontal', bg_color=(220, 140, 60))
    combo_1 = AppendImages([Image.open("tmp/1.png"),Image.open("tmp/2.png")], direction='horizontal', bg_color=(220, 140, 60))
    # combo_2 = AppendImages(images_bottom, direction='horizontal')
    combo_2 = AppendImages([Image.open("tmp/3.png"),Image.open("tmp/4.png")], direction='horizontal')
    combo_3 = AppendImages([combo_1, combo_2], direction='vertical')

    combo_3.save('tmp/0.png')
    print("Collage done!")
    return

def GetJSONFromHorde(promt, randseed):

    jsonrequest = {
        "prompt": promt,
        "params": {
            "sampler_name": "k_lms",
            "cfg_scale": 8,
            "seed": str(randseed),
            "height": 512,
            "width": 512,
            "seed_variation": 1,
            "steps": 50,
            "n": 4
        }
    }
    url = 'https://stablehorde.net/api/v2/generate/sync'
    headers = {'Content-Type': 'application/json', 'apikey': '0000000000'}
    print("Waiting for JSON from Stable Horde...")
    req = requests.post(url, headers=headers, json=jsonrequest)

    # print(req.json())
    if req.ok != True:
        print(req)
        print(req.json())
        raise Exception('API Failed.')
    with open('req.json', 'w') as f:
        json.dump(req.json(), f)
    print("JSON good!")
    return

def processJSONpy(jsonObj):
    
    return

def GetRandomPrompt():
    lines = open('dog_prompts.txt').read().splitlines()
    myline = random.choice(lines)
    return myline

def NewPost(timestamp, vk, uploads):
    randseed = random.randrange(999999)
    prompt = GetRandomPrompt()
    translator = googletrans.Translator()
    prompt_translated = translator.translate(prompt, dest='ru').text

    print("Img params:", randseed, prompt, '(', prompt_translated, ')')

    GetJSONFromHorde(prompt, randseed)
    subprocess.call(['bash', './processJSON.sh'])

    uploadedIMG1 = uploads.photo_wall(photos=['tmp/1.png'], group_id=216606944)
    uploadedIMG2 = uploads.photo_wall(photos=['tmp/2.png'], group_id=216606944)
    uploadedIMG3 = uploads.photo_wall(photos=['tmp/3.png'], group_id=216606944)
    uploadedIMG4 = uploads.photo_wall(photos=['tmp/4.png'], group_id=216606944)
    upimg1 = 'photo' + str((uploadedIMG1[0])['owner_id']) + '_' + str((uploadedIMG1[0])['id'])
    upimg2 = 'photo' + str((uploadedIMG2[0])['owner_id']) + '_' + str((uploadedIMG2[0])['id'])
    upimg3 = 'photo' + str((uploadedIMG3[0])['owner_id']) + '_' + str((uploadedIMG3[0])['id'])
    upimg4 = 'photo' + str((uploadedIMG4[0])['owner_id']) + '_' + str((uploadedIMG4[0])['id'])

    upimgs = ','.join([upimg1,upimg2,upimg3,upimg4])
    # print(upimgs)
    postMsg = "⭐ Тема: " + prompt_translated + " (" + prompt + ")\n🎲 Сид: " + str(randseed)
    vk.wall.post(message=postMsg, owner_id=-216606944, from_group=1, attachments=upimgs, publish_date=timestamp, signed=0)
    return

if __name__ == '__main__':
    print(" ***  VK AI Dog Pics Poster bot v0.1  ***")

    nextHourDT = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1) # gen nearest hour (as 12:00:00)
    print("[---] Closest hour: ", nextHourDT)
    nextHourUT = int(nextHourDT.strftime('%s'))# + 3 * 3600

    vk_session = vk_api.VkApi(token='***REMOVED***')
    vk = vk_session.get_api()
    tools = vk_api.VkTools(vk_session)
    uploads = vk_api.VkUpload(vk_session)
    postponedPosts = tools.get_all('wall.get', 100, {'owner_id': -216606944, 'filter': 'postponed'})

    hours = [nextHourUT, nextHourUT + 1 * 3600, nextHourUT + 2 * 3600, nextHourUT + 3 * 3600, nextHourUT + 4 * 3600, nextHourUT + 5 * 3600, nextHourUT + 6 * 3600, nextHourUT + 7 * 3600, nextHourUT + 8 * 3600, nextHourUT + 9 * 3600, nextHourUT + 10 * 3600, nextHourUT + 11 * 3600, nextHourUT + 12 * 3600, nextHourUT + 13 * 3600, nextHourUT + 14 * 3600, nextHourUT + 15 * 3600, nextHourUT + 16 * 3600, nextHourUT + 17 * 3600, nextHourUT + 18 * 3600, nextHourUT + 19 * 3600, nextHourUT + 20 * 3600, nextHourUT + 21 * 3600, nextHourUT + 22 * 3600, nextHourUT + 23 * 3600]

    for hour in hours:
        # print(datetime.utcfromtimestamp(hour))
        matched = False
        for post in postponedPosts['items']:
            # print(post['date'], hour)
            if post['date'] == hour:
                matched = True
        if matched:
            print('[###]',datetime.utcfromtimestamp(hour+3600*3), "OK")
        else:
            print('[!!!]',datetime.utcfromtimestamp(hour+3600*3), "BAD, making new post...")
            NewPost(hour, vk, uploads)            

    print("[+++] All posts posted!")
