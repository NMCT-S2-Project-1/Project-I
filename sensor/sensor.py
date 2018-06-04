import logging
import signal
import subprocess
from time import sleep
import mysql.connector as mariadb

log = logging.getLogger(__name__)

running = True


def save_sensor_value(name, value):
    try:
        conn = mariadb.connect(database='project1', user='project1-sensor', password='sensorpassword')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sensor (name, value) VALUES (%s, %s)", (name, value))
        conn.commit()
        log.debug("Saved sensor {}={} to database".format(name, value))
        return True
    except Exception as e:
        log.exception("DB update failed: {!s}".format(e))


def setup():
    def shutdown(*args):
        global running
        running = False
        # try:
        #     sys.exit(0)
        # except KeyError as ex:
        #     pass

    signal.signal(signal.SIGTERM, shutdown)


def loop():
    count = subprocess.check_output("/bin/ps aux | wc -l", shell=True)
    save_sensor_value("process_count", count)
    sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        setup()
        while running:
            loop()
    except KeyboardInterrupt:
        pass
