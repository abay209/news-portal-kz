from app import create_app
from rss_parser import fetch_rss_feeds
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = create_app()

# Initialize Scheduler
scheduler = BackgroundScheduler()
# Запуск парсера сразу при старте
scheduler.add_job(func=fetch_rss_feeds, trigger="date")
# Затем каждые 30 минут
scheduler.add_job(func=fetch_rss_feeds, trigger="interval", minutes=30)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # В Windows для продакшена лучше использовать waitress (указано в requirements.txt)
    # Но для разработки можно обычный flask run
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
