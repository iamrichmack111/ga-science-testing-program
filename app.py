from __future__ import annotations

import csv
import io
import os
import random
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, jsonify, redirect, render_template,
    request, send_file, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash


APP_NAME = "Georgia Science Testing Program"
APP_SLUG = "ga_science_testing_program"

DATA_ROOT = Path(
    os.environ.get("RICHMACK_GRADES_DIR", Path.home() / "KIDS-HW" / "grades")
).expanduser().resolve()
GAME_DIR = DATA_ROOT / APP_SLUG
EXPORT_DIR = GAME_DIR / "exports"
DATABASE = GAME_DIR / f"{APP_SLUG}.db"

GAME_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("GA_SCIENCE_SECRET", secrets.token_hex(32))
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

THEMES = {
    "linux": {
        "name": "Linux Laboratory",
        "topic": "scientific_practices",
        "description": "Variables, evidence, models, data, and scientific investigations.",
        "standard": "S7L/SEP",
    },
    "jasmin": {
        "name": "Jasmin Cells",
        "topic": "cells",
        "description": "Cell structure, organelles, and levels of organization.",
        "standard": "S7L2",
    },
    "aria": {
        "name": "Aria Genetics",
        "topic": "genetics",
        "description": "Traits, heredity, reproduction, and variation.",
        "standard": "S7L3",
    },
    "ahmeenah": {
        "name": "Ahmeenah Ecology",
        "topic": "ecology",
        "description": "Ecosystems, food webs, energy flow, and environmental change.",
        "standard": "S7L4",
    },
    "zara": {
        "name": "Zara Classification",
        "topic": "classification",
        "description": "Organism classification and relationships among living things.",
        "standard": "S7L1",
    },
    "kaphmemeris": {
        "name": "Kaphmemeris Review",
        "topic": "mixed_review",
        "description": "A mixed Georgia Grade 7 life-science assessment.",
        "standard": "S7L1-S7L5",
    },
}

QUESTION_BANK = {
    "scientific_practices": {
        1: [
            ("Which tool is best for measuring temperature?", ["Thermometer", "Balance", "Ruler", "Stopwatch"], "Thermometer"),
            ("A scientific observation should be based mainly on what?", ["Evidence", "Opinion", "Guessing", "Popularity"], "Evidence"),
            ("Which variable is deliberately changed in an experiment?", ["Independent variable", "Dependent variable", "Control group", "Conclusion"], "Independent variable"),
        ],
        2: [
            ("Why do scientists repeat trials?", ["To improve reliability", "To change the hypothesis", "To avoid measurements", "To remove all variables"], "To improve reliability"),
            ("What is the dependent variable?", ["The measured outcome", "The changed factor", "A constant", "The hypothesis"], "The measured outcome"),
            ("Which graph is usually best for change over time?", ["Line graph", "Pie chart", "Venn diagram", "Food web"], "Line graph"),
        ],
        3: [
            ("A student tests fertilizer amounts on plant height. What should remain constant?", ["Plant type and water", "Fertilizer amount", "Plant height", "The conclusion"], "Plant type and water"),
            ("What does a scientific model do?", ["Represents a system or process", "Proves every claim", "Removes uncertainty", "Replaces all observations"], "Represents a system or process"),
            ("Which statement best describes a hypothesis?", ["A testable explanation", "A final proven fact", "A data table", "A measurement tool"], "A testable explanation"),
        ],
        4: [
            ("Why is a control group useful?", ["It provides a comparison", "It guarantees the hypothesis", "It changes all variables", "It removes the need for data"], "It provides a comparison"),
            ("Which conclusion is strongest?", ["One supported by repeated data", "One based on a single guess", "One that ignores contrary data", "One copied from another group"], "One supported by repeated data"),
            ("What should a scientist do when evidence does not support the hypothesis?", ["Revise the explanation", "Delete the evidence", "Stop measuring", "Change the data"], "Revise the explanation"),
        ],
        5: [
            ("Which practice best reduces measurement bias?", ["Use the same calibrated procedure", "Choose only favorable results", "Change tools each trial", "Round every value upward"], "Use the same calibrated procedure"),
            ("A correlation between two variables proves what?", ["Association, not necessarily causation", "Definite causation", "No relationship", "Experimental error only"], "Association, not necessarily causation"),
            ("Why should methods be clearly documented?", ["So others can evaluate and repeat them", "To hide uncertainty", "To avoid peer review", "To guarantee identical conclusions"], "So others can evaluate and repeat them"),
        ],
    },
    "cells": {
        1: [
            ("What is the basic unit of life?", ["Cell", "Organ", "Tissue", "Atom"], "Cell"),
            ("Which structure controls cell activities?", ["Nucleus", "Cell wall", "Vacuole", "Cytoplasm"], "Nucleus"),
            ("Which structure surrounds every cell?", ["Cell membrane", "Cell wall", "Chloroplast", "Nucleus"], "Cell membrane"),
        ],
        2: [
            ("Which organelle releases usable energy from food?", ["Mitochondrion", "Ribosome", "Nucleus", "Cell wall"], "Mitochondrion"),
            ("Which structure is found in plant cells but not animal cells?", ["Chloroplast", "Cell membrane", "Cytoplasm", "Mitochondrion"], "Chloroplast"),
            ("What do ribosomes make?", ["Proteins", "Glucose", "DNA copies", "Cell walls"], "Proteins"),
        ],
        3: [
            ("Which sequence goes from simplest to most complex?", ["Cell, tissue, organ, organ system", "Organ, cell, tissue, system", "Tissue, cell, organ system, organ", "Cell, organ system, tissue, organ"], "Cell, tissue, organ, organ system"),
            ("What is diffusion?", ["Movement from high to low concentration", "Movement requiring only sunlight", "Cell division", "Protein production"], "Movement from high to low concentration"),
            ("What is the function of the cell membrane?", ["Controls what enters and leaves", "Stores hereditary information", "Makes all proteins", "Produces cell walls"], "Controls what enters and leaves"),
        ],
        4: [
            ("Why are cells usually small?", ["Small cells exchange materials efficiently", "Small cells have no DNA", "Large cells cannot contain water", "Small cells do not use energy"], "Small cells exchange materials efficiently"),
            ("A red blood cell and nerve cell differ mainly because they have what?", ["Specialized structures and functions", "Different genetic codes in one person", "No cell membranes", "Different atoms"], "Specialized structures and functions"),
            ("Which process maintains internal balance in a cell?", ["Homeostasis", "Classification", "Mutation only", "Fossilization"], "Homeostasis"),
        ],
        5: [
            ("A cell placed in a highly concentrated salt solution loses water by what process?", ["Osmosis", "Photosynthesis", "Mitosis", "Respiration"], "Osmosis"),
            ("How do organ systems support multicellular organisms?", ["They coordinate specialized functions", "They make every cell identical", "They eliminate homeostasis", "They prevent energy use"], "They coordinate specialized functions"),
            ("Why can membrane damage threaten cell survival?", ["It disrupts material transport and homeostasis", "It changes the organism's kingdom", "It creates chloroplasts", "It makes tissues larger"], "It disrupts material transport and homeostasis"),
        ],
    },
    "genetics": {
        1: [
            ("Traits are passed from parents to offspring through what?", ["Genes", "Food", "Muscles", "Weather"], "Genes"),
            ("Where is hereditary information stored?", ["DNA", "Cell wall", "Water", "Glucose"], "DNA"),
            ("An organism with two identical alleles is what?", ["Homozygous", "Heterozygous", "Asexual", "Mutated"], "Homozygous"),
        ],
        2: [
            ("Which process produces genetically identical offspring from one parent?", ["Asexual reproduction", "Sexual reproduction", "Meiosis only", "Fertilization"], "Asexual reproduction"),
            ("What is an allele?", ["A version of a gene", "An organelle", "A tissue", "A food molecule"], "A version of a gene"),
            ("Which reproduction type usually increases genetic variation?", ["Sexual reproduction", "Binary fission", "Budding only", "Cloning"], "Sexual reproduction"),
        ],
        3: [
            ("What does a Punnett square predict?", ["Possible offspring traits", "Exact future population size", "Cell organelles", "Ecosystem energy"], "Possible offspring traits"),
            ("If B is dominant and b is recessive, which genotype shows the recessive trait?", ["bb", "BB", "Bb", "Either BB or Bb"], "bb"),
            ("What is phenotype?", ["Observable trait", "Allele combination", "DNA molecule only", "Cell division"], "Observable trait"),
        ],
        4: [
            ("Why do siblings from the same parents often differ?", ["They inherit different allele combinations", "They have unrelated DNA", "They belong to different species", "Environment never affects traits"], "They inherit different allele combinations"),
            ("A mutation may be what?", ["Helpful, harmful, or neutral", "Always harmful", "Always inherited", "Always visible"], "Helpful, harmful, or neutral"),
            ("Which statement about traits is most accurate?", ["Genes and environment can both influence traits", "Only genes matter", "Only environment matters", "Traits never change"], "Genes and environment can both influence traits"),
        ],
        5: [
            ("How can sexual reproduction support population survival?", ["It creates genetic variation", "It eliminates mutations", "It produces identical offspring", "It prevents natural selection"], "It creates genetic variation"),
            ("A carrier for a recessive trait is usually what genotype?", ["Heterozygous", "Homozygous dominant", "Homozygous recessive", "No alleles"], "Heterozygous"),
            ("Why can some mutations affect offspring while others cannot?", ["Only mutations in reproductive cells can be inherited", "All body-cell mutations are inherited", "Mutations never reach offspring", "Only dominant mutations exist"], "Only mutations in reproductive cells can be inherited"),
        ],
    },
    "ecology": {
        1: [
            ("What is a producer?", ["An organism that makes its own food", "An organism that eats only animals", "A decomposer only", "A nonliving factor"], "An organism that makes its own food"),
            ("What is a habitat?", ["The place an organism lives", "Its genetic code", "Its food chain position only", "Its species name"], "The place an organism lives"),
            ("Which is an abiotic factor?", ["Sunlight", "Grass", "Bacteria", "Rabbit"], "Sunlight"),
        ],
        2: [
            ("What do decomposers do?", ["Recycle nutrients", "Make sunlight", "Create all oxygen", "Stop food chains"], "Recycle nutrients"),
            ("Arrows in a food web show what?", ["Direction of energy transfer", "Animal size", "Population age", "Water flow only"], "Direction of energy transfer"),
            ("Which organism is most likely a primary consumer?", ["Rabbit", "Hawk", "Mushroom", "Grass"], "Rabbit"),
        ],
        3: [
            ("Why is less energy available at higher trophic levels?", ["Energy is used and lost as heat", "Producers store no energy", "Consumers create sunlight", "Energy cycles without loss"], "Energy is used and lost as heat"),
            ("What is carrying capacity?", ["Largest population an environment can support", "Number of predators only", "Amount of sunlight", "Number of species names"], "Largest population an environment can support"),
            ("What might happen if a top predator is removed?", ["Food-web populations may become unbalanced", "All producers disappear immediately", "Energy flow stops completely", "Abiotic factors vanish"], "Food-web populations may become unbalanced"),
        ],
        4: [
            ("Which change is most likely to reduce biodiversity?", ["Habitat destruction", "Resource protection", "Native plant restoration", "Pollution reduction"], "Habitat destruction"),
            ("How does competition affect organisms?", ["They struggle for limited resources", "They always cooperate", "They stop reproducing completely", "They become producers"], "They struggle for limited resources"),
            ("An invasive species may harm an ecosystem because it can what?", ["Outcompete native species", "Increase every native population", "Remove all abiotic factors", "Prevent weather"], "Outcompete native species"),
        ],
        5: [
            ("Why can a small change to one population affect an entire food web?", ["Species are interconnected through energy and resource relationships", "Every organism is independent", "Only producers matter", "Food webs contain one pathway"], "Species are interconnected through energy and resource relationships"),
            ("Which evidence best indicates ecosystem recovery?", ["Increasing native biodiversity and stable populations", "One invasive species dominates", "Soil loss increases", "Producer populations collapse"], "Increasing native biodiversity and stable populations"),
            ("How can limiting factors regulate populations?", ["They restrict growth when resources are scarce", "They guarantee unlimited growth", "They remove competition", "They eliminate carrying capacity"], "They restrict growth when resources are scarce"),
        ],
    },
    "classification": {
        1: [
            ("Why do scientists classify organisms?", ["To organize and compare living things", "To change their traits", "To eliminate species", "To measure weather"], "To organize and compare living things"),
            ("Which level is most specific?", ["Species", "Kingdom", "Phylum", "Class"], "Species"),
            ("A scientific name contains what two parts?", ["Genus and species", "Kingdom and phylum", "Class and order", "Family and kingdom"], "Genus and species"),
        ],
        2: [
            ("Which characteristic is used in modern classification?", ["Shared traits and genetic evidence", "Color only", "Habitat only", "Size only"], "Shared traits and genetic evidence"),
            ("Organisms in the same genus are generally what?", ["Closely related", "Always identical", "In different kingdoms", "Unable to reproduce"], "Closely related"),
            ("What is a dichotomous key used for?", ["Identifying organisms", "Measuring mass", "Tracking weather", "Calculating energy"], "Identifying organisms"),
        ],
        3: [
            ("Which evidence best shows evolutionary relationship?", ["DNA similarities", "Same body size", "Same location today", "Same color"], "DNA similarities"),
            ("Why may classification systems change?", ["New evidence changes understanding", "Species choose new names", "Scientific names expire", "Kingdoms move locations"], "New evidence changes understanding"),
            ("Which group contains organisms that are more closely related?", ["Same family", "Same kingdom only", "Same domain only", "Different phyla"], "Same family"),
        ],
        4: [
            ("Two organisms share many DNA sequences but look different. What is most reasonable?", ["They may still be closely related", "They must be unrelated", "Appearance always outweighs DNA", "They belong to no kingdom"], "They may still be closely related"),
            ("Why are scientific names useful worldwide?", ["They provide a common naming system", "They replace all local languages", "They show population size", "They never change"], "They provide a common naming system"),
            ("What does a branching classification diagram represent?", ["Patterns of shared ancestry", "Exact organism age", "Daily population change", "Weather patterns"], "Patterns of shared ancestry"),
        ],
        5: [
            ("What is the strongest basis for revising evolutionary relationships?", ["Multiple lines of genetic and structural evidence", "One color similarity", "One habitat observation", "Common name spelling"], "Multiple lines of genetic and structural evidence"),
            ("Why can analogous structures be misleading in classification?", ["Similar function can evolve without close ancestry", "They always share identical genes", "They occur only in plants", "They prove the same species"], "Similar function can evolve without close ancestry"),
            ("A classification claim is strongest when it is supported by what?", ["Independent evidence from several sources", "One untested assumption", "Only body size", "Only geographic location"], "Independent evidence from several sources"),
        ],
    },
}


def now_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE,
            age INTEGER NOT NULL CHECK(age BETWEEN 5 AND 19),
            grade_level INTEGER NOT NULL CHECK(grade_level BETWEEN 1 AND 12),
            current_difficulty INTEGER NOT NULL DEFAULT 1 CHECK(current_difficulty BETWEEN 1 AND 5),
            diagnostic_complete INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(name, age)
        );

        CREATE TABLE IF NOT EXISTS test_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            theme_key TEXT NOT NULL,
            theme_name TEXT NOT NULL,
            topic TEXT NOT NULL,
            standard_code TEXT NOT NULL,
            mode TEXT NOT NULL,
            grade_level INTEGER NOT NULL,
            starting_difficulty INTEGER NOT NULL,
            ending_difficulty INTEGER NOT NULL,
            questions_attempted INTEGER NOT NULL,
            questions_correct INTEGER NOT NULL,
            raw_percent REAL NOT NULL,
            letter_grade TEXT NOT NULL,
            mastery_score REAL NOT NULL,
            mastery_status TEXT NOT NULL,
            seconds REAL NOT NULL,
            average_seconds REAL NOT NULL,
            timestamp TEXT NOT NULL,
            federation_version TEXT NOT NULL DEFAULT '1.0',
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS test_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_number INTEGER NOT NULL,
            topic TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            expected_answer TEXT NOT NULL,
            submitted_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            seconds REAL NOT NULL,
            FOREIGN KEY(session_id) REFERENCES test_sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_science_sessions_student ON test_sessions(student_id);
        CREATE INDEX IF NOT EXISTS idx_science_sessions_date ON test_sessions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_science_answers_session ON test_answers(session_id);
        """)

        pin = os.environ.get("GA_SCIENCE_PARENT_PIN", "2468")
        conn.execute("""
            INSERT INTO settings(key, value)
            VALUES ('parent_pin_hash', ?)
            ON CONFLICT(key) DO NOTHING
        """, (generate_password_hash(pin),))


def grade_letter(percent: float) -> str:
    if percent >= 90: return "A"
    if percent >= 80: return "B"
    if percent >= 70: return "C"
    if percent >= 60: return "D"
    return "F"


def expected_difficulty(grade: int) -> int:
    return max(1, min(5, grade - 3))


def mastery_status(score: float, difficulty: int, grade: int) -> str:
    expected = expected_difficulty(grade)
    if difficulty < expected - 1:
        return "Building prerequisite science skills"
    if score < 60:
        return "Needs targeted science review"
    if difficulty < expected:
        return "Approaching grade-level science mastery"
    if score >= 90 and difficulty > expected:
        return "Exceeding grade-level science expectations"
    if score >= 75:
        return "Meeting grade-level science expectations"
    return "Developing grade-level science mastery"


def make_question(topic: str, difficulty: int) -> dict:
    if topic == "mixed_review":
        topic = random.choice(list(QUESTION_BANK.keys()))
    difficulty = max(1, min(5, difficulty))
    available = QUESTION_BANK[topic].get(difficulty) or QUESTION_BANK[topic][1]
    prompt, choices, answer = random.choice(available)
    shuffled = choices[:]
    random.shuffle(shuffled)
    return {"topic": topic, "prompt": prompt, "choices": shuffled, "answer": answer}


def parent_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("parent_authenticated"):
            return redirect(url_for("parent_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return render_template("home.html", themes=THEMES, app_name=APP_NAME)


@app.route("/student", methods=["GET", "POST"])
def student():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        try:
            age = int(request.form.get("age", ""))
            grade_level = int(request.form.get("grade_level", ""))
        except ValueError:
            flash("Age and grade must be whole numbers.", "error")
            return render_template("student.html")

        if not name or not (5 <= age <= 19) or not (1 <= grade_level <= 12):
            flash("Enter a valid name, age, and grade.", "error")
            return render_template("student.html")

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM students WHERE name=? COLLATE NOCASE AND age=?",
                (name, age)
            ).fetchone()
            if row:
                student_id = row["id"]
                conn.execute(
                    "UPDATE students SET grade_level=?, updated_at=? WHERE id=?",
                    (grade_level, now_text(), student_id)
                )
            else:
                cursor = conn.execute("""
                    INSERT INTO students(
                        name, age, grade_level, current_difficulty,
                        diagnostic_complete, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 0, ?, ?)
                """, (name, age, grade_level, expected_difficulty(grade_level), now_text(), now_text()))
                student_id = cursor.lastrowid

        session.clear()
        session["student_id"] = student_id
        return redirect(url_for("tests"))

    return render_template("student.html")


@app.route("/tests")
def tests():
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("student"))
    with get_db() as conn:
        selected = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    if not selected:
        session.clear()
        return redirect(url_for("student"))
    return render_template("tests.html", student=selected, themes=THEMES)


@app.post("/start/<theme_key>")
def start_test(theme_key: str):
    if theme_key not in THEMES:
        abort(404)
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("student"))
    with get_db() as conn:
        selected = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    mode = "diagnostic" if not selected["diagnostic_complete"] else "test"
    total = 12 if mode == "diagnostic" else 10
    session["active_test"] = {
        "theme_key": theme_key,
        "topic": THEMES[theme_key]["topic"],
        "mode": mode,
        "starting_difficulty": selected["current_difficulty"],
        "difficulty": selected["current_difficulty"],
        "total_questions": total,
        "current_question": 0,
        "correct": 0,
        "answers": [],
        "started_at": time.time(),
        "question_started_at": time.time(),
    }
    return redirect(url_for("question"))


@app.route("/question", methods=["GET", "POST"])
def question():
    active = session.get("active_test")
    if not active:
        return redirect(url_for("tests"))

    feedback = None
    if request.method == "POST":
        submitted = request.form.get("answer", "")
        elapsed = max(0.1, time.time() - active["question_started_at"])
        expected = active["question"]["answer"]
        correct = submitted == expected
        if correct:
            active["correct"] += 1

        active["answers"].append({
            "question_number": active["current_question"] + 1,
            "topic": active["question"]["topic"],
            "difficulty": active["difficulty"],
            "prompt": active["question"]["prompt"],
            "expected_answer": expected,
            "submitted_answer": submitted,
            "is_correct": correct,
            "seconds": round(elapsed, 2),
        })
        active["current_question"] += 1

        recent = active["answers"][-3:]
        if len(recent) == 3 and all(item["is_correct"] for item in recent):
            active["difficulty"] = min(5, active["difficulty"] + 1)
        elif len(recent) == 3 and sum(item["is_correct"] for item in recent) <= 1:
            active["difficulty"] = max(1, active["difficulty"] - 1)

        if active["current_question"] >= active["total_questions"]:
            session["active_test"] = active
            return redirect(url_for("finish"))

        feedback = "Correct!" if correct else f"The correct answer was: {expected}"

    active["question"] = make_question(active["topic"], active["difficulty"])
    active["question_started_at"] = time.time()
    session["active_test"] = active

    return render_template(
        "question.html",
        active_test=active,
        theme=THEMES[active["theme_key"]],
        feedback=feedback,
    )


@app.route("/finish")
def finish():
    active = session.get("active_test")
    student_id = session.get("student_id")
    if not active or not student_id:
        return redirect(url_for("home"))
    if active.get("saved_session_id"):
        return redirect(url_for("result", session_id=active["saved_session_id"]))

    attempted = active["total_questions"]
    correct = active["correct"]
    raw = round(correct / attempted * 100, 1)
    seconds = round(time.time() - active["started_at"], 1)
    average_seconds = round(seconds / attempted, 2)
    avg_difficulty = sum(a["difficulty"] for a in active["answers"]) / attempted
    difficulty_score = avg_difficulty / 5 * 100
    speed_score = max(0, min(100, 100 - max(0, average_seconds - 15) * 2))
    consistency = 100 - (
        max(a["difficulty"] for a in active["answers"])
        - min(a["difficulty"] for a in active["answers"])
    ) * 10
    mastery = round(max(0, min(
        100,
        raw * .60 + difficulty_score * .20 + speed_score * .10 + consistency * .10
    )), 1)

    with get_db() as conn:
        selected = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
        theme = THEMES[active["theme_key"]]
        status = mastery_status(mastery, active["difficulty"], selected["grade_level"])
        cursor = conn.execute("""
            INSERT INTO test_sessions(
                student_id, game_name, theme_key, theme_name, topic,
                standard_code, mode, grade_level, starting_difficulty,
                ending_difficulty, questions_attempted, questions_correct,
                raw_percent, letter_grade, mastery_score, mastery_status,
                seconds, average_seconds, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id, APP_NAME, active["theme_key"], theme["name"],
            active["topic"], theme["standard"], active["mode"],
            selected["grade_level"], active["starting_difficulty"],
            active["difficulty"], attempted, correct, raw,
            grade_letter(raw), mastery, status, seconds, average_seconds, now_text()
        ))
        saved_id = cursor.lastrowid

        for item in active["answers"]:
            conn.execute("""
                INSERT INTO test_answers(
                    session_id, question_number, topic, difficulty, prompt,
                    expected_answer, submitted_answer, is_correct, seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                saved_id, item["question_number"], item["topic"],
                item["difficulty"], item["prompt"], item["expected_answer"],
                item["submitted_answer"], int(item["is_correct"]), item["seconds"]
            ))

        conn.execute("""
            UPDATE students
            SET current_difficulty=?,
                diagnostic_complete=CASE WHEN ?='diagnostic' THEN 1 ELSE diagnostic_complete END,
                updated_at=?
            WHERE id=?
        """, (active["difficulty"], active["mode"], now_text(), student_id))

    active["saved_session_id"] = saved_id
    session["active_test"] = active
    return redirect(url_for("result", session_id=saved_id))


@app.route("/result/<int:session_id>")
def result(session_id: int):
    with get_db() as conn:
        result_row = conn.execute("""
            SELECT ts.*, s.name, s.age
            FROM test_sessions ts
            JOIN students s ON s.id=ts.student_id
            WHERE ts.id=?
        """, (session_id,)).fetchone()
        answers = conn.execute("""
            SELECT * FROM test_answers
            WHERE session_id=?
            ORDER BY question_number
        """, (session_id,)).fetchall()
    if not result_row:
        abort(404)
    return render_template("result.html", result=result_row, answers=answers)


@app.route("/parent/login", methods=["GET", "POST"])
def parent_login():
    if request.method == "POST":
        pin = request.form.get("pin", "")
        with get_db() as conn:
            saved = conn.execute(
                "SELECT value FROM settings WHERE key='parent_pin_hash'"
            ).fetchone()
        if saved and check_password_hash(saved["value"], pin):
            session["parent_authenticated"] = True
            return redirect(request.args.get("next") or url_for("parent_dashboard"))
        flash("Incorrect parent PIN.", "error")
    return render_template("parent_login.html")


@app.route("/parent/logout")
def parent_logout():
    session.pop("parent_authenticated", None)
    return redirect(url_for("home"))


@app.route("/parent")
@parent_required
def parent_dashboard():
    selected_id = request.args.get("student_id", type=int)
    with get_db() as conn:
        students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
        summaries = conn.execute("""
            SELECT s.id, s.name, s.age, s.grade_level, s.current_difficulty,
                   COUNT(ts.id) tests_taken,
                   ROUND(AVG(ts.raw_percent),1) average_score,
                   ROUND(AVG(ts.mastery_score),1) average_mastery,
                   MAX(ts.timestamp) last_test
            FROM students s
            LEFT JOIN test_sessions ts ON ts.student_id=s.id
            GROUP BY s.id ORDER BY s.name
        """).fetchall()

        query = """
            SELECT ts.*, s.name, s.age
            FROM test_sessions ts
            JOIN students s ON s.id=ts.student_id
        """
        params = []
        if selected_id:
            query += " WHERE s.id=?"
            params.append(selected_id)
        query += " ORDER BY ts.id DESC LIMIT 250"
        results = conn.execute(query, params).fetchall()

    return render_template(
        "parent.html",
        students=students,
        summaries=summaries,
        results=results,
        selected_student_id=selected_id,
    )


@app.post("/parent/student/<int:student_id>")
@parent_required
def update_student(student_id: int):
    try:
        age = int(request.form.get("age", ""))
        grade = int(request.form.get("grade_level", ""))
        difficulty = int(request.form.get("current_difficulty", ""))
    except ValueError:
        flash("Settings must be whole numbers.", "error")
        return redirect(url_for("parent_dashboard"))

    if not (5 <= age <= 19 and 1 <= grade <= 12 and 1 <= difficulty <= 5):
        flash("Settings are outside the allowed range.", "error")
        return redirect(url_for("parent_dashboard"))

    with get_db() as conn:
        conn.execute("""
            UPDATE students
            SET age=?, grade_level=?, current_difficulty=?, updated_at=?
            WHERE id=?
        """, (age, grade, difficulty, now_text(), student_id))

    flash("Student settings updated.", "success")
    return redirect(url_for("parent_dashboard", student_id=student_id))


@app.post("/parent/reset-diagnostic/<int:student_id>")
@parent_required
def reset_diagnostic(student_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE students SET diagnostic_complete=0, updated_at=? WHERE id=?",
            (now_text(), student_id)
        )
    flash("Diagnostic reset.", "success")
    return redirect(url_for("parent_dashboard", student_id=student_id))


@app.route("/parent/export")
@parent_required
def export_csv():
    headers = [
        "student_name", "student_age", "grade_level", "starting_difficulty",
        "ending_difficulty", "game_name", "theme_name", "topic", "standard_code",
        "mode", "questions_attempted", "questions_correct", "raw_percent",
        "letter_grade", "mastery_score", "mastery_status", "seconds",
        "average_seconds", "timestamp", "federation_version"
    ]
    with get_db() as conn:
        rows = conn.execute("""
            SELECT s.name student_name, s.age student_age, ts.grade_level,
                   ts.starting_difficulty, ts.ending_difficulty, ts.game_name,
                   ts.theme_name, ts.topic, ts.standard_code, ts.mode,
                   ts.questions_attempted, ts.questions_correct, ts.raw_percent,
                   ts.letter_grade, ts.mastery_score, ts.mastery_status,
                   ts.seconds, ts.average_seconds, ts.timestamp,
                   ts.federation_version
            FROM test_sessions ts
            JOIN students s ON s.id=ts.student_id
            ORDER BY ts.id DESC
        """).fetchall()

    text = io.StringIO()
    writer = csv.writer(text)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row[h] for h in headers])
    payload = io.BytesIO(text.getvalue().encode("utf-8"))
    payload.seek(0)
    return send_file(
        payload,
        as_attachment=True,
        download_name=f"ga_science_results_{datetime.now().strftime('%Y%m%d')}.csv",
        mimetype="text/csv",
    )


@app.route("/health")
def health():
    return jsonify({"ok": True, "app": APP_NAME, "database": str(DATABASE)})


@app.route("/federation/manifest")
def federation_manifest():
    return jsonify({
        "schema_version": "1.0",
        "game_slug": APP_SLUG,
        "game_name": APP_NAME,
        "database_path": str(DATABASE),
        "students_table": "students",
        "sessions_table": "test_sessions",
        "answers_table": "test_answers",
        "read_only": True,
    })


init_db()

if __name__ == "__main__":
    print()
    print(APP_NAME)
    print(f"Database: {DATABASE}")
    print("Default parent PIN: 2468")
    print()
    app.run(
        host=os.environ.get("GA_SCIENCE_HOST", "127.0.0.1"),
        port=int(os.environ.get("GA_SCIENCE_PORT", "5075")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
