from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from models import AdminUserModel, User, UserInDB, UserInResponse, UserInLogin, BaseModel
from auth import router as auth_router, get_current_admin_user, get_current_user  
import os
from database import teams_collection, news_collection, fixtures_collection, team_helper, news_helper, fixture_helper, admin_users, users_collection, table_collection, db
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from utils import hash_password, verify_password
from pymongo.errors import DuplicateKeyError
import hashlib
import json
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(auth_router, prefix="/auth", tags=["auth"])

app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ADMIN_USERNAME = "paschal"
ADMIN_PASSWORD = ".adgjmptwpaschal"


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    username = request.session.get("user")
    teams = [team_helper(team) for team in await teams_collection.find().to_list(100)]
    news = [news_helper(news_item) for news_item in await news_collection.find().to_list(100)]
    fixture = [fixture_helper(new_fixture) for new_fixture in await fixtures_collection.find().to_list(100)]
    return templates.TemplateResponse("index.html", {"request": request, "teams": teams, "news": news, "fixture":fixture, "user": username})

@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="admin_token", value="some_admin_token")  # This is a placeholder for actual token management
        return response
    else:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid username or password"})


@app.get("/admin/table", response_class=HTMLResponse)
async def admin_table(request: Request):
    table = await db.table.find().to_list(100)
    return templates.TemplateResponse("admin_table.html", {"request": request, "table": table})

@app.post("/admin/table/add", response_class=RedirectResponse)
async def add_table_team(request: Request, name: str = Form(...)):
    await db.table.insert_one({"name": name, "played": 0, "won": 0, "drawn": 0, "lost": 0, "goals_for": 0, "goals_against": 0, "goal_difference": 0, "points": 0})
    return RedirectResponse(url="/admin/table", status_code=303)

@app.post("/admin/table/update", response_class=RedirectResponse)
async def update_table_team(request: Request, id: str = Form(...), played: int = Form(...), won: int = Form(...), drawn: int = Form(...), lost: int = Form(...), goals_for: int = Form(...), goals_against: int = Form(...), points: int = Form(...)):
    goal_difference = goals_for - goals_against
    await db.table.update_one({"_id": ObjectId(id)}, {"$set": {"played": played, "won": won, "drawn": drawn, "lost": lost, "goals_for": goals_for, "goals_against": goals_against, "goal_difference": goal_difference, "points": points}})
    return RedirectResponse(url="/admin/table", status_code=303)

@app.post("/admin/table/delete", response_class=RedirectResponse)
async def delete_table_team(request: Request, id: str = Form(...)):
    await db.table.delete_one({"_id": ObjectId(id)})
    return RedirectResponse(url="/admin/table", status_code=303)

@app.get("/admin/news", response_class=HTMLResponse)
async def admin_news(request: Request):
    news = await db.news.find().to_list(100)
    return templates.TemplateResponse("admin_news.html", {"request": request, "news": news})

@app.post("/admin/news/add", response_class=HTMLResponse)
async def add_news(request: Request, headline: str = Form(...), details: str = Form(...)):
    new_news = {"headline": headline, "details": details}
    await db.news.insert_one(new_news)
    return RedirectResponse(url="/admin/news", status_code=303)

@app.post("/admin/news/delete", response_class=HTMLResponse)
async def delete_news(request: Request, id: str = Form(...)):
    await news_collection.delete_one({"_id": ObjectId(id)})
    return RedirectResponse(url="/admin/news", status_code=303)

@app.get("/admin/fixtures", response_class=HTMLResponse)
async def admin_fixtures(request: Request):
    fixtures = await db.fixtures.find().to_list(100)
    return templates.TemplateResponse("admin_fixtures.html", {"request": request, "fixtures": fixtures})

@app.post("/admin/fixtures/add", response_class=RedirectResponse)
async def add_fixture(request: Request, home_team: str = Form(...), away_team: str = Form(...), match_date: str = Form(...), match_time: str = Form(...), venue: str = Form(...)):
    new_fixture = {
        "home_team": home_team,
        "away_team": away_team,
        "date": match_date,
        "time": match_time,
        "venue": venue
    }
    await db.fixtures.insert_one(new_fixture)
    return RedirectResponse(url="/admin/fixtures", status_code=303)

@app.post("/admin/fixtures/update", response_class=RedirectResponse)
async def update_fixture(request: Request, fixture_id: str = Form(...), home_team: str = Form(...), away_team: str = Form(...), match_date: str = Form(...), match_time: str = Form(...), venue: str = Form(...)):
    await db.fixtures.update_one({"_id": ObjectId(fixture_id)}, {"$set": {
        "home_team": home_team,
        "away_team": away_team,
        "date": match_date,
        "time": match_time,
        "venue": venue
    }})
    return RedirectResponse(url="/admin/fixtures", status_code=303)

@app.post("/admin/fixtures/delete", response_class=RedirectResponse)
async def delete_fixture(request: Request, fixture_id: str = Form(...)):
    await fixtures_collection.delete_one({"_id": ObjectId(fixture_id)})
    return RedirectResponse(url="/admin/fixtures", status_code=303)

@app.get("/admin/teams", response_class=HTMLResponse)
async def admin_teams(request: Request):
    teams = await db.teams.find().to_list(100)
    return templates.TemplateResponse("admin_teams.html", {"request": request, "teams": teams})

@app.post("/admin/teams/add", response_class=RedirectResponse)
async def add_team(request: Request, name: str = Form(...)):
    await db.teams.insert_one({"name": name, "history": "", "about": ""})
    return RedirectResponse(url="/admin/teams", status_code=303)

@app.post("/admin/teams/update", response_class=RedirectResponse)
async def update_team(request: Request, id: str = Form(...), history: str = Form(...), about: str = Form(...)):
    await db.teams.update_one({"_id": ObjectId(id)}, {"$set": {"history": history, "about": about}})
    return RedirectResponse(url="/admin/teams", status_code=303)

@app.post("/admin/teams/delete", response_class=RedirectResponse)
async def delete_team(request: Request, id: str = Form(...)):
    await db.teams.delete_one({"_id": ObjectId(id)})
    return RedirectResponse(url="/admin/teams", status_code=303)

@app.get("/teams", response_class=HTMLResponse)
async def view_teams(request: Request):
    teams = await teams_collection.find().to_list(100)
    return templates.TemplateResponse("teams.html", {"request": request, "teams": teams})



@app.get("/news", response_class=HTMLResponse)
async def read_news(request: Request):
    news = await news_collection.find().to_list(100)
    return templates.TemplateResponse("news.html", {"request": request, "news": news})

@app.get("/fixtures", response_class=HTMLResponse)
async def read_fixtures(request: Request):
    fixtures = await fixtures_collection.find().to_list(100)
    return templates.TemplateResponse("fixtures.html", {"request": request, "fixtures": fixtures})

@app.get("/table", response_class=HTMLResponse)
async def view_table(request: Request):
    table = await table_collection.find().to_list(100)
    return templates.TemplateResponse("table.html", {"request": request, "table": table})

@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, name: str = Form(...), email: str = Form(...), favorite_team: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match"})
    
    user = await users_collection.find_one({"email": email})
    if user:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already registered"})

    hashed_password = hash_password(password)
    new_user = {
        "username": name,
        "email": email,
        "favorite_team": favorite_team,
        "password": hashed_password
    }
    await users_collection.insert_one(new_user)
    
    request.session["user"] = name

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await users_collection.find_one({"email": email})
    if user and pwd_context.verify(password, user["password"]):
        request.session["user"] = user["username"]
        return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=400, detail="Invalid email or password")


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
    
