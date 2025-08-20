import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from text.env file
load_dotenv("text.env")

# Config from environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
TO_EMAIL = os.getenv("TO_EMAIL")

def get_yesterdays_dodgers_game():
    # Calculate yesterday's date
    yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
    
    # MLB Stats API endpoint for schedule by date
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={yesterday}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Dodgers team ID is 119
        dodgers_team_id = 119
        
        # Loop through dates and games to find Dodgers games
        for date_info in data.get("dates", []):
            for game in date_info.get("games", []):
                away_team_id = game["teams"]["away"]["team"]["id"]
                home_team_id = game["teams"]["home"]["team"]["id"]
                
                if away_team_id == dodgers_team_id or home_team_id == dodgers_team_id:
                    # Check if Dodgers were the home team
                    dodgers_is_home = (home_team_id == dodgers_team_id)
                    
                    # Get scores
                    away_score = game["teams"]["away"].get("score", 0)
                    home_score = game["teams"]["home"].get("score", 0)
                    
                    # Check if Dodgers won
                    if dodgers_is_home:
                        dodgers_won = home_score > away_score
                        dodgers_score = home_score
                        opponent_score = away_score
                        opponent_team = game["teams"]["away"]["team"]["name"]
                    else:
                        dodgers_won = away_score > home_score
                        dodgers_score = away_score
                        opponent_score = home_score
                        opponent_team = game["teams"]["home"]["team"]["name"]
                    
                    # Return game info
                    return {
                        "date": yesterday,
                        "home_game": dodgers_is_home,
                        "won": dodgers_won,
                        #"home_game": True,
                        #"won": True,
                        "dodgers_score": dodgers_score,
                        "opponent_score": opponent_score,
                        "opponent_team": opponent_team,
                        "venue": game.get("venue", {}).get("name", "Unknown")
                    }
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = TO_EMAIL
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
        server.quit()
        
        print("Email sent successfully!")
        
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    game = get_yesterdays_dodgers_game()
    
    if game is None:
        print("No Dodgers game found for yesterday.")
        return
    
    print(f"Date: {game['date']}")
    print(f"Home game: {game['home_game']}")
    print(f"Dodgers won: {game['won']}")
    print(f"Score: Dodgers {game['dodgers_score']} - {game['opponent_score']} {game['opponent_team']}")
    print(f"Venue: {game['venue']}")
    
    # Send email only if Dodgers won AND it was a home game
    if game["won"] and game["home_game"]:
        subject = "🎉 LA Dodgers Won a Home Game!"
        body = f"""Great news! The LA Dodgers won their home game yesterday ({game['date']})!

Final Score: Dodgers {game['dodgers_score']} - {game['opponent_score']} {game['opponent_team']}
Venue: {game['venue']}

Go Dodgers! 🟢⚾"""
        
        send_email(subject, body)
    else:
        if not game["won"]:
            print("Dodgers lost, no email sent.")
        elif not game["home_game"]:
            print("Dodgers didn't play at home, no email sent.")

if __name__ == "__main__":
    main()

