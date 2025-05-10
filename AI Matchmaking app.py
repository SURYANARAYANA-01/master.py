import streamlit as st 
import pandas as pd 
import json 
from sklearn.feature_extraction.text 
import TfidfVectorizer 
from sklearn.metrics.pairwise 
import cosine_similarity 
import os 
import requests 
from PIL 
import Image 
from io 
import BytesIO 
from datetime 
import datetime 
import time

Constants

DATA_URL = "https://raw.githubusercontent.com/amankharwal/Website-data/master/imdb_top_1000.csv" POSTER_PLACEHOLDER = "https://via.placeholder.com/150x225?text=No+Poster" MIN_PASSWORD_LENGTH = 6 XP_PER_RATING = 15 XP_PER_WATCH = 10 XP_LEVEL_THRESHOLD = 100

Initialize users.json if it doesnot exist

if not os.path.exists("users.json"): with open("users.json", "w") as f: json.dump({}, f)

@st.cache_data def load_movies(): try: df = pd.read_csv(DATA_URL) df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x) df['Runtime'] = df['Runtime'].str.extract('(\d+)').astype(float) df['Gross'] = pd.to_numeric(df['Gross'].str.replace('[^\d]', '', regex=True), errors='coerce') df['combined_features'] = ( df['Genre'].fillna('') + " " + df['Director'].fillna('') + " " + df['Overview'].fillna('') ).str.lower() return df except Exception as e: st.error(f"Error loading movie data: {str(e)}") return pd.DataFrame({ "Series_Title": ["Sample Movie 1", "Sample Movie 2"], "Genre": ["Action", "Comedy"], "Director": ["Director A", "Director B"], "Overview": ["Sample overview 1", "Sample overview 2"], "IMDB_Rating": [7.5, 8.0], "Poster_Link": [POSTER_PLACEHOLDER, POSTER_PLACEHOLDER], "Runtime": [120, 90], "combined_features": ["action director a sample overview 1", "comedy director b sample overview 2"] })

@st.cache_resource def vectorize(df): tfidf = TfidfVectorizer(stop_words="english", max_features=5000) matrix = tfidf.fit_transform(df["combined_features"]) return tfidf, matrix

def load_users(): try: with open("users.json", "r") as f: return json.load(f) except Exception as e: st.error(f"Error loading user data: {e}") return {}

def save_users(data): try: with open("users.json", "w") as f: json.dump(data, f, indent=4) except Exception as e: st.error(f"Error saving user data: {e}")

def load_poster(url): try: if url == POSTER_PLACEHOLDER: return Image.new('RGB', (150, 225), color='gray') response = requests.get(url, timeout=5) return Image.open(BytesIO(response.content)) except: return Image.new('RGB', (150, 225), color='gray')

def register_user(username, password, users): if len(username) < 3: return "Username must be at least 3 characters" if len(password) < MIN_PASSWORD_LENGTH: return f"Password must be at least {MIN_PASSWORD_LENGTH} characters" if username in users: return "Username already exists"

users[username] = {
    "password": password,
    "friends": [],
    "watched": [],
    "continue_watching": [],
    "favorites": [],
    "xp": 0,
    "level": 1,
    "ratings": {},
    "chats": {},
    "notifications": [],
    "join_date": datetime.now().strftime("%Y-%m-%d"),
    "preferences": {"genres": [], "actors": [], "directors": []}
}
save_users(users)
return None

def main(): st.set_page_config(page_title="AI Movie Matchmaker", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "current_movie" not in st.session_state:
    st.session_state.current_movie = None
if "last_notification_check" not in st.session_state:
    st.session_state.last_notification_check = 0

df = load_movies()
tfidf, matrix = vectorize(df)
users = load_users()

def login_page():
    st.title("Login or Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.user = username
            st.session_state.page = "Home"
        else:
            st.error("Invalid username or password")
    if st.button("Register"):
        result = register_user(username, password, users)
        if result:
            st.error(result)
        else:
            st.success("Registration successful! You can now log in.")

def show_notifications():
    current_time = time.time()
    if current_time - st.session_state.last_notification_check > 5:
        st.session_state.last_notification_check = current_time
        user_data = users[st.session_state.user]
        if user_data["notifications"]:
            st.toast(user_data["notifications"].pop(0))
            save_users(users)

def home_page():
    st.title("Welcome to AI Movie Matchmaker")
    st.subheader("Featured Movies")
    for _, row in df.sample(5).iterrows():
        st.image(load_poster(row["Poster_Link"]), width=150)
        st.markdown(f"**{row['Series_Title']}** ({row['IMDB_Rating']}/10)")

def discover_page():
    st.title("Discover Movies")
    query = st.text_input("Search for a movie or genre")
    if query:
        results = df[df['combined_features'].str.contains(query.lower())]
        for _, row in results.iterrows():
            st.image(load_poster(row['Poster_Link']), width=150)
            st.markdown(f"**{row['Series_Title']}** ({row['IMDB_Rating']}/10)")

def watch_page():
    st.title("Continue Watching")
    user_data = users[st.session_state.user]
    for title in user_data["continue_watching"]:
        row = df[df["Series_Title"] == title].iloc[0]
        st.image(load_poster(row["Poster_Link"]), width=150)
        st.markdown(f"**{row['Series_Title']}**")

def friends_page():
    st.title("Friends")
    user_data = users[st.session_state.user]
    friend_name = st.text_input("Add Friend")
    if st.button("Add"):
        if friend_name in users and friend_name not in user_data["friends"]:
            user_data["friends"].append(friend_name)
            users[friend_name]["notifications"].append(f"{st.session_state.user} added you as a friend!")
            save_users(users)
            st.success("Friend added")
        else:
            st.error("Invalid friend")
    for friend in user_data["friends"]:
        st.subheader(friend)
        st.text_area("Chat", value="\n".join(user_data["chats"].get(friend, [])), key=friend)

def profile_page():
    st.title("Profile")
    user_data = users[st.session_state.user]
    st.markdown(f"**Level:** {user_data['level']}")
    st.markdown(f"**XP:** {user_data['xp']}")
    st.markdown(f"**Joined:** {user_data['join_date']}")
    st.subheader("Favorites")
    for title in user_data["favorites"]:
        row = df[df["Series_Title"] == title].iloc[0]
        st.image(load_poster(row["Poster_Link"]), width=150)
        st.markdown(f"**{row['Series_Title']}**")

if st.session_state.user is None:
    login_page()
else:
    st.sidebar.title(f"Hello, {st.session_state.user}!")
    st.sidebar.button("Home", on_click=lambda: st.session_state.update({"page": "Home"}))
    st.sidebar.button("Discover", on_click=lambda: st.session_state.update({"page": "Discover"}))
    st.sidebar.button("Watch", on_click=lambda: st.session_state.update({"page": "Watch"}))
    st.sidebar.button("Friends", on_click=lambda: st.session_state.update({"page": "Friends"}))
    st.sidebar.button("Profile", on_click=lambda: st.session_state.update({"page": "Profile"}))
    st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"user": None}))

    show_notifications()

    if st.session_state.page == "Home":
        home_page()
    elif st.session_state.page == "Discover":
        discover_page()
    elif st.session_state.page == "Watch":
        watch_page()
    elif st.session_state.page == "Friends":
        friends_page()
    elif st.session_state.page == "Profile":
        profile_page()

if name == "main": main()

