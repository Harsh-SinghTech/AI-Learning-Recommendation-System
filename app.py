from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import database.init_db
import csv
import os
from urllib.parse import quote_plus

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

@app.route("/robots.txt")
def robots_txt():
    return app.send_static_file("robots.txt")

@app.route("/sitemap.xml")
def sitemap_xml():
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://ai-learning-recommendation-system-9qq5.onrender.com/</loc>
    </url>
</urlset>
"""
    return sitemap, 200, {"Content-Type": "application/xml"}

def load_recommendations():
    recommendations = []

    file_path = os.path.join(
        os.path.dirname(__file__),
        "dataset",
        "recommendations.csv"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            recommendations.append(row)

    return recommendations

def load_resources():

    resources = {}

    file_path = os.path.join(
        os.path.dirname(__file__),
        "dataset",
        "resources.csv"
    )

    with open(file_path, "r", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:
            resources[row["name"]] = row

    return resources

# -----------------------------
# ML CONTENT SIMILARITY MODEL
# -----------------------------

def calculate_ml_similarity(user_interest, user_skill_level):

    recommendations = load_recommendations()

    if not recommendations:
        return {}

    # Create a text profile for every recommendation
    recommendation_texts = []

    for row in recommendations:

        text = (
            row["interest"] + " "
            + row["skill_level"] + " "
            + row["course"] + " "
            + row["project"] + " "
            + row["career"] + " "
            + row["difficulty"] + " "
            + row["skills"]
        )

        recommendation_texts.append(text)


    # User profile
    user_profile = (
        user_interest + " "
        + user_skill_level
    )


    # TF-IDF converts text into numerical vectors
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )


    all_texts = (
        recommendation_texts
        + [user_profile]
    )


    # Convert text into TF-IDF numerical vectors

    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # User profile is the last vector
    user_vector = tfidf_matrix[-1]

    # Recommendation vectors are everything before the user profile
    recommendation_vectors = tfidf_matrix[0:len(recommendations)]

    # Calculate similarity
    similarities = cosine_similarity(
        user_vector,
        recommendation_vectors
    )[0]


    # Store similarity scores
    ml_scores = {}


    for index, row in enumerate(recommendations):

        key = (
            row["course"],
            row["project"]
        )

        ml_scores[key] = round(
            float(similarities[index]) * 100,
            2
        )


    return ml_scores

# --------------------------------
# PERSONALIZED LEARNING ROADMAP
# --------------------------------

ROADMAPS = {

    "Machine Learning": {

        "Beginner": [
            "Python Fundamentals",
            "NumPy & Pandas",
            "Statistics for Data Science",
            "Data Visualization",
            "Data Preprocessing",
            "Introduction to Machine Learning",
            "Feature Engineering",
            "Model Evaluation & Optimization",
            "Machine Learning Project",
            "Model Deployment"
        ],

        "Intermediate": [
            "Python for Machine Learning",
            "NumPy & Pandas",
            "Statistics for Data Science",
            "Data Preprocessing",
            "Feature Engineering",
            "Model Evaluation & Optimization",
            "Advanced Machine Learning",
            "Deep Learning",
            "Natural Language Processing",
            "MLOps",
            "End-to-End ML Deployment"
        ],

        "Advanced": [
            "Advanced Machine Learning",
            "Advanced Feature Engineering",
            "Advanced Model Optimization",
            "Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Generative AI",
            "MLOps",
            "End-to-End ML Deployment",
            "Production Machine Learning"
        ]
    },


    "Artificial Intelligence": {

        "Beginner": [
            "Python for AI",
            "Python Libraries",
            "Mathematics for AI",
            "Introduction to Machine Learning",
            "Data Preprocessing",
            "Machine Learning Project"
        ],

        "Intermediate": [
            "Python for AI",
            "Machine Learning",
            "Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Generative AI",
            "AI Assistant",
            "AI Project",
            "Model Deployment"
        ],

        "Advanced": [
            "Advanced Machine Learning",
            "Deep Learning",
            "Natural Language Processing",
            "Computer Vision",
            "Generative AI",
            "Large Language Models",
            "AI Agents",
            "MLOps",
            "Production AI Systems"
        ]
    },


    "Data Science": {

        "Beginner": [
            "Python for Data Science",
            "NumPy",
            "Pandas",
            "Statistics for Data Science",
            "Data Cleaning",
            "Data Visualization",
            "SQL",
            "Data Analysis Project"
        ],

        "Intermediate": [
            "Python for Data Science",
            "Advanced Pandas",
            "Statistics",
            "Data Visualization",
            "SQL",
            "Advanced Analytics",
            "Machine Learning",
            "Feature Engineering",
            "Data Science Project",
            "Model Deployment"
        ],

        "Advanced": [
            "Advanced Analytics",
            "Advanced Statistics",
            "Machine Learning",
            "Advanced Machine Learning",
            "Deep Learning",
            "Feature Engineering",
            "MLOps",
            "Data Science Capstone Project"
        ]
    },


    "Python": {

        "Beginner": [
            "Python Fundamentals",
            "Python Data Structures",
            "Functions",
            "File Handling",
            "Exception Handling",
            "Python Modules",
            "Python Mini Projects"
        ],

        "Intermediate": [
            "Python OOP",
            "Python Libraries",
            "File Handling",
            "APIs",
            "Automation",
            "Database Programming",
            "Flask Web Development",
            "Python Web Application",
            "Advanced Python Project"
        ],

        "Advanced": [
            "Advanced Python",
            "Advanced OOP",
            "Async Python",
            "APIs & Microservices",
            "Database Systems",
            "Flask",
            "Testing",
            "Deployment",
            "Production Python Project"
        ]
    },


    "Web Development": {

        "Beginner": [
            "HTML & CSS",
            "Responsive Web Design",
            "JavaScript Fundamentals",
            "Git & GitHub",
            "Frontend Project"
        ],

        "Intermediate": [
            "Advanced HTML & CSS",
            "JavaScript",
            "DOM & APIs",
            "Frontend Development",
            "Flask Web Development",
            "Databases",
            "Authentication",
            "Full Stack Project",
            "Deployment"
        ],

        "Advanced": [
            "Advanced JavaScript",
            "Frontend Architecture",
            "Backend Development",
            "REST APIs",
            "Database Design",
            "Authentication & Security",
            "Full Stack Architecture",
            "Cloud Deployment",
            "Production Web Application"
        ]
    }
}
def get_recommendations(interest, skill_level):

    # --------------------------------
    # Load recommendation dataset
    # --------------------------------

    all_recommendations = load_recommendations()

    # Calculate ML similarity scores
    ml_scores = calculate_ml_similarity(
        interest,
        skill_level
    )

    matched_rows = []


    # --------------------------------
    # Get user's history and saved items
    # --------------------------------

    user_id = session.get("user_id")

    viewed_items = set()
    saved_items = set()

    if user_id:

        conn = get_db_connection()


        # Previously viewed recommendations

        history_rows = conn.execute("""
            SELECT recommendation_type, recommendation_name
            FROM recommendation_history
            WHERE user_id = ?
        """, (user_id,)).fetchall()


        for item in history_rows:

            viewed_items.add(
                (
                    item["recommendation_type"],
                    item["recommendation_name"]
                )
            )


        # Saved recommendations

        saved_rows = conn.execute("""
            SELECT recommendation_type, recommendation_name
            FROM saved_recommendations
            WHERE user_id = ?
        """, (user_id,)).fetchall()


        for item in saved_rows:

            saved_items.add(
                (
                    item["recommendation_type"],
                    item["recommendation_name"]
                )
            )


        conn.close()


    # --------------------------------
    # Match recommendations
    # --------------------------------

    for row in all_recommendations:

        if row["interest"] == interest:

            relevance = int(row["relevance"])


            # --------------------------------
            # Skill matching
            # --------------------------------

            if row["difficulty"] == skill_level:

                skill_match = 100

                skill_reason = "✓ Skill level matched"

            elif (
                (skill_level == "Beginner"
                 and row["difficulty"] == "Intermediate")

                or

                (skill_level == "Intermediate"
                 and row["difficulty"] in ["Beginner", "Advanced"])

                or

                (skill_level == "Advanced"
                 and row["difficulty"] == "Intermediate")
            ):

                skill_match = 80

                skill_reason = "✓ Suitable progression"

            else:

                skill_match = 65

                skill_reason = "✓ Available for exploration"


            # --------------------------------
            # Base recommendation score
            # --------------------------------

            # --------------------------------
            # ML similarity score
            # --------------------------------

            ml_key = (
                row["course"],
                row["project"]
            )

            ml_similarity = ml_scores.get(
                ml_key,
                0
            )


            # --------------------------------
            # Combined AI recommendation score
            # --------------------------------

            final_score = (
                (relevance * 0.70)
                +
                (skill_match * 0.20)
                +
                (ml_similarity * 0.10)
            )


            # --------------------------------
            # Determine recommendation type
            # --------------------------------

            course_name = row["course"]
            project_name = row["project"]


            course_key = (
                "course",
                course_name
            )

            project_key = (
                "project",
                project_name
            )


            # --------------------------------
            # Personalization
            # --------------------------------

            course_bonus = 0
            project_bonus = 0


            # Previously viewed → small penalty

            if course_key in viewed_items:

                course_bonus -= 8

            if project_key in viewed_items:

                project_bonus -= 8


            # Saved → small bonus

            if course_key in saved_items:

                course_bonus += 5

            if project_key in saved_items:

                project_bonus += 5


            # --------------------------------
            # Final personalized scores
            # --------------------------------

            course_score = int(
                max(
                    0,
                    min(
                        100,
                        final_score + course_bonus
                    )
                )
            )


            project_score = int(
                max(
                    0,
                    min(
                        100,
                        final_score + project_bonus
                    )
                )
            )


            # --------------------------------
            # Explanations
            # --------------------------------

            course_explanation = (
                f"✓ Interest matched: {interest} | "
                f"{skill_reason} | "
                f"Relevance: {relevance}% | "
                f"🤖 ML similarity: {ml_similarity:.1f}%"
            )


            project_explanation = (
                f"✓ Interest matched: {interest} | "
                f"{skill_reason} | "
                f"Relevance: {relevance}% | "
                f"🤖 ML similarity: {ml_similarity:.1f}%"
            )


            # Add personalization explanation

            if course_key in viewed_items:

                course_explanation += (
                    " | 📜 Previously viewed"
                )

            if course_key in saved_items:

                course_explanation += (
                    " | ⭐ Saved by you"
                )


            if project_key in viewed_items:

                project_explanation += (
                    " | 📜 Previously viewed"
                )

            if project_key in saved_items:

                project_explanation += (
                    " | ⭐ Saved by you"
                )


            # --------------------------------
            # Store course
            # --------------------------------

            matched_rows.append({

                "course": row["course"],

                "project": row["project"],

                "career": row["career"],

                "course_score": course_score,

                "project_score": project_score,

                "ml_similarity": ml_similarity,

                "course_explanation":
                    course_explanation,

                "project_explanation":
                    project_explanation,

                "description":
                    row.get(
                        "description",
                        ""
                    ),

                "difficulty":
                    row["difficulty"],

                "skills":
                    row["skills"],

                "youtube_url":
                    row.get("youtube_url", ""),

                "github_url":
                    row.get("github_url", "")

            })


    # --------------------------------
    # Sort recommendations
    # --------------------------------

    matched_rows.sort(
        key=lambda x: x["course_score"],
        reverse=True
    )


    # --------------------------------
    # Prepare output
    # --------------------------------

    courses = []

    projects = []

    course_scores = []

    project_scores = []

    career = ""


    for row in matched_rows:

        courses.append(
            row["course"]
        )

        projects.append(
            row["project"]
        )


        course_scores.append({

            "name":
                row["course"],

            "score":
                row["course_score"],

            "ml_similarity":
                row["ml_similarity"],

            "explanation":
                row["course_explanation"],

            "description":
                row["description"],

            "difficulty":
                row["difficulty"],

            "skills":
                row["skills"],

            "youtube_url": 
                row.get("youtube_url", ""),

            "github_url": 
                row.get("github_url", "")

            })


        project_scores.append({

            "name":
                row["project"],

            "score":
                row["project_score"],

            "ml_similarity":
                row["ml_similarity"],

            "explanation":
                row["project_explanation"],

            "description":
                row["description"],

            "difficulty":
                row["difficulty"],

            "skills":
                row["skills"],
                
            "youtube_url": 
                row.get("youtube_url", ""),
            
            "github_url": 
                row.get("github_url", "")
            

        })


        career = row["career"]


    # --------------------------------
    # Return recommendations
    # --------------------------------

    return {

        "courses":
            courses,

        "projects":
            projects,

        "career":
            career,

        "course_scores":
            course_scores,

        "project_scores":
            project_scores

    }
# Secret key for login sessions
app.secret_key = "ai_recommendation_system_secret_key"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_db_connection():
    conn = sqlite3.connect("database/ai_learning.db")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# CREATE SAVED RECOMMENDATIONS TABLE
# -----------------------------

def create_saved_table():

    conn = get_db_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS saved_recommendations (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        recommendation_type TEXT NOT NULL,

        recommendation_name TEXT NOT NULL,

        status TEXT DEFAULT 'Not Started',

        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(user_id, recommendation_type, recommendation_name)

    )
""")

    conn.commit()
    conn.close()


create_saved_table()
def add_progress_column():

    conn = get_db_connection()

    try:

        conn.execute("""
            ALTER TABLE saved_recommendations
            ADD COLUMN status TEXT DEFAULT 'Not Started'
        """)

        conn.commit()

    except sqlite3.OperationalError:

        pass

    conn.close()


add_progress_column()
# -----------------------------
# CREATE RECOMMENDATION HISTORY TABLE
# -----------------------------

def create_history_table():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS recommendation_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            recommendation_type TEXT NOT NULL,

            recommendation_name TEXT NOT NULL,

            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


create_history_table()
# -----------------------------
# HOME
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# REGISTER
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        interest = request.form["interest"]
        skill_level = request.form["skill_level"]

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:

            conn.execute("""
                INSERT INTO users
                (full_name, email, password, interest, skill_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                email,
                hashed_password,
                interest,
                skill_level
            ))

            conn.commit()

            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return """
            <h2>Email already registered.</h2>
            <a href="/register">Go Back</a>
            """

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]

            return redirect(url_for("dashboard"))

        else:

            return """
            <h2>Invalid email or password.</h2>
            <a href="/login">Try Again</a>
            """


    return render_template("login.html")


# --------------------------------
# PERSONALIZED ROADMAP
# --------------------------------

@app.route("/roadmap")
def roadmap():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Get logged-in user

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if user is None:
        return redirect(url_for("login"))


    # User profile

    interest = user["interest"]
    skill_level = user["skill_level"]


    # Get personalized roadmap

    roadmap_steps = ROADMAPS.get(
        interest,
        {}
    ).get(
        skill_level,
        []
    )


    # Load all learning resources

    resources = load_resources()


    # Build complete roadmap data

    roadmap_data = []


    for index, step in enumerate(
        roadmap_steps,
        start=1
    ):

        resource = resources.get(
            step,
            {}
        )


        # Existing resources.csv links

        youtube_url = resource.get(
            "youtube_url",
            ""
        )

        free_course_url = resource.get(
            "free_course_url",
            ""
        )

        paid_course_url = resource.get(
            "paid_course_url",
            ""
        )

        project_url = resource.get(
            "project_url",
            ""
        )


        # Fallback YouTube search if
        # a specific YouTube resource
        # has not been added yet

        if not youtube_url:

            youtube_url = (
                "https://www.youtube.com/results?search_query="
                + quote_plus(step)
            )


        roadmap_data.append({

            "number": index,

            "name": step,

            "progress": round(
                (index / len(roadmap_steps)) * 100
            ),

            "youtube_url": youtube_url,

            "free_course_url": free_course_url,

            "paid_course_url": paid_course_url,

            "project_url": project_url

        })


    return render_template(
        "roadmap.html",

        roadmap_data=roadmap_data,

        interest=interest,

        skill_level=skill_level
    )

# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    recommendations = get_recommendations(
        user["interest"],
        user["skill_level"]
    )

    return render_template(
        "dashboard.html",
        user_name=user["full_name"],
        interest=user["interest"],
        skill_level=user["skill_level"],
        courses=recommendations["courses"],
        projects=recommendations["projects"],
        career=recommendations["career"],
        recommendations=recommendations
    )

# -----------------------------
# SAVE RECOMMENDATION
# -----------------------------

@app.route("/save-recommendation", methods=["POST"])
def save_recommendation():

    if "user_id" not in session:
        return redirect(url_for("login"))

    recommendation_type = request.form["recommendation_type"]
    recommendation_name = request.form["recommendation_name"]

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT OR IGNORE INTO saved_recommendations
            (user_id, recommendation_type, recommendation_name)
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            recommendation_type,
            recommendation_name
        ))

        conn.commit()

    finally:
        conn.close()

    return redirect(url_for(
        "recommendation",
        recommendation_type=recommendation_type,
        name=recommendation_name
    ))
# -----------------------------
# UPDATE LEARNING PROGRESS
# -----------------------------

@app.route("/update-progress", methods=["POST"])
def update_progress():

    if "user_id" not in session:
        return redirect(url_for("login"))

    recommendation_id = request.form["recommendation_id"]
    status = request.form["status"]

    allowed_statuses = [
        "Not Started",
        "In Progress",
        "Completed"
    ]

    if status not in allowed_statuses:
        return redirect(url_for("my_learning"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE saved_recommendations
        SET status = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        status,
        recommendation_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("my_learning"))
# -----------------------------
# RECOMMENDATION HISTORY
# -----------------------------

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    history_items = conn.execute("""
        SELECT *
        FROM recommendation_history
        WHERE user_id = ?
        ORDER BY viewed_at DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history_items
    )
# -----------------------------
# MY LEARNING
# -----------------------------

@app.route("/my-learning")
def my_learning():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    saved = conn.execute("""
        SELECT *
        FROM saved_recommendations
        WHERE user_id = ?
        ORDER BY saved_at DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "my_learning.html",
        saved=saved
    )

# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# -----------------------------
# RUN APPLICATION
# -----------------------------
@app.route("/recommendation/<recommendation_type>/<path:name>")
def recommendation(recommendation_type, name):

    # --------------------------------
    # Check login
    # --------------------------------

    if "user_id" not in session:
        return redirect(url_for("login"))


    # --------------------------------
    # Get logged-in user
    # --------------------------------

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()


    # --------------------------------
    # Get personalized recommendations
    # --------------------------------

    recommendations = get_recommendations(
        user["interest"],
        user["skill_level"]
    )


    # --------------------------------
    # Find selected recommendation
    # --------------------------------

    selected = None

    if recommendation_type == "course":

        for item in recommendations["course_scores"]:

            if item["name"] == name:

                selected = item
                break


    elif recommendation_type == "project":

        for item in recommendations["project_scores"]:

            if item["name"] == name:

                selected = item
                break


    # --------------------------------
    # Invalid recommendation
    # --------------------------------

    if selected is None:
        return redirect(url_for("dashboard"))


    # --------------------------------
    # Find exact recommendation in CSV
    # --------------------------------

    all_recommendations = load_recommendations()

    csv_data = None


    for row in all_recommendations:

        if recommendation_type == "course":

            if (
                row["course"] == name
                and row["interest"] == user["interest"]
            ):

                csv_data = row
                break


        elif recommendation_type == "project":

            if (
                row["project"] == name
                and row["interest"] == user["interest"]
            ):

                csv_data = row
                break


    # --------------------------------
    # If recommendation not found
    # --------------------------------

    if csv_data is None:
        return redirect(url_for("dashboard"))


    # --------------------------------
    # Get skills
    # --------------------------------

    skills = []

    if csv_data.get("skills"):

        skills = [
            skill.strip()
            for skill in csv_data["skills"].split(",")
        ]


    # --------------------------------
    # OPTIONAL RESOURCES
    # --------------------------------
    #
    # Free and paid resources still come
    # from resources.csv.
    #
    # YouTube and GitHub MUST come from
    # recommendations.csv.
    # --------------------------------

    resources = load_resources()

    resource = resources.get(
        name,
        {
            "free_course_url": "",
            "paid_course_url": ""
        }
    )


    # --------------------------------
    # DIRECT LINKS FROM RECOMMENDATIONS
    # --------------------------------

    youtube_url = csv_data.get(
        "youtube_url",
        ""
    )

    github_url = csv_data.get(
        "github_url",
        ""
    )

    # --------------------------------
    # SAVE RECOMMENDATION HISTORY
    # --------------------------------
    conn = get_db_connection()

    conn.execute("""
        INSERT INTO recommendation_history
        (user_id, recommendation_type, recommendation_name)
        VALUES (?, ?, ?)
    """, (
        session["user_id"],
        recommendation_type,
        name
    ))

    conn.commit()
    conn.close()


    # --------------------------------
    # Render recommendation page
    # --------------------------------
    ml_similarity = selected.get("ml_similarity", 0)
    return render_template(
    "recommendation.html",

    # Basic information
    name=name,
    recommendation_type=recommendation_type,

    description=csv_data.get(
        "description",
        ""
    ),

    difficulty=csv_data.get(
        "difficulty",
        ""
    ),

    skills=skills,

    # Recommendation information
    score=selected["score"],

    ml_similarity=selected.get(
        "ml_similarity",
        0
    ),

    interest=user["interest"],

    skill_level=user["skill_level"],

    # Direct resource links
    youtube_url=csv_data.get(
        "youtube_url",
        ""
    ),

    github_url=csv_data.get(
        "github_url",
        ""
    ),

    # Optional resources
    free_course_url=resource.get(
        "free_course_url",
        ""
    ),

    paid_course_url=resource.get(
        "paid_course_url",
        ""
    )
)

    

if __name__ == "__main__":
    app.run(debug=True)