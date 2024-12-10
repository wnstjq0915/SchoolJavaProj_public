from datetime import datetime
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from mysql.connector import Error
from mysql_connection import get_connection
from utils import verify_access_token, call_recipe_openapi
from db_structure import RecipeMovement
from typing import List, Optional # 기본패키지
from config import Config
import boto3 # 람다에는 설치되어 있음.


router = APIRouter()


# 유저가 등록한 레시피 가져오기
@router.get("/getUserRecipe")
async def getUserRecipe(
    my_user_id: str = Depends(verify_access_token),
    title: Optional[str] = None,
    user_id: Optional[int] = None,
    ingredient: Optional[List[str]] = Query(None),
    paging: Optional[int] = 0
): # # ex: GET http://127.0.0.1:8000/getUserRecipe?title=스파게티&ingredient=토마토&ingredient=파스타

    if not my_user_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()
        # print(my_user_id)

        add_query = []
        format_query = [my_user_id]

        query = '''select r.id, title, `description`, userId, `name`, ingredient,
	visited, ifnull(star, 5) as star, if(rmf.id is not null, 1, 0) as favorite
from recipe r
join user u
    on r.userId=u.id
left join (
	select recipeId, avg(star) as star
    from recipeMovement
    group by recipeId
) rms
on r.id=rms.recipeId
left join (
	select id, recipeId
    from recipeMovement
    where star is null
		and `comment` is null
        and userId=%s
) rmf
on r.id=rmf.recipeId'''
        
        if title:
            add_query.append('title like %s')
            format_query.append(f'%{title}%')
        if user_id:
            add_query.append('userId=%s')
            format_query.append(user_id)
        if ingredient:
            for ing in ingredient:
                add_query.append('ingredient like %s')
                format_query.append(f'%{ing}%')

        if add_query:
            query += '\nwhere '
            query += ' and '.join(add_query)
        query += '\norder by visited / DATEDIFF(DATE_ADD(NOW(), INTERVAL 1 DAY), r.createdAt) desc, star desc, favorite desc, r.id desc'
        query += '\nlimit %s, 5;'

        print(query)

        format_query.append(paging)

        record = tuple(format_query)

        print('tuple: ', record)

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
        "result": "success", "item-count": len(result_list), 'items' : result_list
    }


# 오픈API 이용해서 받은 레시피 가져오기
@router.get("/getApiRecipe")
async def getApiRecipe(
    title: Optional[str] = None,
    paging: Optional[int] = 1
): # ex: GET http://127.0.0.1:8000/getApiRecipe?title=스파게티

    if not title:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    open_api_result = call_recipe_openapi(paging, paging + 4, title)

    if not open_api_result['result']:
        print("RecipeOpenAPI 이용 중에 예외가 발생했습니다:")
        raise HTTPException(status_code=400, detail="OpenAPI Error")

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success", "items": open_api_result['items']
    }


# 레시피 등록
@router.post("/postRecipe")
async def postRecipe(
    title: str = Form(...),
    description: str = Form(None),
    ingredient: str = Form(None),
    current_user: str = Depends(verify_access_token),
    detail1: str = Form(...), img1: UploadFile  = File(None),
    detail2: str = Form(None), img2: UploadFile = File(None),
    detail3: str = Form(None), img3: UploadFile = File(None),
    detail4: str = Form(None), img4: UploadFile = File(None),
    detail5: str = Form(None), img5: UploadFile = File(None),
    detail6: str = Form(None), img6: UploadFile = File(None),
    detail7: str = Form(None), img7: UploadFile = File(None),
    detail8: str = Form(None), img8: UploadFile = File(None),
    detail9: str = Form(None), img9: UploadFile = File(None),
    detail10: str = Form(None), img10: UploadFile = File(None),
    detail11: str = Form(None), img11: UploadFile = File(None),
    detail12: str = Form(None), img12: UploadFile = File(None),
    detail13: str = Form(None), img13: UploadFile = File(None),
    detail14: str = Form(None), img14: UploadFile = File(None),
    detail15: str = Form(None), img15: UploadFile = File(None),
    detail16: str = Form(None), img16: UploadFile = File(None),
    detail17: str = Form(None), img17: UploadFile = File(None),
    detail18: str = Form(None), img18: UploadFile = File(None),
    detail19: str = Form(None), img19: UploadFile = File(None),
    detail20: str = Form(None), img20: UploadFile = File(None),
):
    detail_li = [
        detail1, detail2, detail3, detail4, detail5,
        detail6, detail7, detail8, detail9, detail10,
        detail11, detail12, detail13, detail14, detail15,
        detail16, detail17, detail18, detail19, detail20
    ]
    img_file_li = [
        img1, img2, img3, img4, img5, img6, img7, img8, img9, img10,
        img11, img12, img13, img14, img15, img16, img17, img18, img19, img20
    ]
    img_url_li = [None for i in range(20)]

    print("유저ID: ", current_user)

    if not title or not current_user:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()
        query = '''insert into recipe(title, `description`, userId, ingredient)
values(%s, %s, %s, %s);'''
        record = (title,
                description,
                str(current_user),
                ingredient)
        cursor = connection.cursor()
        cursor.execute(query, record)
        
        connection.commit()
        recipe_id = cursor.lastrowid


        record = []
        i = 0
        current_time = datetime.now()
        s3 = boto3.client('s3',
            aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        while detail_li[i]:
            if img_file_li[i]: # 사진 있는지 확인
                # 수정된 사진부터 S3에 저장한다.
                img_url_li[i] = f"{current_time.isoformat().replace(':', '_').replace('.','_')}_{current_user}_{i+1}.jpg"
                try:
                    print(i)
                    s3.upload_fileobj(img_file_li[i].file,
                        Config.S3_BUCKET,
                        img_url_li[i],
                        ExtraArgs = {'ACL':'public-read',
                            'ContentType':'image/jpeg'})
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=str(e))
            record.append(detail_li[i])
            record.append(img_url_li[i])
            i+=1

        record = tuple(record)

        query = 'insert into recipeDetail(recipeId, detail, imgUrl) values'

        while i:
            query += '(' + str(recipe_id) + ', %s, %s)'
            if i == 1:
                query += ';'
            else:
                query += ','
            i-=1

        cursor.execute(query, record)
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {"result": "success"}


# todo: 하기 전에 1번 유저를 admin으로 설정
# API 레시피 상세내용 가져오기
@router.get("/getApiRecipeDetail")
async def getApiRecipeDetail(title: Optional[str] = None):

    if not title:
        raise HTTPException(status_code=400, detail='필수요소를 입력해주세요.')

    open_api_result = call_recipe_openapi(1, 1, title)
    if not open_api_result['result']:
        print('openapi 에러')
        raise HTTPException(status_code=500, detail=str('openapi 에러'))
    result = open_api_result['items']['row'][0]


    # 요청 본문에서 받은 데이터를 처리
    return {'result': 'success', 'items': result}


# 유저 레시피 상세내용 가져오기
@router.get("/getUserRecipeDetail")
async def getUserRecipeDetail(recipe_id: Optional[int] = None):

    if not recipe_id:
        raise HTTPException(status_code=400, detail='필수요소를 입력해주세요.')

    try:
        connection = get_connection()
        query = '''select *
from recipe r
join recipeDetail rd
on r.id = rd.recipeId
where recipeId = %s
	and userId != 1
order by rd.id;'''
        record = (str(recipe_id), )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)

        result_list = cursor.fetchall()

        cursor.close()
        query = '''update recipe
set visited=visited+1
where id=%s;'''
        record = (recipe_id, )
        cursor = connection.cursor()
        cursor.execute(query, record)
        connection.commit()

        # 리뷰
        cursor.close()
        query = '''select userId, name, star, comment, rm.createdAt
from recipeMovement rm
join user u
on rm.userId=u.id
where star is not null and recipeId=%s
order by rm.id desc;'''
        record = (str(recipe_id), )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)

        review_result_list = cursor.fetchall()

        # 댓글
        cursor.close()
        query = '''select rm.id, userId, name, comment, rm.createdAt
from recipeMovement rm
join user u
on rm.userId=u.id
where star is null and `comment` is not null and recipeId=%s
order by rm.id desc;'''
        record = (str(recipe_id), )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)

        comment_result_list = cursor.fetchall()

        cursor.close()
        connection.close()
    
        if len(result_list) == 0 :
            raise HTTPException(status_code=400, detail='상세정보가 없는 레시피입니다. 로직에러')

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    items = {'title': result_list[0]['title'], 'description': result_list[0]['description']}
    items['details'] = list()

    for result in result_list:
        items['details'].append({'detail': result['detail']})
        if result['imgUrl']:
            items['details'][-1]['img'] = Config.S3_BASE_URL + result['imgUrl']

    items['review'] = review_result_list
    items['comment'] = comment_result_list

    return {'result': 'success', 'items': items}


# 레시피 삭제
@router.delete("/deleteUserRecipe")
async def deleteUserRecipe(
    recipe_id: str,
    user_id: str = Depends(verify_access_token)
):
    """
    자신이 등록한 레시피일 경우만 삭제
    남의 것을 삭제시도하는 것든 따로 예외처리 X
    """
    
    if not recipe_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()
        query = '''delete from recipe where id = %s and userId=%s;'''
        record = (recipe_id, user_id)
        cursor = connection.cursor()
        cursor.execute(query, record)
        
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 유저 레시피 즐겨찾기 등록/삭제        # todo: 추후에 DB에서 함수로 처리하도록
@router.post("/postUserRecipeFavorites")
async def postRecipeFavorites(
    # recipe_id: str = None,
    recipe: RecipeMovement,
    user_id: str = Depends(verify_access_token)
):
    
    if not recipe.recipe_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = '''select userId, recipeId, createdAt from recipeMovement
where star is null and comment is null and userId=%s and recipeId=%s
order by id desc;'''
        record = (user_id, recipe.recipe_id)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)
        result_list = cursor.fetchall()

        if len(result_list) == 0: # 즐겨찾기된 레시피가 없으면 insert
            cursor.close()
            query = '''insert into recipeMovement(userId, recipeId) values(%s, %s);'''
            record = (user_id, recipe.recipe_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
        elif len(result_list) == 1: # 즐겨찾기된 레시피가 있으면 delete
            cursor.close()
            query = '''delete from recipeMovement
where star is null and comment is null and userId=%s and recipeId=%s;'''
            record = (user_id, recipe.recipe_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 자신의 즐겨찾기 가져오기
@router.get("/getRecipeFavorites")
async def getRecipeFavorites(
    user_id: str = Depends(verify_access_token)
):
    try:
        connection = get_connection()
        query = '''select userId, recipeId, createdAt from recipeMovement
where star is null and comment is null and userId=%s
order by id desc;'''
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



# 할거
# total 이용해서 프론트에서 페이징하고
# call_recipe_openapi 변경하고
# 리턴값 조정하기
# 페이징처리는 아래에 버튼이 있는 식이 아닌,
# 스크롤되면 자동으로 처리되도록


# 레시피 등록시 userId=1이면 api사용한 것을 저장한 것
# description에는 RCP_SEQ(일련번호) 저장하고
# 즐찾에서 누르면 api 호출해서 유저가 볼 수 있도록


# 리뷰 등록
# 없으면 넣고 있다면 수정
# comment를 수정하는 것이 아니라면 요청에 주지 않기.
@router.post("/postUserRecipeReview")
async def postUserRecipeReview(
    recipe: RecipeMovement,
    user_id: str = Depends(verify_access_token)
):
    
    if not recipe.recipe_id or recipe.star == None:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    if recipe.star < 1 or recipe.star > 10:
        raise HTTPException(status_code=400, detail="별점을 확인해주세요.")
    
    try:
        connection = get_connection()

        query = '''select userId, recipeId, star, `comment`, createdAt
from recipeMovement
where star is not null and userId=%s and recipeId=%s
order by id desc;'''
        record = (user_id, recipe.recipe_id)
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)
        result_list = cursor.fetchall()

        if len(result_list) == 0: # 즐겨찾기된 레시피가 없으면 insert
            cursor.close()

            query = '''insert into recipeMovement(userId, recipeId, star, `comment`)
values(%s, %s, %s, %s);'''
            if recipe.comment:
                record = (user_id, recipe.recipe_id, recipe.star, recipe.comment)
            else:
                record = (user_id, recipe.recipe_id, 'null')

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

        elif len(result_list) == 1: # 즐겨찾기된 레시피가 있으면 update
            cursor.close()

            if recipe.comment:
                query = '''update recipeMovement
set star=%s, `comment`=%s
where star is not null and userId=%s and recipeId=%s;'''
                record = (recipe.star, recipe.comment, user_id, recipe.recipe_id)
            else:
                query = '''update recipeMovement
set star=%s
where star is not null and userId=%s and recipeId=%s;'''
                record = (recipe.star, user_id, recipe.recipe_id)

            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 리뷰 삭제
@router.delete("/deleteUserRecipeReview/{recipe_id}")
async def deleteUserRecipeReview(
    recipe_id: int,
    user_id: str = Depends(verify_access_token)
):
    
    if not recipe_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = '''delete from recipeMovement
where star is not null and userId=%s and recipeId=%s;'''

        record = (user_id, recipe_id)
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


# 댓글 작성
@router.post("/postUserRecipeComment")
async def postUserRecipeComment(
    recipe: RecipeMovement,
    user_id: str = Depends(verify_access_token)
):
    if not recipe.recipe_id or recipe.comment == None:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = '''insert into recipeMovement(userId, recipeId, `comment`)
values(%s, %s, %s);'''
        record = (user_id, recipe.recipe_id, recipe.comment)

        cursor = connection.cursor()
        cursor.execute(query, record)
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 댓글 삭제
@router.delete("/deleteUserRecipeComment/{comment_id}")
async def deleteUserRecipeComment(
    comment_id: int,
    user_id: str = Depends(verify_access_token)
):
    if not comment_id or not user_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = '''delete from recipeMovement
where star is null
	and `comment` is not null
    and userId=%s
    and id=%s;'''
        record = (user_id, comment_id)

        cursor = connection.cursor()
        cursor.execute(query, record)
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 레시피의 댓글 가져오기
@router.get("/getRecipeComment/{recipe_id}")
async def getRecipeComment(
    recipe_id: int = None
):
    if not recipe_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")

    try:
        connection = get_connection()
        query = '''select rm.id, userId, `name`, `comment`, rm.createdAt
from recipeMovement rm
join user u
on rm.userId=u.id
where star is null and `comment` is not null
	and recipeId=%s
order by rm.id desc;'''
        record = (recipe_id, )
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


# 댓글 수정
@router.put("/putUserRecipeComment")
async def putUserRecipeComment(
    recipe: RecipeMovement,
    user_id: str = Depends(verify_access_token),
):
    if not recipe.comment_id or not user_id or not recipe.comment:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    try:
        connection = get_connection()

        query = '''update recipeMovement set `comment`=%s
where star is null and `comment` is not null
	and id=%s and userId=%s;'''
        record = (recipe.comment, recipe.comment_id, user_id)

        cursor = connection.cursor()
        cursor.execute(query, record)
        connection.commit()

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success"
    }


# 레시피의 리뷰 가져오기
@router.get("/getRecipeReview/{recipe_id}")
async def getRecipeReview(
    recipe_id: int = None
):
    if not recipe_id:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")

    try:
        connection = get_connection()
        query = '''select userId, name, star, comment, rm.createdAt
from recipeMovement rm
join user u
on rm.userId=u.id
where star is not null and recipeId=%s
order by rm.id desc;'''
        record = (recipe_id, )
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