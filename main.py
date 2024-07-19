from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from typing import List
from bson import ObjectId
import os
from dotenv import load_dotenv
import openai
app = FastAPI()

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

# MongoDB 설정
mongo = os.getenv('MONGODB_URI')
client = MongoClient(mongo)
db = client["para1"]
users_collection = db["Tusers"]
todos_collection = db["todos"]

# 모델 정의
class User(BaseModel):
    username: str
    password: str

class ToDoItem(BaseModel):
    title: str
    description: str = ""
    completed: bool = False

class ToDoItemInDB(ToDoItem):
    username: str
    
class VariableDescription(BaseModel):
    description: str
    naming_convention: str

# 유틸리티 함수
def get_user(username: str):
    return users_collection.find_one({"username": username})

def verify_user(username: str, password: str):
    user = get_user(username)
    if user and user["password"] == password:
        return True
    return False

# 엔드포인트
@app.post("/register")
def register(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    users_collection.insert_one(user.dict())
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: User):
    if not verify_user(user.username, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"message": "Login successful"}

@app.post("/todos/", response_model=ToDoItem)
def create_todo_item(todo: ToDoItem, username: str):
    if not get_user(username):
        raise HTTPException(status_code=400, detail="User not found")
    todo_in_db = ToDoItemInDB(**todo.dict(), username=username)
    todos_collection.insert_one(todo_in_db.dict())
    return todo

@app.get("/todos/", response_model=List[ToDoItem])
def read_todo_items(username: str):
    if not get_user(username):
        raise HTTPException(status_code=400, detail="User not found")
    todos = list(todos_collection.find({"username": username}))
    return [ToDoItem(**todo) for todo in todos]

@app.delete("/todos/")
def delete_todo_item(username: str, title: str):
    if not get_user(username):
        raise HTTPException(status_code=400, detail="User not found")
    result = todos_collection.delete_one({"username": username, "title": title})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="ToDo item not found")
    return {"message": "ToDo item deleted successfully"}

@app.post("/recommend")
async def recommend_variable_name(request: VariableDescription):
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"다음 기능이나 설명에 맞는 변수 이름을 {request.naming_convention} 규칙으로 5개 추천해 주세요: {request.description}"}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=prompt,
        max_tokens=300,
        temperature=0.7,
    )
    
    response_message = response.choices[0].message.content
    return {"recommendations": response_message.split("\n")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
