"""
seed.py — MovieTracker Database Seeder
=======================================
Populates the `movies` table with 100 well-known, real movies.

Usage (run from the backend/ directory):
    python seed.py

Features:
- Idempotent: skips movies that already exist (by title).
- Commits once after all inserts (rolls back on any failure).
- Prints a clear summary at the end.
- Uses the existing SQLAlchemy `Movie` model and `db` session — no schema changes.
"""

import random
import sys
from datetime import datetime, timedelta

from app import create_app
from database import db
from models.movie import Movie

# ---------------------------------------------------------------------------
# Movie Dataset
# Each entry maps directly to Movie model fields.
# Poster URLs: TMDB image CDN (https://image.tmdb.org/t/p/w500/<path>)
# ---------------------------------------------------------------------------

MOVIES = [
    # ── Action ──────────────────────────────────────────────────────────────
    {
        "title": "The Dark Knight",
        "description": (
            "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, "
            "Batman must accept one of the greatest psychological and physical tests of his ability "
            "to fight injustice. A masterpiece of modern superhero cinema."
        ),
        "genre": "Action",
        "release_year": 2008,
        "duration": 152,
        "rating": 9.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "status": "Completed",
    },
    {
        "title": "Inception",
        "description": (
            "A thief who steals corporate secrets through the use of dream-sharing technology "
            "is given the inverse task of planting an idea into the mind of a C.E.O. "
            "Christopher Nolan's mind-bending sci-fi thriller redefined blockbuster filmmaking."
        ),
        "genre": "Sci-Fi",
        "release_year": 2010,
        "duration": 148,
        "rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        "status": "Completed",
    },
    {
        "title": "Interstellar",
        "description": (
            "A team of explorers travel through a wormhole in space in an attempt to ensure "
            "humanity's survival. Blending hard science with deep human emotion, it stands as "
            "one of the most ambitious films of the 21st century."
        ),
        "genre": "Sci-Fi",
        "release_year": 2014,
        "duration": 169,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "status": "Completed",
    },
    {
        "title": "Mad Max: Fury Road",
        "description": (
            "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler "
            "in search of her homeland with the aid of a group of female prisoners, a psychotic "
            "worshiper, and a drifter named Max. A relentless, visually stunning action spectacle."
        ),
        "genre": "Action",
        "release_year": 2015,
        "duration": 120,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg",
        "status": "Completed",
    },
    {
        "title": "John Wick",
        "description": (
            "An ex-hitman comes out of retirement to track down the gangsters that killed "
            "his dog, a final gift from his recently deceased wife. The film reinvented the "
            "action genre with its hyper-choreographed combat sequences."
        ),
        "genre": "Action",
        "release_year": 2014,
        "duration": 101,
        "rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/fZPSd91yGE9fCcCe6OoQr6E3Bev.jpg",
        "status": "Completed",
    },
    {
        "title": "Top Gun: Maverick",
        "description": (
            "After more than thirty years of service as one of the Navy's top aviators, "
            "Pete Mitchell is where he belongs, pushing the envelope as a courageous test pilot. "
            "A triumphant sequel that surpassed every expectation."
        ),
        "genre": "Action",
        "release_year": 2022,
        "duration": 130,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/62HCnUTziyWcpDaBO2i1DX17ljH.jpg",
        "status": "Completed",
    },
    {
        "title": "Mission: Impossible - Fallout",
        "description": (
            "Ethan Hunt and his IMF team, along with some familiar allies, race against time "
            "after a mission gone wrong. Tom Cruise's death-defying stunts make this the pinnacle "
            "of the franchise."
        ),
        "genre": "Action",
        "release_year": 2018,
        "duration": 147,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/AkJQpZp9WoNdj7pLYSj1L0RcMMN.jpg",
        "status": "Completed",
    },
    {
        "title": "Gladiator",
        "description": (
            "A former Roman General sets out to exact vengeance against the corrupt emperor "
            "who murdered his family and sent him into slavery. Russell Crowe delivers a towering "
            "performance in Ridley Scott's epic."
        ),
        "genre": "Action",
        "release_year": 2000,
        "duration": 155,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/ehGpAnd60Ou7Dj0kRAx4gVkiPCr.jpg",
        "status": "Completed",
    },
    {
        "title": "The Batman",
        "description": (
            "When the Riddler, a sadistic serial killer, begins murdering key political figures "
            "in Gotham, Batman is forced to investigate the city's hidden corruption. "
            "A neo-noir take on the Caped Crusader unlike anything seen before."
        ),
        "genre": "Action",
        "release_year": 2022,
        "duration": 176,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
        "status": "Watching",
    },
    {
        "title": "Kill Bill: Volume 1",
        "description": (
            "After awakening from a four-year coma, a woman sets out to exact revenge on the "
            "people who tried to kill her. Tarantino's stylish homage to martial arts cinema "
            "is a masterclass in choreography and composition."
        ),
        "genre": "Action",
        "release_year": 2003,
        "duration": 111,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/v7TaX8kXMXs5yFFGR41guUDNcnB.jpg",
        "status": "Completed",
    },
    # ── Crime / Thriller ─────────────────────────────────────────────────────
    {
        "title": "The Godfather",
        "description": (
            "The aging patriarch of an organized crime dynasty transfers control of his "
            "clandestine empire to his reluctant son. Francis Ford Coppola's masterpiece "
            "remains the definitive portrait of American organized crime."
        ),
        "genre": "Crime",
        "release_year": 1972,
        "duration": 175,
        "rating": 9.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsLe1rDtrmBfA.jpg",
        "status": "Completed",
    },
    {
        "title": "Pulp Fiction",
        "description": (
            "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of "
            "diner bandits intertwine in four tales of violence and redemption. "
            "Quentin Tarantino's non-linear narrative redefined independent cinema."
        ),
        "genre": "Crime",
        "release_year": 1994,
        "duration": 154,
        "rating": 8.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
        "status": "Completed",
    },
    {
        "title": "Fight Club",
        "description": (
            "An insomniac office worker and a devil-may-care soapmaker form an underground "
            "fight club that evolves into something much more sinister. "
            "David Fincher's provocative thriller features one of cinema's great twist endings."
        ),
        "genre": "Thriller",
        "release_year": 1999,
        "duration": 139,
        "rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "status": "Completed",
    },
    {
        "title": "Parasite",
        "description": (
            "Greed and class discrimination threaten the newly formed symbiotic relationship "
            "between the wealthy Park family and the destitute Kim clan. "
            "Bong Joon-ho's Oscar-winning thriller is a searing social satire."
        ),
        "genre": "Thriller",
        "release_year": 2019,
        "duration": 132,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "status": "Completed",
    },
    {
        "title": "Joker",
        "description": (
            "In Gotham City, mentally troubled comedian Arthur Fleck is disregarded and mistreated "
            "by society and begins a slow descent into insanity, becoming the criminal mastermind "
            "known as the Joker. Joaquin Phoenix delivers a career-defining performance."
        ),
        "genre": "Crime",
        "release_year": 2019,
        "duration": 122,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/udDclJoHjfjb8Ekgsd4FDteOkCU.jpg",
        "status": "Completed",
    },
    {
        "title": "The Silence of the Lambs",
        "description": (
            "A young FBI cadet must receive the help of an incarcerated and manipulative "
            "cannibal killer to help catch another serial killer. "
            "Jonathan Demme's psychological thriller swept the Academy Awards."
        ),
        "genre": "Thriller",
        "release_year": 1991,
        "duration": 118,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/rplLJ2hPcOQmkFhTqUte0MkEaO2.jpg",
        "status": "Completed",
    },
    {
        "title": "Gone Girl",
        "description": (
            "With his wife's disappearance having become the focus of an intense media circus, "
            "a man sees the spotlight turned on him when it's suspected that he may not be "
            "innocent. A chilling examination of marriage and media obsession."
        ),
        "genre": "Thriller",
        "release_year": 2014,
        "duration": 149,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/umu84bUhmqm5mHDOZBSrEBbFWAq.jpg",
        "status": "Completed",
    },
    {
        "title": "Se7en",
        "description": (
            "Two detectives, a rookie and a veteran, hunt a serial killer who uses the seven "
            "deadly sins as his modus operandi. David Fincher's dark thriller builds to one "
            "of the most shocking finales in cinema history."
        ),
        "genre": "Crime",
        "release_year": 1995,
        "duration": 127,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/6yoghtyTpznpBik8EngEmJskVUO.jpg",
        "status": "Completed",
    },
    {
        "title": "No Country for Old Men",
        "description": (
            "Violence and mayhem ensue after a hunter stumbles upon a drug deal gone wrong "
            "and finds two million dollars. The Coen Brothers' pursuit thriller is a meditation "
            "on fate, morality, and the nature of evil."
        ),
        "genre": "Crime",
        "release_year": 2007,
        "duration": 122,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/6d5XOaczqjTtcSVFB5CVxBFTvEw.jpg",
        "status": "Completed",
    },
    {
        "title": "Knives Out",
        "description": (
            "A detective investigates the death of a patriarch of an eccentric, combative family. "
            "Rian Johnson's whodunit is a cleverly constructed, endlessly entertaining mystery "
            "with a stellar ensemble cast."
        ),
        "genre": "Mystery",
        "release_year": 2019,
        "duration": 130,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/pThyQovXQrws2wmHL7zF9eDyrIT.jpg",
        "status": "Completed",
    },
    # ── Drama ─────────────────────────────────────────────────────────────────
    {
        "title": "The Shawshank Redemption",
        "description": (
            "Two imprisoned men bond over a number of years, finding solace and eventual "
            "redemption through acts of common decency. Consistently ranked the greatest film "
            "ever made by IMDb users worldwide."
        ),
        "genre": "Drama",
        "release_year": 1994,
        "duration": 142,
        "rating": 9.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bAY5trNydOMnCGjx.jpg",
        "status": "Completed",
    },
    {
        "title": "Whiplash",
        "description": (
            "A promising young drummer enrolls at a cut-throat music conservatory where his "
            "drive to succeed is matched by the cruelty of his teacher. "
            "Damien Chazelle's electrifying debut is a film about obsession and greatness."
        ),
        "genre": "Drama",
        "release_year": 2014,
        "duration": 107,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/7fn624j5lj3xTme2SgiLCeuedmO.jpg",
        "status": "Completed",
    },
    {
        "title": "The Social Network",
        "description": (
            "The story of the founding of the social-networking website Facebook and the "
            "resulting lawsuits. David Fincher and Aaron Sorkin's collaboration produced "
            "one of the defining films of the digital age."
        ),
        "genre": "Drama",
        "release_year": 2010,
        "duration": 120,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
        "status": "Completed",
    },
    {
        "title": "The Green Mile",
        "description": (
            "The lives of guards on Death Row are affected by one of their charges: "
            "a massive, yet gentle man with a mysterious gift. Frank Darabont's adaptation "
            "of Stephen King's novel is a profound exploration of justice and compassion."
        ),
        "genre": "Drama",
        "release_year": 1999,
        "duration": 189,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/sOHqdY1RnSn6QLfFJuaQy1cvnkH.jpg",
        "status": "Completed",
    },
    {
        "title": "Forrest Gump",
        "description": (
            "The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate and "
            "other historical events unfold through the perspective of an Alabama man with "
            "an IQ of 75. A touching, humorous, and uniquely American epic."
        ),
        "genre": "Drama",
        "release_year": 1994,
        "duration": 142,
        "rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
        "status": "Completed",
    },
    {
        "title": "A Beautiful Mind",
        "description": (
            "After a brilliant but asocial mathematician accepts secret work in cryptography, "
            "his life takes a turn for the chaotic. Ron Howard's biopic of John Nash earned "
            "four Academy Awards including Best Picture."
        ),
        "genre": "Drama",
        "release_year": 2001,
        "duration": 135,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/2WXopnEMqFBg5b59fKY8DynJfqZ.jpg",
        "status": "Completed",
    },
    {
        "title": "Oppenheimer",
        "description": (
            "The story of American scientist J. Robert Oppenheimer and his role in the "
            "development of the atomic bomb during World War II. Christopher Nolan's magnum "
            "opus is a stunning meditation on genius, ethics, and consequence."
        ),
        "genre": "History",
        "release_year": 2023,
        "duration": 181,
        "rating": 8.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "status": "Completed",
    },
    {
        "title": "12 Angry Men",
        "description": (
            "A jury holdout attempts to prevent a miscarriage of justice by forcing his "
            "colleagues to reconsider the evidence. Sidney Lumet's chamber drama remains "
            "the most compelling courtroom film ever committed to celluloid."
        ),
        "genre": "Drama",
        "release_year": 1957,
        "duration": 96,
        "rating": 9.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/qqHQsStV6exghCM7zbObuYBiYxw.jpg",
        "status": "Completed",
    },
    {
        "title": "Good Will Hunting",
        "description": (
            "Will Hunting, a janitor at MIT, has a gift for mathematics but needs help from "
            "a psychologist to find his direction in life. Matt Damon and Ben Affleck's Oscar-"
            "winning script launched two legendary careers."
        ),
        "genre": "Drama",
        "release_year": 1997,
        "duration": 126,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/bABCBKYBK7A5G0RFvhRg3GgIkx.jpg",
        "status": "Completed",
    },
    {
        "title": "Everything Everywhere All at Once",
        "description": (
            "An aging Chinese immigrant is swept up in an insane adventure in which she alone "
            "can save existence by exploring other universes and connecting with the lives she "
            "could have led. The Daniels' multiverse masterpiece swept the 2023 Academy Awards."
        ),
        "genre": "Sci-Fi",
        "release_year": 2022,
        "duration": 139,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg",
        "status": "Completed",
    },
    # ── Sci-Fi ────────────────────────────────────────────────────────────────
    {
        "title": "The Matrix",
        "description": (
            "A computer hacker learns from mysterious rebels about the true nature of his "
            "reality and his role in the war against its controllers. The Wachowskis' "
            "groundbreaking film redefined visual effects and science fiction cinema."
        ),
        "genre": "Sci-Fi",
        "release_year": 1999,
        "duration": 136,
        "rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "status": "Completed",
    },
    {
        "title": "Dune",
        "description": (
            "Feature adaptation of Frank Herbert's science fiction novel about the son of "
            "a noble family entrusted with the protection of the most valuable asset in the galaxy. "
            "Denis Villeneuve crafts an awe-inspiring epic of staggering scale."
        ),
        "genre": "Sci-Fi",
        "release_year": 2021,
        "duration": 155,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/d5NXSklXo0qyIYkgV94XAgMIckC.jpg",
        "status": "Completed",
    },
    {
        "title": "Dune: Part Two",
        "description": (
            "Paul Atreides unites with Chani and the Fremen while seeking revenge against "
            "the conspirators who destroyed his family. Villeneuve's sequel is even more "
            "ambitious and emotionally resonant than its predecessor."
        ),
        "genre": "Sci-Fi",
        "release_year": 2024,
        "duration": 167,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "status": "Watching",
    },
    {
        "title": "Blade Runner 2049",
        "description": (
            "A young blade runner's discovery of a long-buried secret leads him to track down "
            "former blade runner Rick Deckard, who's been missing for thirty years. "
            "Denis Villeneuve's meditative sequel is a visual poem."
        ),
        "genre": "Sci-Fi",
        "release_year": 2017,
        "duration": 163,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg",
        "status": "Completed",
    },
    {
        "title": "Avatar",
        "description": (
            "A paraplegic marine dispatched to the moon Pandora on a unique mission becomes "
            "torn between following his orders and protecting the world he feels is his home. "
            "James Cameron's visual revolution grossed the most money in cinema history."
        ),
        "genre": "Sci-Fi",
        "release_year": 2009,
        "duration": 162,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/jRXYjXNq0Cs2TcJjLkki24MLp7u.jpg",
        "status": "Completed",
    },
    {
        "title": "Arrival",
        "description": (
            "A linguist works with the military to communicate with alien lifeforms after "
            "twelve mysterious spacecraft appear around the world. Denis Villeneuve's profound "
            "science fiction film reframes the nature of time and language."
        ),
        "genre": "Sci-Fi",
        "release_year": 2016,
        "duration": 116,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/x2FJsf1ElAgr63Y3PNPtJrcmpoe.jpg",
        "status": "Completed",
    },
    {
        "title": "Ex Machina",
        "description": (
            "A young programmer is selected to participate in a ground-breaking experiment "
            "in synthetic intelligence by evaluating the human qualities of a highly advanced "
            "female A.I. A chilling, intimate exploration of consciousness and control."
        ),
        "genre": "Sci-Fi",
        "release_year": 2014,
        "duration": 108,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/btBEBHSaMW1yJKqkPBN8Bqt5O5i.jpg",
        "status": "Completed",
    },
    {
        "title": "The Martian",
        "description": (
            "An astronaut becomes stranded on Mars after his team assume him dead, and must "
            "rely on his ingenuity to find a way to signal that he is alive. "
            "Ridley Scott's optimistic survival thriller is a celebration of human problem-solving."
        ),
        "genre": "Sci-Fi",
        "release_year": 2015,
        "duration": 144,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/5aGhaIHYuQbqlHWvWYqMCnj40y2.jpg",
        "status": "Completed",
    },
    # ── Fantasy / Adventure ──────────────────────────────────────────────────
    {
        "title": "The Lord of the Rings: The Fellowship of the Ring",
        "description": (
            "A meek Hobbit from the Shire and eight companions set out on a journey to destroy "
            "the powerful One Ring and save Middle-earth from the Dark Lord Sauron. "
            "Peter Jackson's masterpiece redefined the fantasy epic."
        ),
        "genre": "Fantasy",
        "release_year": 2001,
        "duration": 178,
        "rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg",
        "status": "Completed",
    },
    {
        "title": "The Lord of the Rings: The Return of the King",
        "description": (
            "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze "
            "from Frodo and Sam as they approach Mount Doom with the One Ring. "
            "The crowning achievement of Peter Jackson's trilogy swept eleven Academy Awards."
        ),
        "genre": "Fantasy",
        "release_year": 2003,
        "duration": 201,
        "rating": 9.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
        "status": "Completed",
    },
    {
        "title": "The Prestige",
        "description": (
            "After a tragic accident, two stage magicians engage in a battle to create the "
            "ultimate illusion while sacrificing everything they have to outwit each other. "
            "Nolan's intricate puzzle of a film is best experienced knowing nothing in advance."
        ),
        "genre": "Mystery",
        "release_year": 2006,
        "duration": 130,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/tRNlZbgNCNOpLpbPEz5L8G8A0MV.jpg",
        "status": "Completed",
    },
    {
        "title": "Pirates of the Caribbean: The Curse of the Black Pearl",
        "description": (
            "Blacksmith Will Turner teams up with eccentric pirate Jack Sparrow to rescue his "
            "love, the governor's daughter, from Jack's former pirate allies. "
            "Johnny Depp's iconic portrayal of Sparrow launched a beloved franchise."
        ),
        "genre": "Adventure",
        "release_year": 2003,
        "duration": 143,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/z8onk7LV9Mmw6zKz4hT6pzzvmvl.jpg",
        "status": "Completed",
    },
    {
        "title": "Indiana Jones and the Raiders of the Lost Ark",
        "description": (
            "In 1936, archaeologist and adventurer Indiana Jones is hired by the U.S. government "
            "to find the Ark of the Covenant before the Nazis can obtain its awesome powers. "
            "Spielberg and Lucas created the definitive adventure hero."
        ),
        "genre": "Adventure",
        "release_year": 1981,
        "duration": 115,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/ceG9VzoRAVGwivFU403Wc3AHRys.jpg",
        "status": "Completed",
    },
    {
        "title": "Avatar: The Way of Water",
        "description": (
            "Jake Sully lives with his newfound family formed on the planet of Pandora. "
            "When a familiar threat returns to finish what was previously started, Jake must "
            "work with Neytiri and the army of the Na'vi race to protect their planet."
        ),
        "genre": "Adventure",
        "release_year": 2022,
        "duration": 192,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg",
        "status": "Watching",
    },
    # ── War / History ─────────────────────────────────────────────────────────
    {
        "title": "Saving Private Ryan",
        "description": (
            "Following the Normandy Landings, a group of U.S. soldiers go behind enemy lines "
            "to retrieve a paratrooper whose brothers have been killed in action. "
            "Spielberg's harrowing opening sequence is the most realistic depiction of warfare ever filmed."
        ),
        "genre": "War",
        "release_year": 1998,
        "duration": 169,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/uqx37oQM6khSa8Iga86fDpljkAK.jpg",
        "status": "Completed",
    },
    {
        "title": "Dunkirk",
        "description": (
            "Allied soldiers from Belgium, the British Commonwealth and France are surrounded "
            "by the German Army and evacuated during a fierce battle in World War II. "
            "Nolan's non-linear war film is a visceral, immersive experience."
        ),
        "genre": "War",
        "release_year": 2017,
        "duration": 106,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/ebSnODDg9lbsMIaWg2uAbjn7TO5.jpg",
        "status": "Completed",
    },
    {
        "title": "1917",
        "description": (
            "Two British soldiers are given an impossible mission: deliver a message deep in "
            "enemy territory that will stop 1,600 men, and one of the soldier's brothers, "
            "walking straight into a deadly trap. Sam Mendes' continuous-shot war film is a technical marvel."
        ),
        "genre": "War",
        "release_year": 2019,
        "duration": 119,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/iZf0KyrE25z1sage4SYQLAjQcEx.jpg",
        "status": "Completed",
    },
    {
        "title": "Schindler's List",
        "description": (
            "In German-occupied Poland during World War II, industrialist Oskar Schindler "
            "gradually becomes concerned for his Jewish workforce after witnessing their "
            "persecution by the Nazis. Spielberg's most personal film is an unflinching monument to the Holocaust."
        ),
        "genre": "History",
        "release_year": 1993,
        "duration": 195,
        "rating": 9.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
        "status": "Completed",
    },
    {
        "title": "Hacksaw Ridge",
        "description": (
            "WWII American Army Medic Desmond T. Doss, who served during the Battle of Okinawa, "
            "refuses to kill people and becomes the first man in American history to receive "
            "the Medal of Honor without firing a shot. Mel Gibson's faith-driven war epic is genuinely stirring."
        ),
        "genre": "War",
        "release_year": 2016,
        "duration": 139,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/ggpCfnAbBxGXuNH7MdWiNkQoNqM.jpg",
        "status": "Completed",
    },
    # ── Horror ────────────────────────────────────────────────────────────────
    {
        "title": "Get Out",
        "description": (
            "A young African-American visits his white girlfriend's parents for the weekend, "
            "where his uneasiness about their reception of him proves justified. "
            "Jordan Peele's debut is a politically charged social horror masterpiece."
        ),
        "genre": "Horror",
        "release_year": 2017,
        "duration": 104,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/tFXcEccSQMf3lfhfXKSU9iRBpa3.jpg",
        "status": "Completed",
    },
    {
        "title": "Hereditary",
        "description": (
            "When the matriarch of the Graham family passes away, her daughter's family begins "
            "to unravel cryptic and increasingly terrifying secrets about their ancestry. "
            "Ari Aster's debut remains one of the most frightening films of the modern era."
        ),
        "genre": "Horror",
        "release_year": 2018,
        "duration": 127,
        "rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/miBp02Gj5eMHiZYiWiKPrZspGPe.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Midsommar",
        "description": (
            "A couple travels to Sweden to visit a rural hometown's fabled mid-summer festival, "
            "but what begins as an idyllic retreat quickly devolves into an increasingly violent "
            "and bizarre competition. Ari Aster's folk horror is as beautiful as it is horrifying."
        ),
        "genre": "Horror",
        "release_year": 2019,
        "duration": 148,
        "rating": 7.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/7LEI8ulZzO5gy9Ww2NVCrKmHeDZ.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "A Quiet Place",
        "description": (
            "In a post-apocalyptic world, a family is forced to live in near silence while "
            "hiding from creatures that hunt by sound. John Krasinski's minimalist horror is "
            "an exercise in sustained tension."
        ),
        "genre": "Horror",
        "release_year": 2018,
        "duration": 90,
        "rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/nAU74GmpUk7t5iklEp3bufwDq4n.jpg",
        "status": "Completed",
    },
    {
        "title": "The Conjuring",
        "description": (
            "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized "
            "by a dark presence in their farmhouse. James Wan's atmospheric supernatural horror "
            "is one of the most effective haunted house films ever made."
        ),
        "genre": "Horror",
        "release_year": 2013,
        "duration": 112,
        "rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/wVYREutTvI2tmxr6ujrHT704wGF.jpg",
        "status": "Completed",
    },
    # ── Comedy ────────────────────────────────────────────────────────────────
    {
        "title": "The Grand Budapest Hotel",
        "description": (
            "A writer encounters the owner of an ageing European hotel between the wars and "
            "learns of the adventures of the hotel's legendary concierge. "
            "Wes Anderson's most beloved film is a perfectly crafted confection of wit and whimsy."
        ),
        "genre": "Comedy",
        "release_year": 2014,
        "duration": 99,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/eWdyYQreja6JGCzqHWXpWHDrrPo.jpg",
        "status": "Completed",
    },
    {
        "title": "Superbad",
        "description": (
            "Two co-dependent high school seniors are forced to deal with separation anxiety "
            "after their plan to score alcohol for a party goes awry. "
            "Greg Mottola's comedy is a warm, hilarious ode to the awkward agony of adolescence."
        ),
        "genre": "Comedy",
        "release_year": 2007,
        "duration": 113,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/ek8e8txUyUwd2BNqj6lFEeQtJlA.jpg",
        "status": "Completed",
    },
    {
        "title": "The Truman Show",
        "description": (
            "An insurance salesman discovers his whole life is actually a reality TV show. "
            "Peter Weir's prescient satire was decades ahead of its time and features one of "
            "Jim Carrey's finest dramatic performances."
        ),
        "genre": "Comedy",
        "release_year": 1998,
        "duration": 103,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/vuza0WqY239yBXOadKlGwJsZJFE.jpg",
        "status": "Completed",
    },
    # ── Romance ───────────────────────────────────────────────────────────────
    {
        "title": "Titanic",
        "description": (
            "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard "
            "the ill-fated R.M.S. Titanic. James Cameron's epic romance became the highest-"
            "grossing film of all time upon release and won eleven Academy Awards."
        ),
        "genre": "Romance",
        "release_year": 1997,
        "duration": 194,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/9xjZS2rlVxm8SFx8kPC3aIGCOYQ.jpg",
        "status": "Completed",
    },
    {
        "title": "La La Land",
        "description": (
            "While navigating their careers in Los Angeles, a pianist and an aspiring actress "
            "fall in love while attempting to reconcile their aspirations for the future. "
            "Damien Chazelle's musical love letter to Hollywood won six Academy Awards."
        ),
        "genre": "Romance",
        "release_year": 2016,
        "duration": 128,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg",
        "status": "Completed",
    },
    {
        "title": "(500) Days of Summer",
        "description": (
            "An offbeat romantic comedy about a woman who doesn't believe true love exists "
            "and the young man who falls for her. Marc Webb's non-linear narrative is a "
            "genuinely fresh take on the modern romantic comedy."
        ),
        "genre": "Romance",
        "release_year": 2009,
        "duration": 95,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/4RdJlNnKYJMCyuBMoFb2hgGNKpF.jpg",
        "status": "Completed",
    },
    # ── Animation ─────────────────────────────────────────────────────────────
    {
        "title": "Spirited Away",
        "description": (
            "During her family's move to the suburbs, a sullen 10-year-old girl wanders into "
            "a world ruled by gods, witches, and spirits, and where humans are changed into beasts. "
            "Miyazaki's masterpiece is the greatest animated film ever made."
        ),
        "genre": "Animation",
        "release_year": 2001,
        "duration": 125,
        "rating": 9.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
        "status": "Completed",
    },
    {
        "title": "The Lion King",
        "description": (
            "Lion cub and future king Simba searches for his identity. His eagerness to please "
            "others and his tendency to run from his problems will test him on his journey to adulthood. "
            "Disney's 1994 masterpiece remains one of the finest animated films ever made."
        ),
        "genre": "Animation",
        "release_year": 1994,
        "duration": 88,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/sKCr78MXSuUSFdY0tQmtgp7a7uA.jpg",
        "status": "Completed",
    },
    {
        "title": "WALL-E",
        "description": (
            "In the distant future, a small waste-collecting robot inadvertently embarks on "
            "a space journey that will ultimately decide the fate of mankind. "
            "Pixar's sci-fi romance is one of the most visually expressive animated films ever made."
        ),
        "genre": "Animation",
        "release_year": 2008,
        "duration": 98,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/hbhFnRzzg6ZDmm8YAmxBnQpQIPh.jpg",
        "status": "Completed",
    },
    {
        "title": "Spider-Man: No Way Home",
        "description": (
            "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help. "
            "When a spell goes wrong, dangerous foes from other worlds start to appear. "
            "A love letter to three generations of Spider-Man fans."
        ),
        "genre": "Fantasy",
        "release_year": 2021,
        "duration": 148,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg",
        "status": "Completed",
    },
    {
        "title": "Toy Story",
        "description": (
            "A cowboy doll is profoundly threatened and jealous when a new spaceman figure "
            "supplants him as top toy in a boy's room. The first fully computer-animated feature "
            "film remains a towering achievement in storytelling."
        ),
        "genre": "Animation",
        "release_year": 1995,
        "duration": 81,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPu9cdmR9.jpg",
        "status": "Completed",
    },
    {
        "title": "Up",
        "description": (
            "78-year-old Carl Fredricksen travels to Paradise Falls in his house equipped "
            "with balloons, inadvertently taking a young stowaway. Pixar's tear-jerking adventure "
            "opens with one of the greatest montages in cinema history."
        ),
        "genre": "Animation",
        "release_year": 2009,
        "duration": 96,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/vpR0ib4HD8yLdExMvbyYBm4GZui.jpg",
        "status": "Completed",
    },
    {
        "title": "Inside Out",
        "description": (
            "After young Riley is uprooted from her Midwest life and moved to San Francisco, "
            "her emotions - Joy, Fear, Anger, Disgust and Sadness - conflict on how best to "
            "navigate a new city. Pixar's most ingenious and emotionally mature film."
        ),
        "genre": "Animation",
        "release_year": 2015,
        "duration": 95,
        "rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/aAmfIX3TT40zUHGcCKrlOZRKC7u.jpg",
        "status": "Completed",
    },
    {
        "title": "Coco",
        "description": (
            "Aspiring musician Miguel, confronted with his family's ancestral ban on music, "
            "enters the Land of the Dead to find his great-great-grandfather, a legendary singer. "
            "Pixar's most culturally rich film is a joyful celebration of heritage and memory."
        ),
        "genre": "Animation",
        "release_year": 2017,
        "duration": 105,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/gGEsBPAijhVUFoiNpgZXqRVWJt2.jpg",
        "status": "Completed",
    },
    # ── Drama / Biographical ──────────────────────────────────────────────────
    {
        "title": "Bohemian Rhapsody",
        "description": (
            "The story of the legendary British rock band Queen and lead singer Freddie Mercury, "
            "leading up to their famous performance at Live Aid in 1985. "
            "Rami Malek's Oscar-winning portrayal of Freddie Mercury is electrifying."
        ),
        "genre": "Drama",
        "release_year": 2018,
        "duration": 134,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/lHu1wtNaczFPGFDTrjCSzeLPTKN.jpg",
        "status": "Completed",
    },
    {
        "title": "The Wolf of Wall Street",
        "description": (
            "Based on the true story of Jordan Belfort, from his rise to a wealthy stock-broker "
            "living the high life to his fall involving crime, corruption, and the federal government. "
            "Scorsese's most exhilarating film since Goodfellas."
        ),
        "genre": "Crime",
        "release_year": 2013,
        "duration": 180,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/34m2tygAYBGqA9MXKhRDtzSd5ro.jpg",
        "status": "Completed",
    },
    {
        "title": "Goodfellas",
        "description": (
            "The story of Henry Hill and his life in the mob, covering his relationship with "
            "his wife Karen Hill and his mob partners Jimmy Conway and Tommy DeVito "
            "in the Italian-American crime syndicate. Scorsese's best film, and arguably "
            "the greatest crime film ever made."
        ),
        "genre": "Crime",
        "release_year": 1990,
        "duration": 146,
        "rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/aKuFiU82s5ISJpGZp7YkIr3kCUd.jpg",
        "status": "Completed",
    },
    {
        "title": "Once Upon a Time in Hollywood",
        "description": (
            "A faded television actor and his stunt double strive to achieve fame and success "
            "in the film industry during the final years of Hollywood's Golden Age in 1969 Los Angeles. "
            "Tarantino's most nostalgic and personal film."
        ),
        "genre": "Drama",
        "release_year": 2019,
        "duration": 161,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/8j58iEBw9pOXFD2L0nt0ZXeHviB.jpg",
        "status": "Completed",
    },
    {
        "title": "The Revenant",
        "description": (
            "A frontiersman on a fur trading expedition in the 1820s fights for survival "
            "after being mauled by a bear and left for dead by members of his own hunting team. "
            "Alejandro Inarritu's brutal survival epic earned DiCaprio his first Oscar."
        ),
        "genre": "Drama",
        "release_year": 2015,
        "duration": 156,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/ji3ecJphATlVgWNY0B0RVXZizdf.jpg",
        "status": "Completed",
    },
    {
        "title": "The Irishman",
        "description": (
            "An aging hitman recalls his time with the mob and the intersecting events with "
            "his friend, Jimmy Hoffa, through the 1950-80s. Scorsese's epic Netflix film is "
            "a melancholy meditation on violence, loyalty, and regret."
        ),
        "genre": "Crime",
        "release_year": 2019,
        "duration": 209,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/mbm8k3GFhXS0Rock3M9rNaOiqNB.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Birdman",
        "description": (
            "A washed-up superhero actor attempts to revive his faded career by writing and "
            "starring in a Broadway play. Alejandro Inarritu's one-shot technical marvel "
            "won Best Picture and four Oscars."
        ),
        "genre": "Drama",
        "release_year": 2014,
        "duration": 119,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/mLUWBMvKGv4bimOSGKXuNc8qnqB.jpg",
        "status": "Completed",
    },
    {
        "title": "Marriage Story",
        "description": (
            "A stage director and his actor wife struggle through a grueling, coast-to-coast "
            "divorce that pushes them to their personal limits. Noah Baumbach's Netflix film "
            "is one of the most emotionally devastating depictions of a relationship's end."
        ),
        "genre": "Drama",
        "release_year": 2019,
        "duration": 137,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/pZekG6xabBSLocxnFOm2k6x9EfO.jpg",
        "status": "Plan to Watch",
    },
    # ── Superhero / Blockbuster ───────────────────────────────────────────────
    {
        "title": "Avengers: Infinity War",
        "description": (
            "The Avengers and their allies must be willing to sacrifice all in an attempt "
            "to defeat the powerful Thanos before his blitz of devastation and ruin puts "
            "an end to the universe. The MCU's most daring film redefines the superhero genre."
        ),
        "genre": "Action",
        "release_year": 2018,
        "duration": 149,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
        "status": "Completed",
    },
    {
        "title": "Avengers: Endgame",
        "description": (
            "After the devastating events of Infinity War, the universe is in ruins. With "
            "the help of remaining allies, the Avengers assemble once more in order to "
            "reverse Thanos' actions and restore balance to the universe."
        ),
        "genre": "Action",
        "release_year": 2019,
        "duration": 181,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "status": "Completed",
    },
    {
        "title": "Black Panther",
        "description": (
            "T'Challa, heir to the hidden but advanced kingdom of Wakanda, must step forward "
            "to lead his people into a new future and must confront a challenger from his "
            "country's past. Ryan Coogler's culturally groundbreaking superhero film."
        ),
        "genre": "Action",
        "release_year": 2018,
        "duration": 134,
        "rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/uxzzxijgPIY7slzFvMotPv8wjKA.jpg",
        "status": "Completed",
    },
    {
        "title": "Doctor Strange in the Multiverse of Madness",
        "description": (
            "Doctor Strange teams up with a mysterious newcomer who possesses an unusual "
            "ability that can travel between multiverses, to face a powerful opponent. "
            "Sam Raimi brings his horror sensibility to the MCU."
        ),
        "genre": "Fantasy",
        "release_year": 2022,
        "duration": 126,
        "rating": 6.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/9Gtg2DzBhmYamXBS1hKAhiwbBKS.jpg",
        "status": "Watching",
    },
    # ── More Sci-Fi ───────────────────────────────────────────────────────────
    {
        "title": "Tenet",
        "description": (
            "Armed with only one word - Tenet - and fighting for the survival of the entire "
            "world, a Protagonist journeys through a twilight world of international espionage "
            "on a mission that will unfold in something beyond real time. Nolan's most ambitious puzzle."
        ),
        "genre": "Sci-Fi",
        "release_year": 2020,
        "duration": 150,
        "rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/k68nPLbIST6NP96JmTxmZijZcpf.jpg",
        "status": "Completed",
    },
    {
        "title": "2001: A Space Odyssey",
        "description": (
            "After discovering a mysterious artifact buried beneath the Lunar surface, "
            "mankind sets off on a quest to find its origins with help from intelligent "
            "supercomputer H.A.L. 9000. Kubrick's visionary science fiction film remains "
            "the medium's greatest achievement."
        ),
        "genre": "Sci-Fi",
        "release_year": 1968,
        "duration": 149,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/ve72VxNqjGM69Uky4WTo2bK6rfq.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Alien",
        "description": (
            "After a space merchant vessel receives an unknown transmission as a distress call, "
            "one of the crew is attacked by a mysterious life form and they soon realize that "
            "its life cycle has merely begun. Ridley Scott's haunted-house-in-space still terrifies."
        ),
        "genre": "Sci-Fi",
        "release_year": 1979,
        "duration": 117,
        "rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/vfrQk5IPloGg1v9Rzbh2Eg3VGyM.jpg",
        "status": "Completed",
    },
    {
        "title": "Gravity",
        "description": (
            "Two astronauts work together to survive after an accident leaves them stranded "
            "in space. Alfonso Cuaron's technical tour de force is one of the most visually "
            "spectacular films ever created."
        ),
        "genre": "Sci-Fi",
        "release_year": 2013,
        "duration": 91,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/A1VoK6RVdFwLxQyrRzMKXLCJKAK.jpg",
        "status": "Completed",
    },
    # ── Western ───────────────────────────────────────────────────────────────
    {
        "title": "Django Unchained",
        "description": (
            "With the help of a German bounty hunter, a freed slave sets out to rescue "
            "his wife from a brutal Mississippi plantation owner. Tarantino's Spaghetti "
            "Western tribute is wildly entertaining and defiantly political."
        ),
        "genre": "Western",
        "release_year": 2012,
        "duration": 165,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/7oWY8VDWW7thTzWh3OKYRkWcKU6.jpg",
        "status": "Completed",
    },
    {
        "title": "The Hateful Eight",
        "description": (
            "In the dead of a Wyoming winter, a bounty hunter and his prisoner find shelter "
            "in a stagecoach waystation with six other strangers. Tarantino's claustrophobic "
            "whodunit is a tense, explosive powder keg."
        ),
        "genre": "Western",
        "release_year": 2015,
        "duration": 168,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/tIBSxGqGQ8O5I1FOoOYHRpzMhA5.jpg",
        "status": "Completed",
    },
    {
        "title": "The Good, the Bad and the Ugly",
        "description": (
            "A bounty hunting scam joins two men in an uneasy alliance against a third "
            "in a race to find a fortune in gold buried in a remote cemetery. "
            "Sergio Leone's magnum opus remains the greatest Western ever made."
        ),
        "genre": "Western",
        "release_year": 1966,
        "duration": 178,
        "rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/bX2xnavhMYjWDoZp1VM6VnU1xwe.jpg",
        "status": "Completed",
    },
    # ── Documentary ───────────────────────────────────────────────────────────
    {
        "title": "Free Solo",
        "description": (
            "Follow Alex Honnold as he becomes the first person to ever free solo climb "
            "Yosemite's 3,000-foot El Capitan wall. The Oscar-winning documentary is one of "
            "the most heart-stopping pieces of filmmaking ever captured."
        ),
        "genre": "Documentary",
        "release_year": 2018,
        "duration": 100,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/v3ckfLFhgBSqTNIVmCi6a7aqQdE.jpg",
        "status": "Completed",
    },
    {
        "title": "Won't You Be My Neighbor?",
        "description": (
            "An exploration of the life, lessons, and legacy of iconic children's television "
            "host, Fred Rogers. The highest-grossing biographical documentary in U.S. history "
            "is a reminder of the power of kindness."
        ),
        "genre": "Documentary",
        "release_year": 2018,
        "duration": 94,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/vMmkgGAFnbVwkIAnSQ7g1lGdvDD.jpg",
        "status": "Plan to Watch",
    },
    # ── 2023–2024 Hits ────────────────────────────────────────────────────────
    {
        "title": "Poor Things",
        "description": (
            "The incredible tale about the fantastic evolution of Bella Baxter, a young woman "
            "brought back to life by the brilliant and unorthodox scientist Dr. Godwin Baxter. "
            "Yorgos Lanthimos' visually striking feminist fairy tale won the Palme d'Or."
        ),
        "genre": "Fantasy",
        "release_year": 2023,
        "duration": 141,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/kCGlIMHnOm8JPXEaM7PtVNHxa0q.jpg",
        "status": "Watching",
    },
    {
        "title": "The Zone of Interest",
        "description": (
            "The commandant of Auschwitz, Rudolf Hoss, and his wife strive to build a "
            "dream life for their family in a house and garden next to the camp. "
            "Jonathan Glazer's devastating film depicts horror through banality."
        ),
        "genre": "History",
        "release_year": 2023,
        "duration": 105,
        "rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/hUu9zyZmDd6D4j7M0F24gBxLMTl.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Killers of the Flower Moon",
        "description": (
            "Members of the Osage Nation are murdered under mysterious circumstances in the "
            "1920s, sparking a major F.B.I. investigation. Scorsese's sprawling epic is a "
            "searing indictment of American greed and racial violence."
        ),
        "genre": "History",
        "release_year": 2023,
        "duration": 206,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/dB6Krk806zeqd0YNp2ngQ9zXteH.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Past Lives",
        "description": (
            "Two childhood friends are separated when one emigrates from South Korea, but "
            "are reunited decades later for one fateful week in New York City. "
            "Celine Song's debut feature is an achingly beautiful meditation on love and roads not taken."
        ),
        "genre": "Romance",
        "release_year": 2023,
        "duration": 106,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/k3waqVXSnYiJWCNZfCMaU0UaWqd.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "The Holdovers",
        "description": (
            "A curmudgeonly instructor at a New England prep school is forced to remain "
            "on campus during the holidays with a troubled student who has no place to go. "
            "A warm, funny, and deeply human film in the vein of 1970s character dramas."
        ),
        "genre": "Drama",
        "release_year": 2023,
        "duration": 133,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/VHSzNBTwxV8vh7wylo7O9CLdaCe.jpg",
        "status": "Completed",
    },
    {
        "title": "Barbie",
        "description": (
            "Barbie suffers a crisis that leads her to question her perfect life in Barbieland, "
            "and journey to the real world where she explores what it truly means to be human. "
            "Greta Gerwig's meta-comedy became one of the most culturally significant films of 2023."
        ),
        "genre": "Comedy",
        "release_year": 2023,
        "duration": 114,
        "rating": 6.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/iuFNMS8vlbOQFBUcrUqkEPcCaSh.jpg",
        "status": "Completed",
    },
    {
        "title": "Alien: Romulus",
        "description": (
            "While scavenging the deep ends of a derelict space station, a group of young "
            "space colonizers come face to face with the most terrifying life form in the "
            "universe. Fede Alvarez delivers the most frightening Alien film in decades."
        ),
        "genre": "Horror",
        "release_year": 2024,
        "duration": 119,
        "rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/9SSEUrSqhljBMzRe4aBTh17rUaC.jpg",
        "status": "Watching",
    },
    {
        "title": "Gladiator II",
        "description": (
            "Years after witnessing the death of the revered hero Maximus at the hands of "
            "the corrupt Commodus, Lucius is forced to enter the Colosseum and must look "
            "to his past to find strength and honor. Ridley Scott returns to ancient Rome."
        ),
        "genre": "Action",
        "release_year": 2024,
        "duration": 148,
        "rating": 7.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/2cxhvwyEwRlysAmRH4iodkvo0z5.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "Deadpool & Wolverine",
        "description": (
            "Deadpool is offered a place in the Marvel Cinematic Universe by the Time Variance "
            "Authority, but instead recruits a variant of Wolverine to save his universe. "
            "The highest-grossing R-rated film in history."
        ),
        "genre": "Action",
        "release_year": 2024,
        "duration": 127,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
        "status": "Completed",
    },
    {
        "title": "Inside Out 2",
        "description": (
            "Teenage Riley's mind headquarters is suddenly turned upside down when Anxiety "
            "shows up unexpectedly. Pixar's beloved sequel introduces a host of new emotions "
            "and surpassed a billion dollars at the box office."
        ),
        "genre": "Animation",
        "release_year": 2024,
        "duration": 100,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",
        "status": "Completed",
    },
    # ── World Cinema ──────────────────────────────────────────────────────────
    {
        "title": "City of God",
        "description": (
            "In the slums of Rio, two kids' paths diverge as one grows up to be a photographer "
            "and the other a drug dealer. Fernando Meirelles' kinetic crime epic is one of the "
            "most powerful films of the 21st century."
        ),
        "genre": "Crime",
        "release_year": 2002,
        "duration": 130,
        "rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/k7eYdWvhYQyRQoU2TB2A2Xu2TfD.jpg",
        "status": "Completed",
    },
    {
        "title": "Oldboy",
        "description": (
            "After being kidnapped and imprisoned for fifteen years, Oh Dae-Su is released, "
            "only to find that he must find his captor in five days. Park Chan-wook's "
            "vengeance thriller is a disturbing and electrifying masterpiece."
        ),
        "genre": "Thriller",
        "release_year": 2003,
        "duration": 120,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/pWDtjs568ZfOTMbURQBYuT4Qxka.jpg",
        "status": "Completed",
    },
    {
        "title": "Princess Mononoke",
        "description": (
            "On a journey to find the cure for a Tatarigami's curse, Ashitaka finds himself "
            "in the middle of a war between the forest gods and Tatara, a mining colony. "
            "Miyazaki's epic environmental fable is his most complex and mature work."
        ),
        "genre": "Animation",
        "release_year": 1997,
        "duration": 134,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/jHxhEKHlFKiLKRJqGJrh6sCWOuI.jpg",
        "status": "Completed",
    },
    {
        "title": "Amelie",
        "description": (
            "A quirky, idealistic Parisian girl decides to change the lives of those around "
            "her for the better, while struggling with her own isolation. Jean-Pierre Jeunet's "
            "whimsical romantic comedy is one of the most visually inventive films ever made."
        ),
        "genre": "Romance",
        "release_year": 2001,
        "duration": 122,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/nzpMBMKhRCi7mFqCRrqJBBunOqh.jpg",
        "status": "Completed",
    },
    {
        "title": "Pan's Labyrinth",
        "description": (
            "In post-Civil War Spain, a girl who loves fairy tales seeks refuge in an eerie "
            "but captivating fantasy world. Guillermo del Toro's dark fairy tale is a heartbreaking "
            "meditation on escapism and the horrors of fascism."
        ),
        "genre": "Fantasy",
        "release_year": 2006,
        "duration": 118,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/htYSMJBnmArCHNXzCXWpVyCCVvw.jpg",
        "status": "Completed",
    },
    {
        "title": "Drive My Car",
        "description": (
            "A stage actor and director, still emotionally adrift two years after the death "
            "of his wife, receives unexpected consolation from his taciturn young chauffeur. "
            "Ryusuke Hamaguchi's Palme d'Or-winning epic is an extraordinary meditation on grief."
        ),
        "genre": "Drama",
        "release_year": 2021,
        "duration": 179,
        "rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/y0DeetxVBIBjH4iJpQH0kBFrSja.jpg",
        "status": "Plan to Watch",
    },
    # ── Modern Classics ───────────────────────────────────────────────────────
    {
        "title": "Memento",
        "description": (
            "A man with short-term memory loss attempts to track down his wife's murderer. "
            "Christopher Nolan's reverse-chronology noir is a dazzling puzzle that becomes "
            "more devastating with each viewing."
        ),
        "genre": "Mystery",
        "release_year": 2000,
        "duration": 113,
        "rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/yuNs09hvpHVU1cBTCAk9zxsL2oW.jpg",
        "status": "Completed",
    },
    {
        "title": "There Will Be Blood",
        "description": (
            "A story of family, religion, hatred, oil, and madness, focusing on a ruthless "
            "man who becomes a wealthy silver miner and oil man in the early 20th century. "
            "Daniel Day-Lewis delivers one of the greatest screen performances of all time."
        ),
        "genre": "Drama",
        "release_year": 2007,
        "duration": 158,
        "rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/fa0RDkAlCec0STeMNfan0NZwG3TP.jpg",
        "status": "Completed",
    },
    {
        "title": "Eternal Sunshine of the Spotless Mind",
        "description": (
            "When their relationship turns sour, a couple undergoes a medical procedure "
            "to have each other erased from their memories. Michel Gondry and Charlie Kaufman's "
            "inventive romantic drama is a one-of-a-kind cinematic experience."
        ),
        "genre": "Romance",
        "release_year": 2004,
        "duration": 108,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/5MwkWH9tYHv3mV9OqYdjuXGOxHm.jpg",
        "status": "Completed",
    },
    {
        "title": "Children of Men",
        "description": (
            "In 2027, in a chaotic world in which women have somehow become infertile, "
            "a former activist agrees to help transport a miraculously pregnant woman to "
            "a sanctuary at sea. Alfonso Cuaron's dystopian masterpiece is staggeringly powerful."
        ),
        "genre": "Sci-Fi",
        "release_year": 2006,
        "duration": 109,
        "rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/mfwq2nMBzArzQ7Y9RKE8SKeaTry.jpg",
        "status": "Completed",
    },
    {
        "title": "Her",
        "description": (
            "A lonely writer develops an unlikely relationship with an operating system designed "
            "to meet his every need. Spike Jonze's tender, melancholy sci-fi romance asks "
            "profound questions about connection in the digital age."
        ),
        "genre": "Sci-Fi",
        "release_year": 2013,
        "duration": 126,
        "rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/sPg43VwHWOOxOSZyUXRhNKxRiCH.jpg",
        "status": "Completed",
    },
    {
        "title": "Moonlight",
        "description": (
            "A young man's journey is followed over three defining chapters in his life, "
            "as he experiences the ecstasy, pain, and beauty of falling in love, while "
            "grappling with his sexuality. Barry Jenkins' Oscar-winning film is intimately tender."
        ),
        "genre": "Drama",
        "release_year": 2016,
        "duration": 111,
        "rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/4911T5FbJ9eAlnDfXbObNkXrQDj.jpg",
        "status": "Completed",
    },
    {
        "title": "Nomadland",
        "description": (
            "Following the economic collapse of a company town in rural Nevada, Fern packs "
            "her van and sets off on the road exploring a life outside of conventional society "
            "as a modern-day nomad. Chloe Zhao's Oscar-winning film is quietly transformative."
        ),
        "genre": "Drama",
        "release_year": 2020,
        "duration": 108,
        "rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/66A9MqNax9CVDuoqDlVqqoeaVlB.jpg",
        "status": "Completed",
    },
    {
        "title": "The Lighthouse",
        "description": (
            "Two lighthouse keepers try to maintain their sanity while living on a remote "
            "and mysterious New England island in the 1890s. Robert Eggers' black-and-white "
            "psychological horror is a fever dream steeped in maritime myth."
        ),
        "genre": "Horror",
        "release_year": 2019,
        "duration": 110,
        "rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/3nSMdoZWZqcFAEGHaufBGEBXSvF.jpg",
        "status": "Dropped",
    },
    {
        "title": "Promising Young Woman",
        "description": (
            "A young woman, traumatized by a tragic event in her past, seeks out men who "
            "prey on inebriated women. Emerald Fennell's provocative revenge thriller is "
            "a subversive take on the rape-revenge genre."
        ),
        "genre": "Thriller",
        "release_year": 2020,
        "duration": 113,
        "rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/ii5bKJ9KzhrMHFZGmWx8hqg7nSA.jpg",
        "status": "Completed",
    },
    {
        "title": "Sound of Metal",
        "description": (
            "A heavy-metal drummer's life is thrown into turmoil when he begins to lose "
            "his hearing. Darius Marder's film is a profoundly empathetic portrait of "
            "loss, acceptance, and the nature of silence."
        ),
        "genre": "Drama",
        "release_year": 2019,
        "duration": 120,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/jwGhSBdg8MHuLN9pEaAoizXQPnS.jpg",
        "status": "Plan to Watch",
    },
    {
        "title": "The Father",
        "description": (
            "A man refuses all assistance from his daughter as he ages. As he tries to "
            "make sense of his changing circumstances, he begins to doubt his loved ones, "
            "his own mind and even the fabric of his reality. Anthony Hopkins won the Oscar "
            "for Best Actor for this harrowing portrayal of dementia."
        ),
        "genre": "Drama",
        "release_year": 2020,
        "duration": 97,
        "rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/fFRq98cW9lTo6di2o4lK1qUAWaN.jpg",
        "status": "Completed",
    },
    {
        "title": "Mank",
        "description": (
            "The story of how classic Hollywood's most controversial writer, Herman J. "
            "Mankiewicz, came to co-write Citizen Kane. David Fincher's black-and-white "
            "love letter to Old Hollywood is impeccably crafted."
        ),
        "genre": "Drama",
        "release_year": 2020,
        "duration": 131,
        "rating": 6.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/4wyJBPY99mTSw8UO9c5mOxC63Iy.jpg",
        "status": "Dropped",
    },
    {
        "title": "Judas and the Black Messiah",
        "description": (
            "The story of Fred Hampton, Chairman of the Illinois Black Panther Party, and his "
            "fateful betrayal by FBI informant William O'Neal. Daniel Kaluuya won the Oscar "
            "for Best Supporting Actor for his towering performance."
        ),
        "genre": "History",
        "release_year": 2021,
        "duration": 126,
        "rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/3jzfVdDPZZwUcqCXXUkCGQGjNTE.jpg",
        "status": "Completed",
    },
    {
        "title": "The Menu",
        "description": (
            "A young couple travels to a coastal island to eat at an exclusive restaurant "
            "where the chef has prepared a lavish menu, with some shocking surprises. "
            "Mark Mylod's razor-sharp satire on fine dining and privilege is darkly hilarious."
        ),
        "genre": "Thriller",
        "release_year": 2022,
        "duration": 107,
        "rating": 7.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/v6aXzGWkEuHqXCpkZmNELqkpGLl.jpg",
        "status": "Completed",
    },
    {
        "title": "Glass Onion: A Knives Out Mystery",
        "description": (
            "Tech billionaire Miles Bron invites his friends for a getaway on his private "
            "Greek island. When someone turns up dead, Detective Benoit Blanc is put on the case. "
            "Rian Johnson's hilarious and inventive mystery sequel."
        ),
        "genre": "Mystery",
        "release_year": 2022,
        "duration": 139,
        "rating": 7.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/vDGr1YdrlfbU9wxTOdpf3zChmv9.jpg",
        "status": "Completed",
    },
    {
        "title": "Nope",
        "description": (
            "The residents of a lonely gulch in inland California bear witness to an "
            "uncanny and chilling discovery. Jordan Peele's third film is a visually "
            "spectacular spectacle wrapped in a meditation on spectatorship and exploitation."
        ),
        "genre": "Horror",
        "release_year": 2022,
        "duration": 130,
        "rating": 6.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/AcKVlWaNVVVFQwynzLQaTKEFrK4.jpg",
        "status": "Watching",
    },
    {
        "title": "The Banshees of Inisherin",
        "description": (
            "Two lifelong friends find themselves at an impasse when one abruptly ends their "
            "friendship, setting off a chain of events that has irreversible consequences for both. "
            "Martin McDonagh's darkly comic fable is both funny and deeply sad."
        ),
        "genre": "Drama",
        "release_year": 2022,
        "duration": 114,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/nryDz0EfOdYPRijr3sMGJv1rCYh.jpg",
        "status": "Completed",
    },
    {
        "title": "Tar",
        "description": (
            "Lydia Tar, widely considered to be the greatest living conductor, is about to "
            "make history as the first female chief conductor of the Berlin Philharmonic. "
            "Todd Field's measured, sophisticated drama features Cate Blanchett at the height of her powers."
        ),
        "genre": "Drama",
        "release_year": 2022,
        "duration": 158,
        "rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/2LBkw3ZkFi1TfDqrjKmBhRkKTGm.jpg",
        "status": "Watching",
    },
    {
        "title": "All Quiet on the Western Front",
        "description": (
            "A young German soldier's terrifying experiences and brutal disillusionment during "
            "the First World War. The 2022 German adaptation won four Academy Awards, "
            "including Best International Feature Film."
        ),
        "genre": "War",
        "release_year": 2022,
        "duration": 147,
        "rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/hgGmGgPRYOKHcMVmqgzGM0jKlge.jpg",
        "status": "Completed",
    },
    {
        "title": "The Whale",
        "description": (
            "A reclusive English teacher attempts to reconnect with his estranged teenage "
            "daughter. Darren Aronofsky's intimate chamber drama features Brendan Fraser's "
            "career-best and Oscar-winning performance."
        ),
        "genre": "Drama",
        "release_year": 2022,
        "duration": 117,
        "rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/jQ0gylJMxWSL490sy0RrPj1Lj7e.jpg",
        "status": "Completed",
    },
    {
        "title": "Women Talking",
        "description": (
            "In 2010, the women of an isolated religious colony struggle to reconcile their "
            "faith with a series of brutal crimes perpetrated by the colony's men. "
            "Sarah Polley's dialogue-driven drama is quietly revolutionary."
        ),
        "genre": "Drama",
        "release_year": 2022,
        "duration": 104,
        "rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/cS1FeRDKPeRFbAqGBXJCU8AcZaZ.jpg",
        "status": "Plan to Watch",
    },
]


# ---------------------------------------------------------------------------
# Status distribution weights (must sum to 1.0)
# ---------------------------------------------------------------------------

STATUS_WEIGHTS = {
    "Completed":     0.55,
    "Watching":      0.20,
    "Plan to Watch": 0.20,
    "Dropped":       0.05,
}


def get_weighted_status() -> str:
    """Return a random status respecting the defined distribution."""
    statuses = list(STATUS_WEIGHTS.keys())
    weights = list(STATUS_WEIGHTS.values())
    return random.choices(statuses, weights=weights, k=1)[0]


def spread_timestamps(count: int):
    """
    Generate a list of (created_at, updated_at) datetime tuples spread
    randomly over the past two years, so the dashboard looks like an
    active collection built over time.
    """
    now = datetime.utcnow()
    result = []
    for _ in range(count):
        # created anywhere between 730 and 1 days ago
        days_ago = random.randint(1, 730)
        created = now - timedelta(days=days_ago)
        # updated between created_at and now
        update_offset = random.randint(0, days_ago)
        updated = now - timedelta(days=update_offset)
        result.append((created, updated))
    return result


def seed_movies() -> None:
    """
    Main seeding function.
    - Creates the Flask application context.
    - Iterates over MOVIES list.
    - Skips movies that already exist in the database (by title).
    - Inserts new movies with realistic timestamps.
    - Commits once; rolls back on any failure.
    - Prints a clear summary.
    """
    app = create_app()

    with app.app_context():
        inserted = 0
        skipped = 0
        errors = 0

        # Pre-load existing titles for O(1) lookup
        existing_titles = {
            row[0] for row in db.session.query(Movie.title).all()
        }
        print(f"Found {len(existing_titles)} existing movie(s) in the database.")

        # Spread timestamps across the dataset
        timestamps = spread_timestamps(len(MOVIES))

        try:
            for idx, data in enumerate(MOVIES):
                title = data["title"]

                if title in existing_titles:
                    print(f"  [SKIP]   {title!r} already exists.")
                    skipped += 1
                    continue

                created_at, updated_at = timestamps[idx]

                movie = Movie(
                    title=title,
                    description=data.get("description"),
                    genre=data["genre"],
                    release_year=data["release_year"],
                    duration=data["duration"],
                    rating=data["rating"],
                    poster_url=data.get("poster_url"),
                    # Use the pre-defined status; fallback to weighted random
                    status=data.get("status") or get_weighted_status(),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                db.session.add(movie)
                existing_titles.add(title)  # Prevent intra-dataset duplicates
                print(
                    f"  [INSERT] {title!r}  "
                    f"({data['genre']}, {data['release_year']})"
                )
                inserted += 1

            # Single commit after all inserts
            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            errors += 1
            print(f"\n[ERROR] An exception occurred during seeding: {exc}")
            print("[ERROR] All changes have been rolled back.")
            raise

        # ── Summary ──────────────────────────────────────────────────────────
        print()
        print("=" * 52)
        print(f"  Inserted  : {inserted} movies")
        print(f"  Skipped   : {skipped} movies (already existed)")
        if errors:
            print(f"  Errors    : {errors}")
        print(
            "  Status    : Finished successfully."
            if not errors
            else "  Status    : Finished with errors."
        )
        print("=" * 52)


if __name__ == "__main__":
    seed_movies()
