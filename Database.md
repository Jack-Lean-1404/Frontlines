# Database Documentation

## Database Hierarchy
The database system is structured in a simple hierarchical format, consisting of a connection, a primary database, and its tables.

## Database Environment

The MySQL connection is configured under the name:

- Connection Name: `Frontlines Database`

This is the saved MySQL Workbench connection profile used by developers to access the database server.

## Primary Database

Within this connection, the main database used is:

- Database Name: `frontlines`

All data for the website is stored within this database.

## Tables
The `frontlines` database contains all standard relational tables. These tables store and organise the app data.

## Structure Overview
```text
Frontlines Database (Connection)
└── frontlines (Database)
    ├── Units
    ├── Nations
    ├── Other Tables...
```

## Add or Delete Data from Tables
1. Click on the arrow next to `frontlines` on the left hand side of the screen under the SCHEMAS heading
2. Click on the arrow next to `Tables` 
3. Click the table icon that appears when hovering over the table name.
4. Either edit the table directly at the bottom of the screen or run SQL scripts to modify the data.  


`Be careful when editing or deleting live data, as changes are applied immediately to the database.`