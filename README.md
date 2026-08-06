# Georgia Science Testing Program

Adaptive science assessment modeled after the Fraction & Ratio Testing Program.

## Core focus

Georgia Grade 7 life science:

- S7L1 Classification
- S7L2 Cells and levels of organization
- S7L3 Genetics, heredity, and reproduction
- S7L4 Ecology and ecosystems
- S7L1-S7L5 Mixed review
- Science and engineering practices

## Features

- Student name, age, and grade entry
- Adaptive diagnostic
- Five difficulty levels
- Multiple-choice assessment
- Automatic letter grade
- Mastery score
- Answer review
- Parent PIN portal
- CSV export
- Separate SQLite database
- Federation-ready schema
- Mac testing setup
- Pop!_OS desktop installer
- Custom science laboratory logo

## Database

    ~/KIDS-HW/grades/ga_science_testing_program/ga_science_testing_program.db

## Default parent PIN

    2468

Set another PIN before the first run:

    export GA_SCIENCE_PARENT_PIN="YOUR-PIN"

## Test on macOS

    chmod +x *.sh
    ./install-mac.sh
    .venv/bin/python app.py

Open:

    http://127.0.0.1:5075

Parent portal:

    http://127.0.0.1:5075/parent

## Install on Pop!_OS

    chmod +x *.sh
    ./install-desktop.sh
    ./start-desktop.sh

Search the application menu for:

    Georgia Science Testing Program

## Federation manifest

    http://127.0.0.1:5075/federation/manifest

## Health check

    curl http://127.0.0.1:5075/health
