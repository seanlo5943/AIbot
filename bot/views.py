from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, ImageSendMessage
from bs4 import BeautifulSoup
import requests

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parse = WebhookParser(settings.LINE_CHANNEL_SECRET)


def get_movie():
    
    try:
        url = 'https://movies.yahoo.com.tw/chart.html'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        trs = soup.find('div', class_="rank_list table rankstyle1").find_all(
            'div', class_='tr')
        i = 0
        for tr in trs[1:]:
            tds = tr.find_all('div', class_='td')
            rank = tds[0].text.strip()
            last_rank = tds[2].text.strip()
            if i == 0:
                title = tds[3].find('h2').text.strip()
            else:
                title = tds[3].text.strip()
            link = tds[3].find('a').get('href')
            i += 1
            data += f"{rank} {title} {link}\n"
        print(data)

        return data
    except Exception as e:
        print(e)
        return '取得排行中，請稍後在試...'


def get_biglottery():
    try:
        url = 'https://www.taiwanlottery.com.tw/lotto/lotto649/history.aspx'
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'lxml')
        trs = soup.find('table', class_="table_org td_hm").find_all('tr')
        data1 = [td.text.strip() for td in trs[0].find_all('td')]
        data2 = [td.text.strip() for td in trs[1].find_all('td')]
        numbers = [td.text.strip() for td in trs[4].find_all('td')][1:]
        data = ''
        for i in range(len(data1)):
            data += f'{data1[i]}:{data2[i]}\n'
        data += ','.join(numbers[:-1])+' 特別號:'+numbers[-1]
        print(data)

        return data
    except Exception as e:
        print(e)
        return '取得大樂透號碼，請稍後在試...'


def lottery(request):
    text = get_biglottery().replace('\n', '<br>')
    return HttpResponse(f'<h1>{text}</h1>')


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parse.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        for event in events:
            if isinstance(event, MessageEvent):
                text = event.message.text
                message = None
                print(text)
                if text == '1':
                    message = '早安'
                elif text == '2':
                    message = '午安'
                elif text == '3':
                    message = '晚安'
                elif '早安' in text:
                    message = '早安你好!'
                elif '電影' in text:
                    message = get_movie()
                elif '捷運' in text:
                    mrts = {
                        '台北': 'https://web.metro.taipei/pages/assets/images/routemap2023n.png',
                        '台中': 'https://assets.piliapp.com/s3pxy/mrt_taiwan/taichung/20201112_zh.png?v=2',
                        '高雄': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/%E9%AB%98%E9%9B%84%E6%8D%B7%E9%81%8B%E8%B7%AF%E7%B6%B2%E5%9C%96_%282020%29.png/550px-%E9%AB%98%E9%9B%84%E6%8D%B7%E9%81%8B%E8%B7%AF%E7%B6%B2%E5%9C%96_%282020%29.png'
                    }

                    image_url = 'https://web.metro.taipei/pages/assets/images/routemap2023n.png'
                    for mrt in mrts:
                        if mrt in text:
                            image_url = mrts[mrt]
                            break
                elif '樂透' in text:
                    message = get_biglottery()
                else:
                    message = '抱歉，我不知道你說甚麼?'

                if message is None:
                    message_obj = ImageSendMessage(image_url, image_url)
                else:
                    message_obj = TextSendMessage(text=message)

                line_bot_api.reply_message(event.reply_token, message_obj)
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def index(request):
    return HttpResponse("<h1>你好，我是AI機器人</h1>")
