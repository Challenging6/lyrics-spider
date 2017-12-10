import requests
import json
from requests import ConnectionError
import re
import asyncio
import aiohttp

album_urls = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_album.fcg?g_tk=1705274270&jsonpCallback=MusicJsonCallbacksinger_album&loginUin=992871471&hostUin=0&format=jsonp&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq&needNewCode=0&singermid={singermid}&order=time&begin=0&num=30&exstatus=1'
song_info_url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric.fcg?nobase64=1&musicid={musicid}"
album_url = "https://y.qq.com/n/yqq/album/{album_id}.html"
search_url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?ct=24&qqmusic_ver=1298&new_json=1&remoteplace=txt.yqq.song&searchid=63569007829239885&t=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=20&w={singer}'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'referer': 'https://y.qq.com/n/yqq/song/003OUlho2HcRHC.html',
}


def get_html(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(response.status_code)
            return None
    except ConnectionError:
        print("ConnectionError!")

"""
qq音乐的很多数据都是jsonp格式,先要把他转化成json格式
"""
def parse_jsonp(content):
    json_str = re.match('.*?\(({.*?})\n\)', content).group(1)
    return json.loads(json_str)

"""
异步爬取专辑页面
"""
async def download_album(album_id):
    a_url = album_url.format(album_id=album_id)
    print("album_url:", a_url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=a_url, headers=headers) as response:
            if response.status == 200:
                resp = await response.text()
                parse_song(resp)
            else:
                print(response.status)

tasks = []

def parse_album(singermid):
    url = album_urls.format(singermid=singermid)
    content = get_html(url)
    json_str = parse_jsonp(content)
    album_infos = json_str['data']['list']
    loop1 = asyncio.get_event_loop()
    tasks1 = []
    for album in album_infos:
        album_id = album.get("albumMID")
        tasks1.append(download_album(album_id))
    loop1.run_until_complete(asyncio.wait(tasks1))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))

"""
异步爬取歌曲页面
"""
async def download_song(url):
    print("crawling", url)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                r = await response.text()

                parse_lyric(r)
            else:
                print(response.status)


def parse_song(content):
    song_id = re.findall(r'"songid":(.*?),', content)
    song_id = list(set(song_id))
    for item in song_id:
        url = song_info_url.format(musicid=item)
        tasks.append(download_song(url))
count = 0

def parse_lyric(content):
    global count
    count+=1
    print('having crawled %d songs' %count)
    lyric = re.findall("[\u4e00-\u9fa5]+", content)
    with open('jay_lyric.txt', 'a') as f:
        lyric = lyric[3:]
        for i in lyric:
            f.write(i + '\n')
        f.write('\n')


def get_singer_mid(singer):
    url = search_url.format(singer=singer)
    content = get_html(url)
    try:
        singer_mid = re.findall(r'"singerMID":"(.*?)"', content)[0]
        return singer_mid
    except:
        print("未找到")


def run():
    singer = input("please input singer name：")
    singer_mid = get_singer_mid(singer)
    parse_album(singer_mid)


if __name__ == "__main__":
    run()
