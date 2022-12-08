#!/bin/env python

from PIL import Image
import time
import os
import random
import requests
import json
import subprocess
# import googletrans
from yandexfreetranslate import YandexFreeTranslate
import vk_api
import re
import base64
import io
from datetime import datetime, timedelta
from time import sleep

# Указываем ключи доступа, id группы и версию API
VK_API_ACCESS_TOKEN = '***'
VK_API_VERSION = '5.95'
GROUP_ID = 123

NEGATIVE_PROMPT = ""
# NEGATIVE_PROMPT = "ugly, mutated, morbid, mutilated, out of frame, extra limbs, gross proportions, cross-eyed, oversaturated, ugly, 3d, grain, low-res, kitsch"
# session = vk.Session(access_token = VK_API_ACCESS_TOKEN)
# api = vk.API(session, v = VK_API_VERSION)


def Appendmages(images, direction='horizontal',
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
    combo_1 = AppendImages([Image.open("tmp/1.png"), Image.open("tmp/2.png")],
                           direction='horizontal', bg_color=(220, 140, 60))
    # combo_2 = AppendImages(images_bottom, direction='horizontal')
    combo_2 = AppendImages(
        [Image.open("tmp/3.png"), Image.open("tmp/4.png")], direction='horizontal')
    combo_3 = AppendImages([combo_1, combo_2], direction='vertical')

    combo_3.save('tmp/0.png')
    print("[---] Collage done!")


def GetJSONFromHorde(promt, randseed):
    # dpmsolver + stable_diffusion_2.0
    # k_euler_a + stable_diffusion
    jsonrequest = {
        "prompt": promt + "###" + NEGATIVE_PROMPT,
        "params": {
            "sampler_name": "k_euler_a",
            "trusted_workers": False,
            "cfg_scale": 8,
            "seed": str(randseed),
            "height": 512,
            "width": 512,
            "seed_variation": 23,
            "steps": 30,
            "n": 4,
            "karras": True,
            # "post_processing": [
            #     "GFPGAN"
            # ],
            "models": [
                "stable_diffusion"
            ]
        }
    }
    url = 'https://stablehorde.net/api/v2/generate/async'
    headers = {'Content-Type': 'application/json', 'apikey': '0000000000'}
    print("[---] Waiting for JSON from Stable Horde", end='', flush=True)
    submit_req = requests.post(url, headers=headers, json=jsonrequest)
    if submit_req.ok:
        submit_results = submit_req.json()
        req_id = submit_results['id']
        is_done = False
        while not is_done:
            chk_req = requests.get(f'https://stablehorde.net/api/v2/generate/check/{req_id}')
            if not chk_req.ok:
                # logger.error(chk_req.text)
                # print(chk_req.text)
                
                print("check request failed!")
                return
            chk_results = chk_req.json()
            print(chk_results)
            is_done = chk_results['done']
            print(".", end='', flush=True)
            time.sleep(10)
        print("")
        retrieve_req = requests.get(f'https://stablehorde.net/api/v2/generate/status/{req_id}')
        if not retrieve_req.ok:
            # logger.error(retrieve_req.text)
            print("retrieve request failed!")

            return
        results_json = retrieve_req.json()
    # print(req.json())
    else:
        print(submit_req)
        print(submit_req.json())
        raise Exception('Horde API returned error response')
    # with open('req.json', 'w') as f:
    #     json.dump(req.json(), f)
    
    print("[---] JSON good!")
    return json.dumps(results_json)


def processJSONpy(jsonObj):
    result = re.findall('(?<=img": ").*?(?=")', jsonObj)
    i = 1
    for b64webp in result:
        img = Image.open(io.BytesIO(base64.b64decode(b64webp)))
        img.save(f"tmp/{i}.png")
        i += 1
    # print(result)


def GetRandomPrompt():
    lines = open('dog_prompts.txt').read().splitlines()
    myline = random.choice(lines)
    return myline


def NewPost(timestamp, vk, uploads):
    randseed = random.randrange(999999)
    prompt = GetRandomPrompt().capitalize()
    translator = YandexFreeTranslate(api = "ios")
    prompt_translated = translator.translate("en", "ru", prompt).capitalize()

    print("[---] Img params:", randseed, prompt, '(', prompt_translated, ')')

    reqJson = GetJSONFromHorde(prompt, randseed)
    # subprocess.call(['bash', './processJSON.sh']) # process JSON using BASH
    processJSONpy(reqJson)

    uploadedIMG1 = uploads.photo_wall(photos=['tmp/1.png'], group_id=216606944)
    uploadedIMG2 = uploads.photo_wall(photos=['tmp/2.png'], group_id=216606944)
    uploadedIMG3 = uploads.photo_wall(photos=['tmp/3.png'], group_id=216606944)
    uploadedIMG4 = uploads.photo_wall(photos=['tmp/4.png'], group_id=216606944)
    upimg1 = 'photo' + \
        str((uploadedIMG1[0])['owner_id']) + '_' + str((uploadedIMG1[0])['id'])
    upimg2 = 'photo' + \
        str((uploadedIMG2[0])['owner_id']) + '_' + str((uploadedIMG2[0])['id'])
    upimg3 = 'photo' + \
        str((uploadedIMG3[0])['owner_id']) + '_' + str((uploadedIMG3[0])['id'])
    upimg4 = 'photo' + \
        str((uploadedIMG4[0])['owner_id']) + '_' + str((uploadedIMG4[0])['id'])

    upimgs = ','.join([upimg1, upimg2, upimg3, upimg4])
    # print(upimgs)
    postMsg = "⭐ Тема: " + prompt_translated + \
        " (" + prompt + ")\n🎲 Сид: " + str(randseed)
    vk.wall.post(message=postMsg, owner_id=-216606944, from_group=1,
                 attachments=upimgs, publish_date=timestamp, signed=0)
    print("[---] Post done")


def checkDelayedPosts():
    nextHourDT = datetime.now().replace(microsecond=0, second=0, minute=0) + \
        timedelta(hours=1)  # gen nearest hour (as 12:00:00)
    print("[---] Closest hour: ", nextHourDT)
    nextHourUT = int(nextHourDT.strftime('%s'))  # + 3 * 3600
    hours = [nextHourUT, nextHourUT + 1 * 3600, nextHourUT + 2 * 3600, nextHourUT + 3 * 3600, nextHourUT + 4 * 3600, nextHourUT + 5 * 3600, nextHourUT + 6 * 3600, nextHourUT + 7 * 3600, nextHourUT + 8 * 3600, nextHourUT + 9 * 3600, nextHourUT + 10 * 3600, nextHourUT + 11 * 3600,
             nextHourUT + 12 * 3600, nextHourUT + 13 * 3600, nextHourUT + 14 * 3600, nextHourUT + 15 * 3600, nextHourUT + 16 * 3600, nextHourUT + 17 * 3600, nextHourUT + 18 * 3600, nextHourUT + 19 * 3600, nextHourUT + 20 * 3600, nextHourUT + 21 * 3600, nextHourUT + 22 * 3600, nextHourUT + 23 * 3600]
    vk_session = vk_api.VkApi(
        token='***REMOVED***')
    vk = vk_session.get_api()
    tools = vk_api.VkTools(vk_session)
    uploads = vk_api.VkUpload(vk_session)
    postponedPosts = tools.get_all(
        'wall.get', 100, {'owner_id': -216606944, 'filter': 'postponed'})
    for hour in hours:
        # print(datetime.utcfromtimestamp(hour))
        matched = False
        for post in postponedPosts['items']:
            # print(post['date'], hour)
            if post['date'] == hour:
                matched = True
        if matched:
            print('[###]', datetime.utcfromtimestamp(hour+3600*3), "OK")
        else:
            print('[!!!]', datetime.utcfromtimestamp(
                hour+3600*3), "MISSING, making new post...")
            NewPost(hour, vk, uploads)

    print("[+++] All posts posted!")


def main():
    print(" ***  VK AI Dog Pics Poster bot v0.2  ***")

    while True:
        print("[###] Checking delayed posts")
        checkDelayedPosts()
        print("[###] Waiting 30 minutes")
        sleep(1800)


if __name__ == '__main__':
    main()
