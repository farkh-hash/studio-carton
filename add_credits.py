import sqlite3
db_path = "C:/data/studio_carton.db"
conn = sqlite3.connect(db_path)
conn.execute("UPDATE users SET credits=100, is_pro=1 WHERE email='moad.farkh2015@gmail.com'")
conn.commit()
cur = conn.execute("SELECT email, credits, is_pro FROM users")
for row in cur.fetchall():
    print(f"User: {row[0]} | Credits: {row[1]} | Pro: {row[2]}")
conn.close()
print("Done")
