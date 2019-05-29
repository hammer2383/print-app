import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask_uploads import patch_request_class

# import atexit
# from apscheduler.schedulers.background import BackgroundScheduler


from flask_script import Manager, Server
from application import create_app
# from utilities.journal import print_date_time

app = create_app()
#file's size limit
patch_request_class(app, size=41943040)
manager = Manager(app)

# scheduler = BackgroundScheduler()
# scheduler.add_job(func=print_date_time,trigger='cron', hour='0')
# scheduler.start()

host = os.environ.get('IP', '127.0.0.1')
port = int(os.environ.get('PORT', 5000))

manager.add_command("runserver",Server(
    use_debugger=True,
    use_reloader=True,
    host=host,
    port=port
    ))

if __name__ == "__main__":
    manager.run()
