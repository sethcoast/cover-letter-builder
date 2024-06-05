from app import create_app

app, celery = create_app()

if __name__ == '__main__':
    app.run(debug=True, port='5001')