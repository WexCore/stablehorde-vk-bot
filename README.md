# stablehorde-vk-bot
## Описание
Этот проект представляет собой бота для VK, который создает посты на следующие 24 часа, используя сгенерированными через Stable Diffusion изображениями на основе случайных промптов. Бот использует API StableHorde для генерации изображений и Yandex Translate для перевода промптов на русский язык.

## Установка

``` bash
git clone https://github.com/WexCore/stablehorde-vk-bot.git
cd stablehorde-vk-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Использование
``` bash
source venv/bin/activate
python main.py
```
Бот будет  проверять наличие отсутствующих отложенных постов каждые 30 минут и создавать их при необходимости. Изображения будут сгенерированы через Stable Horde на основе случайных промптов из файла и загружены в VK.
