
#!/bin/env python

from PIL import Image
import time
import os
import random
import requests
import json
import subprocess
from yandexfreetranslate import YandexFreeTranslate
import vk_api
import re
import base64
import io
from datetime import datetime, timedelta
from time import sleep
from dotenv import load_dotenv
import logging

load_dotenv()

VK_API_ACCESS_TOKEN = os.getenv('VK_API_ACCESS_TOKEN')
VK_API_VERSION = os.getenv('VK_API_VERSION')
GROUP_ID = int(os.getenv('GROUP_ID'))
NEGATIVE_PROMPT = os.getenv('NEGATIVE_PROMPT')

if not VK_API_ACCESS_TOKEN:
    raise ValueError("Missing VK_API_ACCESS_TOKEN")
if not VK_API_VERSION:
    raise ValueError("Missing VK_API_VERSION")
if not GROUP_ID:
    raise ValueError("Missing GROUP_ID")
if not NEGATIVE_PROMPT:
    raise ValueError("Missing NEGATIVE_PROMPT")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def get_json_from_horde(prompt, randseed):
    """
    Отправляет запрос к StableHorde API для генерации изображения на основе предоставленного промпта и сида.
    """
    json_request = {
        "prompt": prompt + "###" + NEGATIVE_PROMPT,
        "params": {
            "sampler_name": "k_dpm_2_a",
            "trusted_workers": False,
            "cfg_scale": 8,
            "seed": str(randseed),
            "height": 512,
            "width": 512,
            "seed_variation": 2,
            "steps": 25,
            "n": 4,
            "karras": True,
            "post_processing": ["GFPGAN"],
            "models": ["stable_diffusion_2.1"]
        }
    }
    url = 'https://stablehorde.net/api/v2/generate/async'
    headers = {'Content-Type': 'application/json', 'apikey': '0000000000'}

    while True:
        try:
            logging.info("Submitting request to StableHorde API")
            submit_req = requests.post(url, headers=headers, json=json_request)
            if not submit_req.ok:
                raise requests.exceptions.HTTPError('Submit request failed')
            submit_results = submit_req.json()
            req_id = submit_results['id']
            for timeout_count in range(20):
                chk_req = requests.get(f'https://stablehorde.net/api/v2/generate/check/{req_id}')
                if not chk_req.ok:
                    raise requests.exceptions.HTTPError('Check request failed')
                chk_results = chk_req.json()
                if chk_results['done']:
                    logging.info("Retrieving results")
                    retrieve_req = requests.get(f'https://stablehorde.net/api/v2/generate/status/{req_id}')
                    if not retrieve_req.ok:
                        raise requests.exceptions.HTTPError('Retrieve request failed')
                    results_json = retrieve_req.json()
                    return json.dumps(results_json)
                logging.info("Awaiting results - queue " + str(chk_results['queue_position']))
                time.sleep(30)
            raise Exception("Worker stuck")
        except requests.exceptions.HTTPError as e:
            logging.error("HTTPError: %s", e)
            sleep(1)
            continue
        except Exception as e:
            logging.error("Unexpected error: %s", e)
            sleep(1)
            continue


def process_images_from_json(json_obj):
    """
    Извлекает данные изображения из предоставленного объекта JSON и сохраняет их в виде файлов PNG.
    """
    json_data = json.loads(json_obj)
    dir_name = "tmp"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for idx, generation in enumerate(json_data["generations"], start=1):
        img_url = generation["img"]
        response = requests.get(img_url)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        img.save(f"{dir_name}/{idx}.png")


def get_random_prompt():
    """
    Возвращает случайную подсказку из файла dog_prompts.txt.
    """
    with open('dog_prompts.txt') as f:
        lines = f.read().splitlines()
    random.seed(datetime.now().timestamp())
    return random.choice(lines)


def upload_images(uploads, num_images=4):
    """
    Загружает указанное количество изображений в VK и возвращает строку их ID для прикрепления к посту.
    """
    uploaded_imgs = [uploads.photo_wall(photos=[f'tmp/{i}.png'], group_id=GROUP_ID) for i in range(1, num_images + 1)]
    return ','.join([f'photo{uploaded_img[0]["owner_id"]}_{uploaded_img[0]["id"]}' for uploaded_img in uploaded_imgs])

def new_post(timestamp, vk, uploads):
    """
    Создает новый пост в VK с случайно сгенерированным промптом и изображениями, сгенерированными на его основе.
    """
    randseed = random.randrange(99999)
    translator = YandexFreeTranslate(api = "ios")
    prompt = get_random_prompt().capitalize()
    prompt_translated = translator.translate("en", "ru", prompt).capitalize()

    logging.info("Img params: %s %s (%s)", randseed, prompt, prompt_translated)

    req_json = get_json_from_horde(prompt, randseed)
    process_images_from_json(req_json)

    upimgs = upload_images(uploads)

    post_msg = f"⭐ Тема: {prompt_translated} ({prompt})\n🎲 Сид: {randseed}"
    vk.wall.post(message=post_msg, owner_id=-GROUP_ID, from_group=1,
                 attachments=upimgs, publish_date=timestamp, signed=0)
    logging.info("Post done")

def check_delayed_posts():
    """
    Проверяет наличие отсутствующих отложенных постов на следующие 24 часа и создает их при необходимости.
    """
    vk_session = vk_api.VkApi(token=VK_API_ACCESS_TOKEN)
    vk = vk_session.get_api()
    tools = vk_api.VkTools(vk_session)
    uploads = vk_api.VkUpload(vk_session)

    next_hour_dt = datetime.now().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)
    next_hour_ut = int(next_hour_dt.strftime('%s'))

    hours = [next_hour_ut + i * 3600 for i in range(24)]
    postponed_posts = tools.get_all('wall.get', 100, {'owner_id': -GROUP_ID, 'filter': 'postponed'})

    for hour in hours:
        matched = any(post['date'] == hour for post in postponed_posts['items'])
        if not matched:
            logging.info('%s MISSING, making new post', datetime.utcfromtimestamp(hour+3600*3))
            new_post(hour, vk, uploads)
        else:
            logging.info('%s OK', datetime.utcfromtimestamp(hour+3600*3))

    logging.info("Every post has been created")



def main():
    """
    Главная функция для запуска скрипта. Она непрерывно проверяет наличие отсутствующих отложенных постов каждые 30 минут.
    """
    logging.info(" ***  VK AI StableHorde Pics Poster bot  ***")

    while True:
        logging.info("Checking delayed posts")
        check_delayed_posts()
        logging.info("Waiting 30 minutes")
        time.sleep(30 * 60) # use time.sleep for better readability


if __name__ == '__main__':
    main()
