from fastapi import APIRouter, Depends, HTTPException
from mysql.connector import Error
from mysql_connection import get_connection
from utils import verify_access_token
from db_structure import Youtube
from typing import Optional # 기본패키지
import requests
from bs4 import BeautifulSoup


router = APIRouter()


# 유튜브 등록하기
@router.post("/postYoutube")
async def postYoutube(
    user_id: str = Depends(verify_access_token),
    youtube : Youtube = None,
):

    if not youtube.url or not user_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()
        query = 'insert into youtube(userId, url) values(%s, %s);'
        record = (user_id, youtube.url)
        cursor = connection.cursor()
        cursor.execute(query, record)
        
        connection.commit()
        ### DB에 데이터를 insert 한 후에, 
        ### 그 인서트된 행의 아이디를 가져오는 코드!!
        youtube_id = cursor.lastrowid

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {"result": "success", "youtube_id": youtube_id}


# 유튜브 가져오기
@router.get("/getYoutube")
async def getYoutube(
    user_id: str = Depends(verify_access_token)
):
    if not user_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")

    try:
        connection = get_connection()
        query = 'select id, url from youtube where userId=%s order by id desc;'
        record = (user_id, )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)

        result_list = cursor.fetchall()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success",
        'items': result_list
    }


# 유튜브 삭제
@router.delete("/deleteYoutube/{youtube_id}")
async def deleteYoutube(
    youtube_id: int,
    user_id: str = Depends(verify_access_token)
):
    if not youtube_id or not user_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = 'delete from youtube where id=%s and userId=%s;'
        record = (youtube_id, user_id)

        cursor = connection.cursor()
        cursor.execute(query, record)
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {"result": "success"}


# 뉴스 리스트
@router.get("/getNewsList")
async def getNewsList(page: Optional[str] = None):
    try:
        url = "http://realfoods.co.kr/section.php?sec=eat"
        if page:
            url += '&pg=' + page
        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        news_li = soup.find('div', attrs={'class': 'result_list'}).find('ul').find_all('li')

        result = []

        for news in news_li:
            add_result = {}
            add_result['title'] = news.find('div', attrs={'class': 's_r_t_box'}).text
            add_result['content'] = news.find('div', attrs={'class': 's_result_ss'}).find('a').text
            add_result['img'] = 'http:' + news.find('div', attrs={'class': 's_result_i'}).find('a').find('img')['src']
            add_result['link'] = 'http://realfoods.co.kr/' + news.find('div', attrs={'class': 's_result_i'}).find('a')['href']
            result.append(add_result)

    except:
        return {'result':'fail'}, 500

    return {'result':'success', 'items' : result}


# 뉴스 상세보기
@router.post("/postNewsDetail")
async def postNewsDetail(youtube : Youtube = None):
    if not youtube.url:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")

    try:
        response = requests.get(youtube.url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        result = dict()
        result['title'] = soup.select_one('body > div > div.viewpage_top > div.viewpage_center > ul > li:nth-child(1)').text.strip()

        content_li = soup.select_one('#view_content')
        result['img'] = 'http:' + content_li.select_one('#view_content > table:nth-child(3) > tbody > tr:nth-child(1) > td').find('img')['src']
        result['content'] = list()

        for i, content in enumerate(content_li.find_all('p')):
            if i==0 and content.text.find(']'):
                result['content'].append(content.text[content.text.find(']')+1:].strip())
                continue
            result['content'].append(content.text)
        result['content'] = '\n\n'.join(result['content'])

    except:
        return {'result':'fail'}, 500

    return {'result':'success', 'items' : result}