import requests
import re
import json

def getJson(iter):
    req = requests.get("https://www.krea.ai/api/prompts?query=dog&pageSize=100&page=" + str(iter + 100))
    # print(req)
    return req.json()

def getPromptList(stringOfJson):
    # print(json.dumps(stringOfJson))
    # for item in req['prompts']:
    #     # print(item)
    #     # print(item['prompts'])
    #     print(item)

    result = re.findall('(?<="prompt": ").*?(?=[,"])', json.dumps(stringOfJson))
    print(result)
    return result


if __name__ == "__main__":
    # x = getJson()
    # print(type(x['prompts']))
    # print(x['prompts'])
    open('prompts.txt', 'w').close()
    for iter in range(100):
        js = getJson(iter)
        y = getPromptList(js)
        with open(r'prompts.txt', 'a') as fp:
            for item in y:
            # write each item on a new line
                fp.write("%s\n" % item)
            print('Done')