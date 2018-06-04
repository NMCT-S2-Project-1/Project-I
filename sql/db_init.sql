	CREATE USER 'project1-admin'@'localhost' IDENTIFIED BY 'adminpassword';
	CREATE USER 'project1-web'@'localhost' IDENTIFIED BY 'webpassword';
	CREATE USER 'project1-sensor'@'localhost' IDENTIFIED BY 'sensorpassword';

	CREATE DATABASE project1;
	GRANT ALL PRIVILEGES ON project1.* to 'project1-admin'@'localhost' WITH GRANT OPTION;
	GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-web'@'localhost';
	GRANT SELECT, INSERT, UPDATE, DELETE ON project1.* TO 'project1-sensor'@'localhost';
	FLUSH PRIVILEGES;
