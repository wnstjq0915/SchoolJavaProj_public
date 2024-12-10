from pydantic import BaseModel
import datetime

# 클라이언트에서 요청할 값만 정의

# 유저
class User(BaseModel):
    account: str = None
    password: str = None
    name: str = None
    number: str = None

# 팔로우
class Follow(BaseModel):
    follower_id: int = None
    followee_id: int = None

# 활동정지
class Restriction(BaseModel):
    user_id: int = None
    restart_date: datetime.date = None # 추후 확인하기(현재시간 기본값 주기?)

# 신고
class Report(BaseModel):
    reporter: int = None
    reportee: int = None
    comment: str = None
    check: int = None

# 유튜브 즐찾
class Youtube(BaseModel):
    user_id: int = None
    url: str = None

# 게시판타입
class PostType(BaseModel):
    type: str = None

# 게시글
class Post(BaseModel):
    user_id: int = None
    post_type_id: int = None
    title: str = None
    detail: str = None

# 댓글
class PostComment(BaseModel):
    post_id: int = None
    user_id: int = None
    comment: str = None

# 레시피
class Recipe(BaseModel):
    title: str = None
    description: str = None
    user_id: int = None
    ingredient: str = None # 재료, 널 허용
    visited: int = None

# 레시피 상세정보
class RecipeDetail(BaseModel):
    recipe_id: int = None
    detail: str = None
    imgUrl: str = None # 이미지, 널 허용

# 레시피에 대한 활동(댓글, 별점, 팔로우)
class RecipeMovement(BaseModel):
    comment_id: int = None
    recipe_id: int = None
    user_id: int = None
    comment: str = None # 댓글, 널 허용
    star: int = None # 1~10, 널 허용
