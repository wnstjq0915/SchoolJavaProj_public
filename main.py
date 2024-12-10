from fastapi import FastAPI
from resources import user, recipe, others
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

app.include_router(user.router)
app.include_router(recipe.router)
app.include_router(others.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}