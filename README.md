# Project I
Voorbeeld voor Project I

## Raspberry Pi

1. Packages installeren
```console 
me@my-rpi:~ $ sudo apt update 
me@my-rpi:~ $ sudo apt install -y python3-venv python3-pip python3-mysqldb mariadb-server uwsgi nginx uwsgi-plugin-python3 rabbitmq-server
```

> Vervang als je wil mariadb-server door mysql-server. In wat volgt moet je dan ook telkens mariadb vervangen door mysql.

2. Database setup
```console 
me@my-rpi:~ $ sudo mariadb
```
  1. Users aanmaken
```mysql
CREATE USER 'project1-admin'@'localhost' IDENTIFIED BY 'adminpassword';
CREATE USER 'project1-web'@'localhost' IDENTIFIED BY 'webpassword';
CREATE USER 'project1-sensor'@'localhost' IDENTIFIED BY 'sensorpassword';
```
  2. Database aanmaken & rechten toekennen
```mysql
CREATE DATABASE project1;
GRANT ALL PRIVILEGES ON project1.* to 'project1-admin'@'localhost' WITH GRANT OPTION;
GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-web'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-sensor'@'localhost';
FLUSH PRIVILEGES;
```
	
3. Virtual environment 
```console 
me@my-rpi:~ $ python3 -m pip install --upgrade pip setuptools wheel virtualenv
me@my-rpi:~ $ mkdir project1 && cd project1
me@my-rpi:~/project1 $ python3 -m venv --system-site-packages env
me@my-rpi:~/project1 $ source env/bin/activate
(env)me@my-rpi:~/project1 $ python -m pip install mysql-connector-python argon2-cffi Flask Flask-HTTPAuth Flask-MySQL mysql-connector-python passlib celery
```

4. Services
```console 
me@my-rpi:~/project1 $ sudo cp conf/project1-*.service /etc/systemd/system/
me@my-rpi:~/project1 $ sudo systemctl daemon-reload
me@my-rpi:~/project1 $ sudo systemctl start project1-flask.service
me@my-rpi:~/project1 $ sudo systemctl status project1-flask.service
● project1-flask.service - uWSGI instance to serve project1 web interface
   Loaded: loaded (/etc/systemd/system/project1-flask.service; disabled; vendor preset: enabled)
   Active: active (running) since Mon 2018-06-04 13:14:56 CEST; 1s ago
 Main PID: 6618 (uwsgi)
    Tasks: 6 (limit: 4915)
   CGroup: /system.slice/project1-flask.service
           ├─6618 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini
           ├─6620 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini
           ├─6621 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini
           ├─6622 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini
           ├─6623 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini
           └─6624 /usr/bin/uwsgi --ini /home/seb/project1/conf/uwsgi-flask.ini

Jun 04 13:14:56 my-rpi uwsgi[6618]: mapped 383928 bytes (374 KB) for 5 cores
Jun 04 13:14:56 my-rpi uwsgi[6618]: *** Operational MODE: preforking ***
me@my-rpi:~/project1 $ sudo systemctl start project1-sensor.service
me@my-rpi:~/project1 $ sudo systemctl status project1-sensor.service
● project1-sensor.service - Project 1 sensor service
   Loaded: loaded (/etc/systemd/system/project1-sensor.service; disabled; vendor preset: enabled)
   Active: active (running) since Mon 2018-06-04 13:16:49 CEST; 5s ago
 Main PID: 6826 (python)
    Tasks: 1 (limit: 4915)
   CGroup: /system.slice/project1-sensor.service
           └─6826 /home/seb/project1/env/bin/python /home/seb/project1/sensor/sensor.py

Jun 04 13:16:49 my-rpi systemd[1]: Started Project 1 sensor service.
Jun 04 13:16:49 my-rpi python[6826]: DEBUG:__main__:Saved sensor process_count=b'217\n' to database
Jun 04 13:16:55 my-rpi python[6826]: DEBUG:__main__:Saved sensor process_count=b'218\n' to database

5. nginx
me@my-rpi:~/project1 $ ls -l /etc/nginx/sites-*
/etc/nginx/sites-available:
total 4
-rw-r--r-- 1 root root 2416 Jul 12  2017 default

/etc/nginx/sites-enabled:
total 0
lrwxrwxrwx 1 root root 34 Jan 18 13:25 default -> /etc/nginx/sites-available/default
me@my-rpi:~/project1 $ sudo rm /etc/nginx/sites-enabled/default
me@my-rpi:~/project1 $ sudo cp conf/nginx /etc/nginx/sites-available/project1
me@my-rpi:~/project1 $ sudo ln -s /etc/nginx/sites-available/project1 /etc/nginx/sites-enabled/project1
me@my-rpi:~/project1 $ sudo systemctl restart nginx.service
me@my-rpi:~/project1 $ sudo systemctl status nginx.service
● nginx.service - A high performance web server and a reverse proxy server
   Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
   Active: active (running) since Mon 2018-06-04 13:21:31 CEST; 23s ago
     Docs: man:nginx(8)
  Process: 7187 ExecStop=/sbin/start-stop-daemon --quiet --stop --retry QUIT/5 --pidfile /run/nginx.pid (code=exited, status=0/SUCCE
  Process: 7193 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
  Process: 7191 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
 Main PID: 7195 (nginx)
    Tasks: 3 (limit: 4915)
   CGroup: /system.slice/nginx.service
           ├─7195 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
           ├─7196 nginx: worker process
           └─7197 nginx: worker process

Jun 04 13:21:30 my-rpi systemd[1]: Starting A high performance web server and a reverse proxy server...
Jun 04 13:21:31 my-rpi systemd[1]: Started A high performance web server and a reverse proxy server.

me@my-rpi:~/project1 $ wget localhost -q -O -
Hello, World!
me@my-rpi:~/project1 $
me@my-rpi:~/project1 $
me@my-rpi:~/project1 $
