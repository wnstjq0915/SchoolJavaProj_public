from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from mysql.connector import Error
from mysql_connection import get_connection
from utils import check_password, hash_password, create_access_token
from db_structure import User # Pydantic 모델 정의
from utils import jwt_blocklist


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
"JWT 토큰"

"""
전화번호 - 넣으면 -로 split하고 안 넣으면 그냥 번호만

db엔 그냥 번호만
"""


# todo: 이미 가입된 회원 검증
# 백엔드에서 account가 unique로 발생하는 예외처리하기
# select로 account여부 있는지 확인하는 것은 비효율적


# 회원가입
@router.post("/userRegister")
async def register(user: User):
    
    if not user.account or not user.password or not user.number or not user.name:
        raise HTTPException(status_code=400, detail="필수요소를 입력해주세요.")
    
    # 비밀번호를 암호화 
    hashed_password = hash_password(user.password)

    if  '-' in user.number:
        user.number = ''.join(list(user.number.split('-')))

    if len(user.number) != 11:
        raise HTTPException(status_code=400, detail="전화번호가 올바르지 않습니다.")

    try:
        connection = get_connection()
        query = '''insert into user 
(account, password, name, number)
values
(%s, %s, %s, %s);'''
        record = (user.account,
                hashed_password,
                user.name,
                user.number)
        cursor = connection.cursor()
        cursor.execute(query, record)
        
        connection.commit()
        ### DB에 데이터를 insert 한 후에, 
        ### 그 인서트된 행의 아이디를 가져오는 코드!!
        user_id = cursor.lastrowid

        cursor.close()
        connection.close()

    except Error as e:
        print(e)
        if str(e).endswith("'user.email_UNIQUE'"):
            raise HTTPException(status_code=400, detail="중복된 아이디입니다.")
        raise HTTPException(status_code=500, detail=str(e))

    # jwt생성
    access_token = create_access_token(data={"sub": str(user_id)})

    # 요청 본문에서 받은 데이터를 처리
    return {
        "result": "success",
        "access_token": access_token
    }


# 로그인
@router.post("/userLogin")
async def login(user: User):

    print('로그인 호출')
    
    if not user.account or not user.password:
        raise HTTPException(status_code=400, detail='필수요소를 입력해주세요.')


    try:
        connection = get_connection()
        query = '''select id, account, password, name, number
                    from user
                    where account=%s;'''
        record = (user.account, )
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, record)

        result_list = cursor.fetchall()

        cursor.close()
        connection.close()
    
        if len(result_list) == 0 :
            raise HTTPException(status_code=400, detail='회원가입 되지 않은 아이디 입니다.')

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    
    # 비밀번호를 암호화시켜 기존에 저장된 비밀번호와 비교
    try:
        check = check_password(user.password, result_list[0]['password'] )
    

        if check == False :
            raise HTTPException(status_code=400, detail='비밀번호가 틀렸습니다.')
        
        
        print(result_list[0])

        # jwt생성
        # access_token = create_access_token(data={"sub": str(user_id)})
        access_token = create_access_token(data={"sub": str(result_list[0]['id'])})

    except Error as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    # 요청 본문에서 받은 데이터를 처리
    return {
        "id": result_list[0]['id'],
        "name": result_list[0]['name'],
        "number": result_list[0]['number'],
        'access_token':access_token
    }


# 로그아웃
@router.delete("/userLogout")
async def logout(token: str = Depends(oauth2_scheme)):
    jwt_blocklist.add(token)
    # print(jwt_blocklist)
    return {"result": "success"}