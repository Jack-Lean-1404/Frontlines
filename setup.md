# Frontlines Webapp – Beginner Setup Guide

This guide is written for someone who has never used the Command Prompt (CMD), terminal, Git, or Python before.

By the end of this guide, you will have the Frontlines project running on your computer.

---

# What You Are Doing

You are going to:

1. Install the software needed for the project
2. Download the project from GitHub
3. Install the project files and tools
4. Start the web application on your computer

---

# Before You Start

You need:

- A Windows computer
- Internet access
- Administrator access to install software

---

# Step 1 – Install Python

Python is the programming language used for this project.

## Download Python

Go to:

https://www.python.org/downloads/

Download the newest version of Python 3.

---

## Install Python

When the installer opens:

### VERY IMPORTANT

Before clicking install:

Tick the box that says:

```text
Add Python to PATH
```

Then click:

```text
Install Now
```

Wait for installation to finish.

---

# Step 2 – Install Git

Git is used to download the project from GitHub.

## Download Git

Go to:

https://git-scm.com/downloads

Download Git for Windows.

---

## Install Git

During installation:

- Leave everything as default
- Keep clicking **Next**
- Click **Install**

---

# Step 3 – Install Visual Studio Code

Visual Studio Code is the program used to edit the project files.

## Download VS Code

Go to:

https://code.visualstudio.com/Download

Download the Windows version.

---

## Install VS Code

During installation:

Tick these boxes if shown:

- Add to PATH
- Open with Code

Then finish installation.

---

# Step 4 – Open Command Prompt

Command Prompt is where you type commands into your computer.

---

## How To Open Command Prompt

1. Click the Windows Start button
2. Type:

```text
cmd
```

3. Click:

```text
Command Prompt
```

A black window will open.

This is normal.

---

# Step 5 – Choose Where To Store The Project

You need a folder to keep the project.

For beginners, Desktop is easiest.

---

## Move CMD To Desktop

Copy and paste this into CMD:

```bash
cd Desktop
```

Then press:

```text
Enter
```

---

## What `cd` Means

`cd` means:

```text
change directory
```

A directory is just another word for a folder.

---

# Step 6 – Download The Frontlines Project

Now you will download the project from GitHub.

Copy and paste this into CMD:

```bash
git clone https://github.com/Jack-Lean-1404/Frontlines.git
```

Press Enter.

---

## What Is Happening?

Git is downloading all project files from GitHub onto your computer.

This may take a minute.

---

# Step 7 – Open The Project Folder

Now type:

```bash
cd Frontlines
```

Press Enter.

You are now inside the project folder.

---

# Step 8 – Install The Project Requirements

The project needs extra Python tools to work.

Copy and paste this command:

```bash
pip install -r requirements.txt
```

Press Enter.

---

## What Is `pip`?

`pip` is Python’s package installer.

It downloads and installs things the project needs.

---

# Step 9 – Install Flask

Flask is the web framework used by the project.

Copy and paste:

```bash
pip install flask
```

Press Enter.

Wait for installation to finish.

---

# Step 10 – Install MySQL Connector

This lets the project connect to the database.

Copy and paste:

```bash
pip install mysql-connector-python
```

Press Enter.

---

# Step 11 – Install Dotenv

This package loads secret settings like database passwords.

Copy and paste:

```bash
pip install python-dotenv
```

Press Enter.

---

# Step 12 – Open The Project In VS Code

While still inside CMD, type:

```bash
code .
```

Press Enter.

Visual Studio Code should open with the project loaded.

---

# Step 13 – Start The Web Application

Go back to CMD.

Make sure you are still inside the `Frontlines` folder.

Then type:

```bash
python app.py
```

Press Enter.

---

## What You Should See

You should see something similar to:

```text
Running on http://127.0.0.1:5000
```

This means the project is running successfully.

---

# Step 14 – Open The Website

Hold:

```text
CTRL
```

and click the link:

```text
http://127.0.0.1:5000
```

Your web browser will open the project.

---

# How To Stop The Project

To stop the Flask server:

1. Click the CMD window
2. Press:

```text
CTRL + C
```

The server will stop running.

---

# How To Restart The Project

If you stopped the server and want to start it again:

1. Make sure CMD is still inside the `Frontlines` folder
2. Run:

```bash
python app.py
```

---

## If You Closed CMD Completely

You will need to reopen the project folder first.

Open Command Prompt and run:

```bash
cd Desktop
cd Frontlines
python app.py
```

---

# Common Problems

## Problem: `'pip' is not recognised`

This means Python was not added to PATH during installation.

Try using:

```bash
python -m pip install -r requirements.txt
```

instead.

---

## Problem: `'git' is not recognised`

Git is either:

- not installed
- or your computer needs restarting after installation

Restart your computer and try again.

---

## Problem: VS Code Does Not Open From `code .`

Close CMD and reopen it.

If it still fails:

1. Open VS Code manually
2. Click:

```text
File → Open Folder
```

3. Select the `Frontlines` folder

---

# Commands You Will Use Often

## Open Project Folder

```bash
cd Desktop
cd Frontlines
```

---

## Start The Project
The following commands must be used inside the frontlines directory (folder)

```bash
python app.py
```

---

## Stop The Project

```text
CTRL + C
```

---

## Restart The Project

```bash
python app.py
```

---

## Download Latest Changes

```bash
git pull
```

---

# You Have Finished Setup

Your Frontlines development environment is now installed and ready to use.