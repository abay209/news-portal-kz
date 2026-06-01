from app import create_app
app = create_app()

if __name__ == '__main__':
    # В Windows для продакшена лучше использовать waitress (указано в requirements.txt)
    # Но для разработки можно обычный flask run
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
