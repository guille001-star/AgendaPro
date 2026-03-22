from app import create_app, db
app = create_app()
with app.app_context():
    try: db.create_all(); print(">>> DB OK")
    except: pass
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
