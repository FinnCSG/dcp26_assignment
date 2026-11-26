import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

#Part 1: Write Python code to read your CSV and insert the rows into a table in SQLITE


df = pd.read_csv("Music_Data.csv")

print("\nMUSIC DATASET CSV\n")
print(df.to_string(index=False))
print("\nTotal Albums:", len(df))

conn = sqlite3.connect("music_database.db")
cursor = conn.cursor()

#table for all csv data
cursor.execute("""
CREATE TABLE IF NOT EXISTS music (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_listened TEXT,
    initial_rating INTEGER CHECK(initial_rating BETWEEN 1 AND 10),
    current_rating INTEGER CHECK(current_rating BETWEEN 1 AND 10),
    artist TEXT,
    album TEXT,
    release_date TEXT,
    genres TEXT,
    descriptors TEXT,
    language TEXT
)
""")
#table for possible invalid data
cursor.execute("""
CREATE TABLE IF NOT EXISTS validation_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    csv_row_number INTEGER,
    issue TEXT
)
""")
#table for genres
cursor.execute("""
CREATE TABLE IF NOT EXISTS album_genres (
    album_id INTEGER,
    genre TEXT,
    FOREIGN KEY (album_id) REFERENCES music(id)
)
""")

conn.commit()


#Part 2: Clean and validate your data as you load it: check types, handle missing values, flag values that are out of range

#list for columns with thext
text_columns = [
    "Artist",
    "Album",
    "Genres",
    "Descriptors",
    "Language"
]

#remove spaces
for col in text_columns:
    df[col] = df[col].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )

#replace empty to show missing value
df = df.replace(r"^\s*$", pd.NA, regex=True)

#convert dates to be readable by pandas
df["Date Listened"] = pd.to_datetime(
    df["Date Listened"],
    format="%Y/%m/%d",
    errors="coerce"
)

df["Release Date"] = pd.to_datetime(
    df["Release Date"],
    format="%Y/%m/%d",
    errors="coerce"
)

#convert text ratings to numbers
df["Initial Rating"] = pd.to_numeric(
    df["Initial Rating"],
    errors="coerce"
)

df["Current Rating"] = pd.to_numeric(
    df["Current Rating"],
    errors="coerce"
)
#fill missing info
df["Language"] = df["Language"].fillna("Unknown")
df["Descriptors"] = df["Descriptors"].fillna("Unknown")

print("\nData cleaning completed.")



#lists for validation
valid_rows = []
errors = []
#check data validity
for index, row in df.iterrows():
#list for problems
    problems = []
#date validity
    if pd.isna(row["Date Listened"]):
        problems.append("Invalid listening date")

    if pd.isna(row["Release Date"]):
        problems.append("Invalid release date")

    if (
        pd.notna(row["Date Listened"])
        and pd.notna(row["Release Date"])
        and row["Date Listened"] < row["Release Date"]
    ):
        problems.append("Listening date before release date")
#text validity
    for col in ["Artist", "Album", "Genres"]:

        if pd.isna(row[col]):
            problems.append("Missing " + col)

#ratings validity
    for rating in ["Initial Rating", "Current Rating"]:

        value = row[rating]

        if pd.isna(value):
            problems.append("Missing or invalid " + rating)

        elif value % 1 != 0:
            problems.append(rating + " must be an integer")

        elif value < 1 or value > 10:
            problems.append(rating + " outside range 1-10")

#valid

    if len(problems) == 0:
        valid_rows.append(row)

#invalid

    else:
        for problem in problems:
            errors.append((index + 2, problem))

        print("Invalid row:", index + 2, problems)



#clear previous imported data for rerun to eliminate duplicates

cursor.execute("DELETE FROM album_genres")
cursor.execute("DELETE FROM music")
cursor.execute("DELETE FROM validation_errors")

#put errors into validation error table
cursor.executemany("""
INSERT INTO validation_errors (csv_row_number, issue)
VALUES (?, ?)
""", errors)

#put valid into main table
for row in valid_rows:

    cursor.execute("""
    INSERT INTO music (
        date_listened,
        initial_rating,
        current_rating,
        artist,
        album,
        release_date,
        genres,
        descriptors,
        language
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["Date Listened"].strftime("%Y-%m-%d"),
        int(row["Initial Rating"]),
        int(row["Current Rating"]),
        row["Artist"],
        row["Album"],
        row["Release Date"].strftime("%Y-%m-%d"),
        row["Genres"],
        row["Descriptors"],
        row["Language"]
    ))

conn.commit()

print("\n===== DATABASE SUMMARY =====")
print("Valid albums inserted:", len(valid_rows))
print("Invalid records flagged:", len(set(row[0] for row in errors)))

#allow genres to be treated as seperate
#i will separate the genres so that multiple genres on one album can be analysed individually later on
cursor.execute("SELECT id, genres FROM music")

albums = cursor.fetchall()

for album in albums:

    album_id = album[0]
    genres = album[1]

    for genre in genres.split(","):

        genre = genre.strip()
#check if empty
        if genre:

            cursor.execute("""
            INSERT INTO album_genres (album_id, genre)
            VALUES (?, ?)
            """, (album_id, genre))

conn.commit()


#check if all inserted correctly
cursor.execute("SELECT COUNT(*) FROM music")

print("\nTotal albums in database:", cursor.fetchone()[0])

cursor.execute("""
SELECT album, artist, initial_rating, current_rating
FROM music
""")

print("\nALBUMS IN DATABASE")

for row in cursor.fetchall():
    print(row)


#Part 3: Write some SQL queries that answer simple questions about your data (GROUP BY, ORDER BY, WHERE, AVG, COUNT)

#QUESTION 1: Do I have any major affinities towards year or genre?
print("\nQUESTION 1: Do I have any major affinities towards year or genre?")


#Which release years appear most frequently?

query = """
SELECT
    strftime('%Y', release_date) AS release_year,
    COUNT(*) AS album_count,
    ROUND(AVG(current_rating), 2) AS average_rating

FROM music

GROUP BY release_year
ORDER BY album_count DESC
"""

cursor.execute(query)

print("\nALBUMS BY RELEASE YEAR")

for row in cursor.fetchall():
    print(row)


# Which genres do I rate most highly?

query = """
SELECT
    album_genres.genre,
    COUNT(*) AS album_count,
    ROUND(AVG(music.current_rating), 2) AS average_rating

FROM album_genres

JOIN music
ON album_genres.album_id = music.id

GROUP BY album_genres.genre
ORDER BY average_rating DESC
"""

cursor.execute(query)

print("\nAVERAGE RATINGS BY GENRE")

for row in cursor.fetchall():
    print(row)


# QUESTION 2: Do my thoughts on albums change much after the first listen?
print("\nQUESTION 2: Do my thoughts on albums change much after the first listen?")


# average change in ratings

query = """
SELECT
    ROUND(AVG(current_rating - initial_rating), 2)

FROM music
"""

cursor.execute(query)

print("\nAVERAGE RATING CHANGE")
print(cursor.fetchone()[0])

#which albums changed the most

query = """
SELECT
    album,
    artist,
    initial_rating,
    current_rating,
    current_rating - initial_rating AS rating_change

FROM music

WHERE initial_rating <> current_rating
ORDER BY ABS(rating_change) DESC
"""

cursor.execute(query)

print("\nBIGGEST RATING CHANGES")

for row in cursor.fetchall():
    print(row)


# QUESTION 3: How likely am i to be positive or negative towards new music?
print("\nQUESTION 3: How likely am i to be positive or negative towards new music?")


#average initial rating

query = """
SELECT
    ROUND(AVG(initial_rating), 2),
    COUNT(*)

FROM music
"""

cursor.execute(query)

print("\nAVERAGE INITIAL RATING")
print(cursor.fetchone())


#positive vs negative
#6-10 = positive
#1-5 = negative

query = """
SELECT
    CASE
        WHEN initial_rating >= 6
            THEN 'Positive'

        ELSE 'Negative'

    END AS first_impression,
    COUNT(*) AS album_count

FROM music

GROUP BY first_impression
ORDER BY album_count DESC
"""

cursor.execute(query)

print("\nPOSITIVE VS NEGATIVE FIRST IMPRESSIONS")

for row in cursor.fetchall():
    print(row)


#Check errors

cursor.execute("""
SELECT csv_row_number, issue
FROM validation_errors
ORDER BY csv_row_number
""")

print("\nVALIDATION ERRORS")

for row in cursor.fetchall():
    print(row)


#Save and Close Database
conn.commit()
conn.close()

print("\nDatabase saved successfully")