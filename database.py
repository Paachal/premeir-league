from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb+srv://paschal:.adgjmptwpaschal@cluster0.dx4v8.mongodb.net/premeirdb?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.premeirdb

teams_collection = db.get_collection("teams")
news_collection = db.get_collection("news")
fixtures_collection = db.get_collection("fixtures")
table_collection = db.get_collection("table")
admin_users = db.get_collection("admin_users")
users = db.get_collection("users")

def team_helper(team) -> dict:
    return {
        "id": str(team["_id"]),
        "name": team["name"],
        "played": team.get("played", 0),
        "wins": team.get("wins", 0),
        "draws": team.get("draws", 0),
        "lost": team.get("lost", 0),
        "points": team.get("points", 0),
        "goals_for": team.get("goals_for", 0),
        "goals_against": team.get("goals_against", 0)
    }

def news_helper(news) -> dict:
    return {
        "id": str(news["_id"]),
        "headline": news["headline"],
        "details": news["details"],
    }

def fixture_helper(fixture) -> dict:
    return {
        "id": str(fixture["_id"]),
        "home_team": fixture["home_team"],
        "away_team": fixture["away_team"],
        "date": fixture["date"],
        "time": fixture["time"],
        "venue": fixture["venue"],
    }
