import praw

reddit = praw.Reddit(
    client_id="DyYF4Ef-Lv9CTOcAK-4Z_g",  # your actual ID
    client_secret=None,  # use None, not ""
    redirect_uri="http://localhost:8080",  # must match exactly what's in Reddit dev dashboard
    user_agent="goatland-weirdnews-script by /u/therealbrandolorian"
)

auth_url = reddit.auth.url(
    scopes=["identity", "read"],
    state="random_state_string",  # can be anything
    duration="permanent"
)

print("Visit this URL and authorize the app:")
print(auth_url)
