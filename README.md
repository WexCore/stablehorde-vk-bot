# stablehorde-vk-bot
## Описание
Этот проект представляет собой бота для VK, который создает посты с сгенерированными изображениями на основе случайных промптов. Бот использует API StableHorde для генерации изображений и Yandex Translate для перевода промптов на русский язык.

## Установка

``` bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
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
Бот будет непрерывно проверять наличие отсутствующих отложенных постов и создавать их при необходимости. Изображения будут сгенерированы через Stable Horde на основе случайных промптов из файла и загружены в VK.
