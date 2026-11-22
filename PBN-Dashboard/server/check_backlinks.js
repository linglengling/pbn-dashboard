const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'pbn_matrix.db');
const db = new sqlite3.Database(dbPath);

console.log("Reading backlinks database...");

db.all("SELECT * FROM backlinks", [], (err, rows) => {
    if (err) {
        console.error("Error:", err);
    } else {
        console.log("Backlinks found:", rows.length);
        console.log(JSON.stringify(rows, null, 2));
    }
    db.close();
});
