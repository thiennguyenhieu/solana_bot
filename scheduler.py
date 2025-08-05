from apscheduler.schedulers.background import BackgroundScheduler
from main import main
import time

# Run both once immediately
main()

# Start the recurring schedule
scheduler = BackgroundScheduler(timezone='Asia/Ho_Chi_Minh')

# Schedule main bot scan every 10 mins
scheduler.add_job(main, 'interval', minutes=10)
scheduler.start()

try:
    while True:
        time.sleep(60)  # Keep the script running
except KeyboardInterrupt:
    scheduler.shutdown()
