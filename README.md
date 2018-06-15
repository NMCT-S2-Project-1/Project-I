# Project I startproject
Voorbeeld voor Project I

## Voorbereiding
Beginsituatie: idem labo Datacom, zie zo nodig  <https://github.com/NMCT-S2-DataCom1/DataCommunication-I-student/blob/master/syllabus/setup.md#0-prerequisites> voor instructies.

### Packages installeren
```console
me@my-rpi:~ $ sudo apt update
me@my-rpi:~ $ sudo apt install -y python3-venv python3-pip python3-mysqldb mariadb-server uwsgi nginx uwsgi-plugin-python3
```
> Vervang als je wil *mariadb-server* door *mysql-server*. In wat volgt moet je dan ook telkens `mariadb` vervangen door `mysql`. Beide zijn functioneel quasi identiek en ook hun tools zijn onderling grotendeels compatibel.

### Virtual environment
```console
me@my-rpi:~ $ python3 -m pip install --upgrade pip setuptools wheel virtualenv
me@my-rpi:~ $ mkdir project1 && cd project1
me@my-rpi:~/project1 $ python3 -m venv --system-site-packages env
me@my-rpi:~/project1 $ source env/bin/activate
(env)me@my-rpi:~/project1 $ python -m pip install mysql-connector-python argon2-cffi Flask Flask-HTTPAuth Flask-MySQL mysql-connector-python passlib
```

### Startproject clonen
- Ga naar `VCS > Import from Version Control > GitHub` en clone het startproject (dit dus - <https://github.com/NMCT-S2-Project-I/Project-I.git>).
- Stel de deployment config in voor de directory die je daarnet gemaakt hebt, bv. `/home/me/project1`. **Klik op Apply!**
- Ga naar de interpreter settings en configureer/kies het virtual environment dat je net gemaakt hebt, bv. `/home/me/project1/env/bin/python`.
- Check dat onder de interpreter het veld `Path mapping` ingevuld is en naar de juiste directory verwijst.
- Upload nu de hele boel vanuit PyCharm naar de Pi en verifieer; het zou er nu zo moeten uitzien:

```console
me@my-rpi:~ $ ls -l project1/
total 20
drwxr-xr-x 2 me me 4096 Jun  4 16:35 conf
drwxr-xr-x 6 me me 4096 Jun  4 15:35 env
drwxr-xr-x 2 me me 4096 Jun  4 17:51 sensor
drwxr-xr-x 2 me me 4096 Jun  4 15:42 sql
drwxr-xr-x 4 me me 4096 Jun  4 16:31 web

```

## Database

Na installatie zou MariaDB/MySQL meteen moeten draaien:

```console
me@my-rpi:~ $ sudo systemctl status mysql
● mariadb.service - MariaDB database server
   Loaded: loaded (/lib/systemd/system/mariadb.service; enabled; vendor preset: enabled)
   Active: active (running) since Sun 2018-06-03 09:41:18 CEST; 1 day 4h ago
 Main PID: 781 (mysqld)
   Status: "Taking your SQL requests now..."
    Tasks: 28 (limit: 4915)
   CGroup: /system.slice/mariadb.service
           └─781 /usr/sbin/mysqld

Jun 03 09:41:13 my-rpi systemd[1]: Starting MariaDB database server...
Jun 03 09:41:15 my-rpi mysqld[781]: 2018-06-03  9:41:15 4144859136 [Note] /usr/sbin/mysqld (mysqld 10.1.26-MariaDB-0+deb9u1)
Jun 03 09:41:18 my-rpi systemd[1]: Started MariaDB database server.

me@my-rpi:~ $ ss -lt | grep mysql
LISTEN     0      80     127.0.0.1:mysql                    *:*        

```
**Merk op dat MariaDB/MySQL enkel luistert op 127.0.0.1 en dus niet bereikbaar is vanaf het netwerk!** Je zou dit kunnen veranderen in de configuratie, maar security-gewijs is dat niet het beste idee. In de plaats zullen we PyCharm verbinden via SSH.

### Users + database aanmaken &amp; rechten toekennen

Omdat er voorlopig geen SQL users zijn, moet je **eenmalig** de client starten als root:

```console
me@my-rpi:~ $ sudo mariadb
```
en dan...

```mysql
CREATE USER 'project1-admin'@'localhost' IDENTIFIED BY 'adminpassword';
CREATE USER 'project1-web'@'localhost' IDENTIFIED BY 'webpassword';
CREATE USER 'project1-sensor'@'localhost' IDENTIFIED BY 'sensorpassword';

CREATE DATABASE project1;

GRANT ALL PRIVILEGES ON project1.* to 'project1-admin'@'localhost' WITH GRANT OPTION;
GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-web'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-sensor'@'localhost';
FLUSH PRIVILEGES;
```

*For the lazy:* Bovenstaande SQL-statements staan ook in [sql/db_init.sql](sql/db_init.sql), dus:

```console
me@my-rpi:~/project1 $ sudo mariadb < sql/db_init.sql
```

### Connectie via PyCharm
- Klik op de tab `Database` langs de rechterkant (geen tab? Menu `View > Tool Windows > Database`) en klik op de groene + om een connectie toe te voegen.
- Kies `Data Source > MySQL` en klik (indien aanwezig) alvast op de link `Download driver` onderaan.
- Ga eerst naar de tab `SSH/SSL` en vink `SSH` aan. Vul aan met de gegevens (host/user/password) **die je anders voor PuTTY gebruikt**. Als `port` nog niet is ingevuld moet je daar *22* zetten. Check `Remember password`.
- Keer terug naar tabblad `General` en vul de gegevens voor de database aan:
  - `Host` blijft *localhost* (want verbonden via SSH)
  - `Database` is *project1* in dit voorbeeld
  - Gebruik de credentials van *project1-admin* en klik op `Test Connection`
- Als de verbinding OK is ga je naar tab `Schemas` en zorg je dat enkel *project1* is aangevinkt. Eventueel moet je eerst refreshen.
- Verander tenslotte `Name` in iets logischer, bv. *project1@rpi-ssh* en klik op OK.

### Tabellen voor de voorbeeldcode
Het voorbeeld maakt gebruik van twee tabellen waarvan een dump te vinden is in [users.sql](sql/users.sql) en [sensor.sql](sql/sensor.sql). Herhaal voor *beide* bestanden:
- Rechterklik --> `Run <file>.sql`
- Vink de connectie die je net maakte **en de database** (project1) aan en bevestig.

Na afloop zou je beide tabellen moeten moeten terugvinden in de database:
```console
me@my-rpi:~ $ echo 'show tables;' | mysql project1 -t -u project1-admin -p
Enter password:
+--------------------+
| Tables_in_project1 |
+--------------------+
| sensor             |
| users              |
+--------------------+
```

## configuratiebestanden
In de directory [conf](conf/) vind je 4 bestanden **die je eerst nog moet aanpassen** en vervolgens op de juiste plaats zetten.

*For the lazy:* **Minimaal** moet je overal de gebruikersnaam en overeenkomstige homedirectory aanpassen in alle bestanden. Dat kan in een klap met:
```console
me@my-rpi:~/project1 $ sed -i s/seb/$USER/g conf/*
```

### uWSGI
In [uwsgi-flask.ini](conf/uwsgi-flask.ini) zit de config voor uWSGI:
- de parameter `module` verwijst naar de Flask-applicatie. Vóór de `:` staat de bestandsnaam, erachter de naam van het object. In het voorbeeld vind je in [web.py](web/web.py) de regel `app = Flask()`, dus dat wordt dan `module = web:app`
- `virtualenv` spreekt hopelijk voor zich
- de rest zou zo juist moeten zijn en het bestand mag blijven staan waar het staat

### systemd
De twee `.service` bestanden zijn unit-files voor `systemd`. Naast de `Description` moet je de 4 parameters onder `[Service]` aanpassen aan jouw situatie. Let op dat je het de juiste Python-interpreter (in virtualenv dus) gebruikt en steeds absolute paden (beginnend vanaf `/`)

Vervolgens kan je de bestanden op hun plaats zetten in `/etc/systemd/system/`. Daarna moet je systemd daarover informeren met een `daemon-reload` en kan je ze (hopelijk) starten:

```console
me@my-rpi:~/project1 $ sudo cp conf/project1-*.service /etc/systemd/system/
me@my-rpi:~/project1 $ sudo systemctl daemon-reload
me@my-rpi:~/project1 $ sudo systemctl start project1-*
me@my-rpi:~/project1 $ sudo systemctl status project1-*
● project1-flask.service - uWSGI instance to serve project1 web interface
   Loaded: loaded (/etc/systemd/system/project1-flask.service; disabled; vendor preset: enabled)
   Active: active (running) since Mon 2018-06-04 13:14:56 CEST; 1s ago
 Main PID: 6618 (uwsgi)
    Tasks: 6 (limit: 4915)
   CGroup: /system.slice/project1-flask.service
           ├─6618 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
           ├─6620 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
           ├─6621 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
           ├─6622 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
           ├─6623 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
           └─6624 /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini

Jun 04 13:14:56 my-rpi uwsgi[6618]: mapped 383928 bytes (374 KB) for 5 cores
Jun 04 13:14:56 my-rpi uwsgi[6618]: *** Operational MODE: preforking ***

● project1-sensor.service - Project 1 sensor service
   Loaded: loaded (/etc/systemd/system/project1-sensor.service; disabled; vendor preset: enabled)
   Active: active (running) since Mon 2018-06-04 13:16:49 CEST; 5s ago
 Main PID: 6826 (python)
    Tasks: 1 (limit: 4915)
   CGroup: /system.slice/project1-sensor.service
           └─6826 /home/me/project1/env/bin/python /home/me/project1/sensor/sensor.py

Jun 04 13:16:49 my-rpi systemd[1]: Started Project 1 sensor service.
Jun 04 13:16:49 my-rpi python[6826]: DEBUG:__main__:Saved sensor process_count=b'217\n' to database
Jun 04 13:16:55 my-rpi python[6826]: DEBUG:__main__:Saved sensor process_count=b'218\n' to database
```
> Eventueel meermaals op `q` duwen om terug op de console te geraken

## nginx
In het bestand [nginx](conf/nginx) moet je enkel de parameter `uwsgi_pass` nog aanpassen, die verwijst naar de *socket* die uWSGI aanmaakt. Het volledige pad wordt gevormd door de combinatie van de parameters `WorkingDirectory` in [project1-flask.service](conf/project1-flask.service) en `socket` in [uwsgi-flask.ini](conf/uwsgi-flask.ini).

In `/etc/nginx` is er een directory `sites-available` voor configuraties die je dan kan activeren door er een symlink naar te leggen in `sites-enabled`:

```console
me@my-rpi:~/project1 $ ls -l /etc/nginx/sites-*
/etc/nginx/sites-available:
total 4
-rw-r--r-- 1 root root 2416 Jul 12  2017 default

/etc/nginx/sites-enabled:
total 0
lrwxrwxrwx 1 root root 34 Jan 18 13:25 default -> /etc/nginx/sites-available/default
```

Om deze *default* te deactiveren en vervangen door onze eigen config moeten we dus:
 - `conf/nginx` naar `*`sites-available* kopiëren (en in passant een duidelijkere naam geven)
 - de link naar de default-config weghalen
 - linken naar de nieuwe config
 - nginx herstarten om de wijzigingen te activeren

```console
me@my-rpi:~/project1 $ sudo cp conf/nginx /etc/nginx/sites-available/project1
me@my-rpi:~/project1 $ sudo rm /etc/nginx/sites-enabled/default
me@my-rpi:~/project1 $ sudo ln -s /etc/nginx/sites-available/project1 /etc/nginx/sites-enabled/project1
me@my-rpi:~/project1 $ sudo systemctl restart nginx.service
```
Even checken of nginx het heeft overleefd...
```console
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
```
... en als alles goed is zou je nu naar je Pi moeten kunnen surfen en daar de "Hello world" van Flask zien. Of op de CLI:
```console
me@my-rpi:~/project1 $ wget -qO - localhost
Hello, World!
```

## Autostart
MariaDB en nginx starten automatisch op, je eigen services (nog) niet. **Het is waarschijnlijk makkelijkst als je dat ook zo laat tot je (ongeveer) klaar bent met je code.** Ondertussen blijf je gewoon verder debuggen op poort 5000 (om daar vanaf je PC aan te kunnen, moet je Flask starten met argument `host='0.0.0.0`).

Op het eind moet je dan enkel je services nog activeren in *systemd*...
```console
me@my-rpi:~/project1 $ sudo systemctl enable project1-*
```
... en checken of na een reboot effectief alles goed werkt.


# Troubleshooting 

## General

- Met `journalctl` kan je in de logfiles kijken. Daar komt ook stdout in terecht (eventuele console output/foutboodschappen/stack traces) van je services/scripts terecht.
- Die logs komen uit de *syslog* en die kan je live volgen met `tail -f /var/log/syslog'
- Met `ss -ltn` kan je zien op welke TCP-poorten geluisterd wordt/services draaien. *:123 wil zeggen elk IPv4 adres, [::]:123 hetzelfde maar voor IPv4+IPv6, 127.0.0.1:123 wil zeggen ENKEL toegankelijk vanop de pi zelf/via SSH.

## Nginx

**Configuratie testen:**
```console
me@my-rpi:~ $ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
**Address already in use** in de log en/of `systemctl status`: Er draait al iets op poort 80! Wellicht een apache2 httpd die we bij CNW eens geïnstalleerd hebben. `systemctl {stop|disable}` om uit te zetten, `apt purge apache2` voor uninstall.

**HTTP/502 Bad Gateway**: nginx geraakt niet tot bij uWSGI -> draait de flask service wel? Klopt het socket-bestand in de nginx-config? (Dubbel)check of dat bestand wel bestaat en doe dat m.b.v. een copy/paste van het pad uit de config. 

**Welcome to nginx** startpagina in je browser? `default` config van nginx is nog actief i.p.v. de jouwe - heb je de config goed gezet in `sites-available` EN ernaar gelinkt in `sites-enabled`?

## systemd/services
**CHROOT** wil zeggen dat `WorkingDirectory` niet klopt/bestaat.
**EXEC** wil zeggen dat `ExecStart` niet klopt/bestaat/meteen crashed.
**zagen over mysqld** betekent dat je ofwel geen mysql hebt, of meer waarschijnlijk dat die om de een of andere een andere naam heeft
Debugging, a.k.a. **doe eens stap-voor-stap want systemd probeert en zie waar het fout gaat:** 
```console
me@my-rpi:~ $ systemctl status project1-flask
● project1-flask.service - uWSGI instance to serve project1 web interface
   Loaded: loaded (/etc/systemd/system/project1-flask.service; enabled; vendor preset: enabled)
   Active: failed (Result: signal) since Thu 2018-06-14 20:51:03 CEST; 3h 1min ago
  Process: 6137 ExecStart=/usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini (code=killed, signal=ABRT)
 Main PID: 6137 (code=killed, signal=ABRT)
#	[...]
	
# COPY/PASTE de unit file van op de regel die begint met 'Loaded:'...
me@my-rpi:~ $ cat /etc/systemd/system/project1-flask.service
#	[...]
[Service]
User=me
Group=www-data
WorkingDirectory=/home/me/project1/web
ExecStart=/usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini
#	[...]
me@my-rpi:~ $ su - me							# User=me
me@my-rpi:~ $ cd /home/me/project1/web			# WorkingDirectory=/home/me/project1/web
me@my-rpi:~/project1/web $ /usr/bin/uwsgi --ini /home/me/project1/conf/uwsgi-flask.ini 
# Die laatste is de VOLLEDIGE regel die volgt op ExecStart

```
