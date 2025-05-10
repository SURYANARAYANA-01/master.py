import streamlit as st
from datetime import datetime
import json
import os
import bcrypt

# Load or initialize data
def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

users = load_data("users.json")
movies = load_data("movies.json")
chats = load_data("chats.json")

# Sample movie database
sample_movies = [
    {"id": 1, "title": "Inception", "genre": "Sci-Fi", "featured": True},
    {"id": 2, "title": "Interstellar", "genre": "Sci-Fi", "featured": True},
    {"id": 3, "title": "The Godfather", "genre": "Crime", "featured": False},
]

if not movies:
    movies = {str(movie['id']): movie for movie in sample_movies}
    save_data("movies.json", movies)

# Auth system
def login():
    st.title("AI Movie Matchmaking Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if not username or not password:
            st.warning("Username and password required.")
        elif username in users and bcrypt.checkpw(password.encode(), users[username]["password"].encode()):
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Invalid login.")

    if st.button("Register"):
        if not username or not password:
            st.warning("Username and password required.")
        elif username in users:
            st.error("Username already taken.")
        else:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            users[username] = {
                "password": hashed_pw,
                "favorites": [],
                "ratings": {},
                "friends": [],
                "watching": [],
                "level": 1
            }
            save_data("users.json", users)
            st.success("Account created. Please log in.")

# Movie interaction functions
def rate_movie(user, movie_id, rating):
    users[user]["ratings"][movie_id] = rating
    users[user]["level"] += 1
    save_data("users.json", users)

def mark_favorite(user, movie_id):
    if movie_id not in users[user]["favorites"]:
        users[user]["favorites"].append(movie_id)
        save_data("users.json", users)

def add_to_continue_watching(user, movie_id):
    if movie_id not in users[user]["watching"]:
        users[user]["watching"].append(movie_id)
        save_data("users.json", users)

# Chat system
def send_message(sender, receiver, text):
    chat_id = "_".join(sorted([sender, receiver]))
    if chat_id not in chats:
        chats[chat_id] = []
    chats[chat_id].append({
        "from": sender,
        "to": receiver,
        "msg": text,
        "time": str(datetime.now())
    })
    save_data("chats.json", chats)

# Main app
if "user" not in st.session_state:
    login()
else:
    user = st.session_state.user
    st.sidebar.title(f"Welcome, {user}!")
    page = st.sidebar.selectbox("Navigate", ["Home", "Search", "Friends", "Favorites", "Continue Watching", "Logout"])
    st.sidebar.markdown(f"**Level:** {users[user]['level']}")

    if page == "Logout":
        del st.session_state.user
        st.rerun()

    elif page == "Home":
        st.title("Featured Movies")
        for movie in movies.values():
            if movie["featured"]:
                with st.expander(movie["title"]):
                    rating = st.slider("Rate", 1, 10, key=f"slider_{movie['id']}")
                    if st.button("Submit Rating", key=f"rate_{movie['id']}"):
                        rate_movie(user, str(movie["id"]), rating)
                        st.success(f"Rated {rating}/10")

                    if st.button("Favorite", key=f"fav_{movie['id']}"):
                        mark_favorite(user, str(movie["id"]))
                        st.success("Marked as favorite")

                    if st.button("Watch", key=f"watch_{movie['id']}"):
                        add_to_continue_watching(user, str(movie["id"]))
                        st.success("Added to continue watching")

    elif page == "Search":
        query = st.text_input("Search for movies")
        if query:
            results = [m for m in movies.values() if query.lower() in m["title"].lower()]
            for movie in results:
                with st.expander(movie["title"]):
                    st.write(f"Genre: {movie['genre']}")
                    if st.button("Watch", key=f"search_watch_{movie['id']}"):
                        add_to_continue_watching(user, str(movie["id"]))
                        st.success("Added to continue watching")

    elif page == "Favorites":
        st.title("Your Favorite Movies")
        for movie_id in users[user]["favorites"]:
            movie = movies.get(str(movie_id))
            if movie:
                st.subheader(movie["title"])

    elif page == "Continue Watching":
        st.title("Continue Watching")
        for movie_id in users[user]["watching"]:
            movie = movies.get(str(movie_id))
            if movie:
                st.subheader(movie["title"])
                if st.button(f"Finished {movie['title']}", key=f"finish_{movie['id']}"):
                    users[user]["watching"].remove(movie_id)
                    save_data("users.json", users)
                    st.success("Marked as watched")

    elif page == "Friends":
        st.title("Friends & Chat")
        st.subheader("Add a Friend")
        friend = st.text_input("Friend's Username")
        if st.button("Add Friend"):
            if friend in users and friend != user and friend not in users[user]["friends"]:
                users[user]["friends"].append(friend)
                save_data("users.json", users)
                st.success(f"Added {friend} as friend")
            else:
                st.warning("Cannot add user.")

        st.subheader("Chat")
        if users[user]["friends"]:
            selected_friend = st.selectbox("Select Friend to Chat", users[user]["friends"])
            chat_id = "_".join(sorted([user, selected_friend]))
            if chat_id in chats:
                st.write("### Chat History")
                for msg in chats[chat_id]:
                    st.markdown(f"**{msg['from']}**: {msg['msg']}  \n<small>{msg['time']}</small>", unsafe_allow_html=True)

            msg = st.text_input("Type message")
            if st.button("Send Message"):
                if msg.strip():
                    send_message(user, selected_friend, msg)
                    st.rerun()
