# Frontlines

## Overview

**Frontlines** is a Flask-based web application designed to simulate combat interactions between military units. It uses structured unit data stored in CSV files and applies simulation logic to determine outcomes such as destruction, suppression, or survival.

This project is intended for **game design experimentation**, allowing rapid iteration of unit stats and combat mechanics without requiring a full database or complex backend.

---

## Features

* Unit vs Unit combat simulation
* Data-driven design using CSV files
* Web-based interface for quick testing
* Expandable combat logic system
* Lightweight Flask backend

---

## Tech Stack

| Layer    | Technology                     |
| -------- | ------------------------------ |
| Backend  | Python (Flask)                 |
| Frontend | HTML, CSS (Jinja2 templating)  |
| Data     | CSV files                      |
| Logic    | Python (randomised simulation) |

---

## Project Structure

```
Frontlines/
│
├── app.py                # Main Flask application and simulation logic
├── UnitValues.csv        # Core unit statistics
├── UnitSizes.csv         # Unit size modifiers
│
├── templates/
│   └── index.html        # Frontend UI
│
├── static/
│   └── styles.css        # Styling for the application
│
└── README.md             # Project documentation
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Jack-Lean-1404/Frontlines.git
cd Frontlines
```

### 2. Install dependencies

```bash
pip install flask
```

### 3. Run the application

```bash
python app.py
```

### 4. Open in browser

```
http://127.0.0.1:5000
```

---

## How It Works

### 1. Data Loading

* Unit data is stored in `UnitValues.csv`
* Additional modifiers (e.g., size) are stored in `UnitSizes.csv`
* These are loaded into Python when the app starts or when needed

---

### 2. User Interaction

* The user selects units via the web interface
* A request is sent to the Flask backend

---

### 3. Simulation Engine

The backend:

1. Retrieves unit stats
2. Applies combat rules
3. Uses randomness for variability
4. Produces an outcome

---

### 4. Output

The result is returned to the frontend and displayed to the user.

---

## Combat Outcomes

The system currently supports outcomes such as:

* **Destroyed** — Unit is eliminated
* **Suppressed** — Unit is weakened but still active
* **No Impact / Survives** — No meaningful damage

---

## Modifying the Game

### Add a New Unit

1. Open `UnitValues.csv`
2. Add a new row with appropriate stats
3. Restart the app

---

### Change Combat Balance

Modify the logic inside:

```
app.py → simulate()
```

---

### Update UI

Edit:

```
templates/index.html
static/styles.css
```

---

## Common Issues

### `NameError: app is not defined`

Ensure:

```python
app = Flask(__name__)
```

appears **before any `@app.route` decorators**

---

### CSV Not Loading

* Ensure files are in the root directory
* Check column names match expected fields

---

### Page Loads but No Units Appear

* Backend may not be passing `units` to the template
* Check `home()` route in `app.py`

---

## Design Notes

This project intentionally uses:

* CSV instead of a database (for simplicity and rapid iteration)
* A single-file backend (`app.py`) for accessibility

As the project scales, consider:

* Moving logic into modules
* Introducing a database (SQLite/PostgreSQL)
* Adding validation and testing

---

## Future Improvements

* Modular combat engine
* Unit abilities system
* Persistent storage (database)
* Multiplayer or turn-based system
* Advanced UI (React or similar)

---

## Contributing

This project is currently in active development. Contributions, refactors, and feature ideas are welcome.

---

## License

No license currently specified.
