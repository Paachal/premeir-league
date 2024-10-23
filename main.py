from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from models import AdminUserModel
from auth import router as auth_router, get_current_admin_user, get_current_user  
import os
from database import teams_collection, news_collection, fixtures_collection, team_helper, news_helper, fixture_helper
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import hashlib
app = FastAPI()

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="supersecretkey")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(auth_router, prefix="/auth", tags=["auth"])

MONGO_DETAILS = "mongodb+srv://paschal:.adgjmptwpaschal@cluster0.dx4v8.mongodb.net/premeirdb?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.premeirdb

ADMIN_USERNAME = "paschal"
ADMIN_PASSWORD = ".adgjmptwpaschal"


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user = request.session.get("user")
    teams = [team_helper(team) for team in await teams_collection.find().to_list(100)]
    news = [news_helper(news_item) for news_item in await news_collection.find().to_list(100)]
    return templates.TemplateResponse("index.html", {"request": request, "teams": teams, "news": news, "user": user})

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

@app.post("/admin/fixtures/add", response_class=HTMLResponse)
async def add_fixture(request: Request, home_team: str = Form(...), away_team: str = Form(...), match_date: str = Form(...)):
    new_fixture = {"home_team": home_team, "away_team": away_team, "match_date": match_date}
    await db.fixtures.insert_one(new_fixture)
    return RedirectResponse(url="/admin/fixtures", status_code=303)

@app.post("/admin/fixtures/delete", response_class=HTMLResponse)
async def delete_fixture(request: Request, id: str = Form(...)):
    await fixtures_collection.delete_one({"_id": ObjectId(id)})
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
    teams = await db.teams.find().to_list(100)
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
    table = await db.table.find().to_list(100)
    return templates.TemplateResponse("table.html", {"request": request, "table": table})

@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_class=RedirectResponse)
async def post_signup(name: str = Form(...), email: str = Form(...), team: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": Request, "error": "Passwords do not match"})
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    new_user = {"name": name, "email": email, "team": team, "password": hashed_password}
    await db.users.insert_one(new_user)
    return RedirectResponse(url="/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=RedirectResponse)
async def post_login(email: str = Form(...), password: str = Form(...)):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = await db.users.find_one({"email": email, "password": hashed_password})
    if user:
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/login", status_code=303)    

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


@app.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/")
