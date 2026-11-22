const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'pbn_matrix.db');
const db = new sqlite3.Database(dbPath);

console.log("Reading sites database...");

db.all("SELECT * FROM sites", [], (err, rows) => {
    if (err) {
        console.error("Error:", err);
    } else {
        console.log("Sites found:", rows.length);
        console.log(JSON.stringify(rows, null, 2));
    }
    
    db.all("SELECT * FROM activity_log ORDER BY id DESC LIMIT 20", [], (err2, logs) => {
        if (err2) {
            console.error("Error logs:", err2);
        } else {
            console.log("\nActivity Log (latest 20):");
            console.log(JSON.stringify(logs, null, 2));
        }
        db.close();
    });
});
