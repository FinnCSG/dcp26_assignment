import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect("music_database.db")

df = pd.read_sql_query("SELECT * FROM music", conn)

genre_df = pd.read_sql_query("""
    SELECT music.album,
           music.artist,
           music.current_rating,
           music.initial_rating,
           album_genres.genre
    FROM music
    JOIN album_genres
    ON music.id = album_genres.album_id
""", conn)

conn.close()

#convert date to datetime
df["date_listened"] = pd.to_datetime(df["date_listened"])
df["release_date"] = pd.to_datetime(df["release_date"])

#new column to show difference in ratings
df["rating_change"] = (
    df["current_rating"] - df["initial_rating"]
)

#seperate release year
df["release_year"] = df["release_date"].dt.year

print("\nDATA LOADED SUCCESSFULLY")
print("Total albums:", len(df))


#functions to analyse the data

#function 1: Analyse overall ratings

def analyse_ratings(data):

    print("\nOVERALL RATINGS")

    print("Average initial rating:",
          round(data["initial_rating"].mean(), 2))

    print("Average current rating:",
          round(data["current_rating"].mean(), 2))

    print("Average rating change:",
          round(data["rating_change"].mean(), 2))

    print("\nRating changes:")

    print("Improved:",
          (data["rating_change"] > 0).sum())

    print("Stayed the same:",
          (data["rating_change"] == 0).sum())

    print("Decreased:",
          (data["rating_change"] < 0).sum())


#function 2: Analyse genre preferences

def analyse_genres(data):

    print("\nGENRE ANALYSIS")
    genre_results = data.groupby("genre").agg(
        album_count=("album", "count"),
        average_rating=("current_rating", "mean")
    ).sort_values(
        "average_rating", ascending=False
    )

    genre_results["average_rating"] = (
        genre_results["average_rating"].round(2)
    )

    print(genre_results)
    return genre_results


#function 3: Analyse release years

def analyse_years(data):

    print("\nRELEASE YEAR ANALYSIS")

    year_results = data.groupby("release_year").agg(
        album_count=("album", "count"),
        average_rating=("current_rating", "mean")
    ).sort_values(
        "album_count", ascending=False
    )

    year_results["average_rating"] = (
        year_results["average_rating"].round(2)
    )

    print(year_results)

    return year_results

#function 4: Analyse first impressions

def analyse_first_impressions(data):

    print("\nFIRST IMPRESSIONS")

    positive = (data["initial_rating"] >= 6).sum()
    negative = (data["initial_rating"] <= 5).sum()

    total = len(data)

    print("Positive first impressions:",
          positive,
          f"({positive / total * 100:.1f}%)")

    print("Negative first impressions:",
          negative,
          f"({negative / total * 100:.1f}%)")


# Run all analysis functions

analyse_ratings(df)

genre_results = analyse_genres(genre_df)

year_results = analyse_years(df)

analyse_first_impressions(df)


#matplotlib to make charts

#CHART 1: RATINGS OVER TIME

def plot_ratings_over_time(data):

    data = data.sort_values("date_listened")

    plt.figure(figsize=(11, 5))
#initial
    plt.plot(
        data["date_listened"],
        data["initial_rating"],
        marker="o",
        label="Initial Rating"
    )
#curent
    plt.plot(
        data["date_listened"],
        data["current_rating"],
        marker="o",
        label="Current Rating"
    )

    plt.title("Album Ratings Over Time")
    plt.xlabel("Date Listened")
    plt.ylabel("Rating out of 10")

    plt.ylim(0, 11)
    plt.xticks(rotation=45)

    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("ratings_over_time.png")
    plt.show()


#CHART 2: AVERAGE RATINGS BY GENRE

def plot_genre_ratings(data):

    results = data.groupby("genre").agg(
        album_count=("album", "count"),
        average_rating=("current_rating", "mean")
    )
# Only genres appearing at least twice
    results = results[results["album_count"] >= 2]

    results = results.sort_values("average_rating")

    plt.figure(figsize=(10, 6))
#barchart
    plt.barh(
        results.index,
        results["average_rating"]
    )

    plt.title("Average Album Rating by Genre")
    plt.xlabel("Average Current Rating")
    plt.ylabel("Genre")

    plt.xlim(0, 10)
    #vertical gridlines
    plt.grid(axis="x")

    plt.tight_layout()
    plt.savefig("genre_ratings.png")
    plt.show()


#CHART 3: DISTRIBUTION OF RATINGS

def plot_rating_distribution(data):

    plt.figure(figsize=(9, 5))

    plt.hist(
        data["current_rating"],
        bins=range(1, 12),
        edgecolor="black"
    )

    plt.title("Distribution of Current Album Ratings")
    plt.xlabel("Current Rating")
    plt.ylabel("Number of Albums")

    plt.xticks(range(1, 11))
    plt.grid(axis="y")

    plt.tight_layout()
    plt.savefig("rating_distribution.png")
    plt.show()


#CHART 4: INITIAL VS CURRENT RATINGS

def plot_rating_comparison(data):

    plt.figure(figsize=(8, 6))

    plt.scatter(
        data["initial_rating"],
        data["current_rating"]
    )

    # Reference line for albums with unchanged ratings
    plt.plot(
        [1, 10],
        [1, 10],
        linestyle="--",
        label="No Rating Change"
    )

    plt.title("Initial Ratings Compared to Current Ratings")
    plt.xlabel("Initial Rating")
    plt.ylabel("Current Rating")

    plt.xticks(range(1, 11))
    plt.yticks(range(1, 11))

    plt.xlim(1, 11)
    plt.ylim(1, 11)

    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("rating_comparison.png")
    plt.show()


#all charts

plot_ratings_over_time(df)

plot_genre_ratings(genre_df)

plot_rating_distribution(df)

plot_rating_comparison(df)

print("\nAll analysis and charts completed")