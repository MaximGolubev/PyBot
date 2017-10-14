# -*- coding: utf-8 -*-
from datetime import datetime
import time
import vk_api
import requests
import codecs
from urllib.request import urlopen, quote

vkToken = ''
yandexKey = ''
with open('keys.keys', 'r') as keysFile:
    vkToken = keysFile.readline().strip('\n')
    yandexKey = keysFile.readline().strip('\n')

vk = vk_api.VkApi(token = vkToken)
vk.auth()
values = {'out': 0,'count': 100,'time_offset': 60}

supportList = [u'Справка', u'Привет', u'Команды', u'Здрасте', u'Помоги', u'Помощь', u'справка', u'привет', u'команды', u'здрасте', u'помоги', u'помощь']
stationsDict = {}
with open('station_dict.dict', 'r', encoding='utf-8') as rFile:
    for line in rFile:
        key = line.split(' : ')[0]
        value = line.split(' : ')[1].strip('\n')
        stationsDict[key] = value

def write_msg(user_id, s):
    vk.method('messages.send', {'user_id':user_id,'message':s})

while True:
    response = vk.method('messages.get', values)
    if response['items']:
        values['last_message_id'] = response['items'][0]['id']

    for item in response['items']:
        msgBody = item['body']
        msgUnixTime = item['date']
        msgIsoTime = datetime.fromtimestamp(int(msgUnixTime)).isoformat()
        print(msgIsoTime[0:10])

        date = msgIsoTime[0:10]
        dateHour = int(msgIsoTime[11:13])
        dateMinute = int(msgIsoTime[14:16])
        print(dateHour, dateMinute)

        destString = 'empty'
        depString = 'empty'
        print(type(msgBody), msgBody)
        if (len(msgBody.split(' ')) == 2):
            depString = msgBody.split(' ')[0]
            destString = msgBody.split(' ')[1]
        if (len(msgBody.split(' ')) > 2):
            depString = msgBody.split(' ')[0]
            destString = msgBody.split(' ')[1]
            date = msgBody.split(' ')[2]
            dateHour = 4
            dateMinute = 0
        # if depString in supportList or destString in supportList:
        #     postText = 'Привет, я бот для получения расписаний электричек.\n\n' \
        #                'Для получения расписания электричек на сегодня введите команду в виде СтанцияОтправления СтанцияНазначения. В этом случае я выведу электрички, которые доступны на остаток текущего дня\n' \
        #                'Для получения расписания электричек на определенную дату введите команду в виде СтанцияОтправления СтанцияНазначения ГГГГ-ММ-ДД. В этом случае я выведу все электрички на введенную дату\n'
        #     write_msg(item[u'user_id'], postText)
        #     continue
        if (depString not in stationsDict) or (destString not in stationsDict):
            postText = 'Нет подходящих электричек. Попробуйте уточнить название станций. \n\n Доступные команды: \n[Станция отправления] [Станция прибытия] ' \
                       '\n[Станция отправления] [Станция прибытия] [ГГГГ-ММ-ДД]'
            write_msg(item[u'user_id'], postText)
            continue

        print(depString, destString)

        url = 'https://api.rasp.yandex.net/v3.0/search/?apikey=' + yandexKey + \
              '&format=json' \
              '&from=' + stationsDict[depString] + \
              '&to=' + stationsDict[destString] + \
              '&lang=ru_RU' \
              '&page=1' \
              '&date=' + date + \
              '&transport_types=suburban'
        print(url)

        request = requests.get(url)
        data = request.json()

        postText = 'Расписание электричек на ' + date + '\n'
        if 'segments' not in data:
            postText = 'Нет подходящих электричек. Попробуйте уточнить название станций. \n\n Доступные команды: \n[Станция отправления] [Станция прибытия] ' \
                       '\n[Станция отправления] [Станция прибытия] [ГГГГ-ММ-ДД]'
            write_msg(item[u'user_id'], postText)
            continue
        for train in data['segments']:
            depHour = int(train['departure'][11:13])
            depMinute = int(train['departure'][14:16])
            if msgIsoTime[0:10] == date and (dateHour > depHour or (dateHour == depHour and dateMinute > depMinute)):
                continue
            postText+= train['departure'][11:16] + ' : ' + train['arrival'][11:16] + '\t | ' + train['thread']['short_title'] + '\n'
        #print(postText)
        if postText == 'Расписание электричек на ' + date + '\n':
            postText+='\nК сожалению, все электрички на текущую дату (' + date + ') ' + 'ушли. ' \
                        'Попробуйте поискать электрички по точной дате, чтобы увидеть первые утренние! \nФормат ввода даты ГГГГ-ММ-ДД\n'
        write_msg(item[u'user_id'],postText)

    time.sleep(3)