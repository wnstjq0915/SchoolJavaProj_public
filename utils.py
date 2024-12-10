from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import pbkdf2_sha256
from jose import jwt, JWTError
from config import Config
import requests

# 원문 비밀번호를, 단방향 암호화 하는 함수 
def hash_password(original_passwod) :    
    password = original_passwod + Config.SALT
    password = pbkdf2_sha256.hash(password)
    return password

# 유저가 로그인할때, 입력한 비밀번호가 맞는지 체크하는 함수
def check_password(original_password, hashed_password) :    
    password = original_password + Config.SALT
    check = pbkdf2_sha256.verify(password , hashed_password)
    return check

# 토큰 생성
def create_access_token(data: dict):
    data.update({"iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(data, Config.SALT, algorithm=Config.HASHING_ALGORITHM)
    return encoded_jwt

# from fastapi.security import OAuth2PasswordBearer
# OAuth2 Password Bearer 토큰
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT에서 jti 추출 함수
def get_jti(token: str):
    try:
        payload = jwt.decode(token, Config.SALT, algorithms=[Config.HASHING_ALGORITHM])
        return payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# OAuth2PasswordBearer: Authorization 헤더에서 토큰 추출
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
jwt_blocklist = set()

# 토큰 검증 함수
def verify_access_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401, detail="자격 증명을 확인할 수 없습니다."
    )
    # 로그아웃된 유저의 토큰은 재사용되지 못 하도록.
    if token in jwt_blocklist:
        # print("블랙리스트: ",jwt_blocklist)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been logged out",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, Config.SALT, algorithms=[Config.HASHING_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id

# 레시피 OpenApi 활용하기
# 재료로 검색 불가능한 것 수정하기.

def call_recipe_openapi(startIdx: int, endIdx: int, RCP_NM: str):

    # API 엔드포인트 URL
    url = f"{Config.RECIPE_API_HOST}/{Config.RECIPE_API_KEY}/{Config.RECIPE_API_SERVICE}/json/{startIdx}/{endIdx}/RCP_NM={RCP_NM}"

    print(url)

    # GET 요청 보내기
    # response = requests.get(url, params=params)
    response = requests.get(url)

    # 응답이 성공적인지 확인
    if response.status_code == 200:
        open_api_result = dict()

        # JSON 형식으로 응답 데이터를 파싱하여 사용
        data = response.json()
        # print("응답 데이터:", data)
        data = data['COOKRCP01']

        open_api_result['total-count'] = data['total_count']
        open_api_result['item-count'] = str(len(data['row']))
        open_api_result['row'] = data['row']

        return {'result': True, 'items': open_api_result}

    else:
        print("요청 실패:", response.status_code)
        return {'result': False}

    # 리턴 수정하기