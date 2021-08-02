# Resume
### Top Skills
<img src="https://img.shields.io/badge/Lang-Python-blue" height="20" alt="Python" > <img src="https://img.shields.io/badge/Lang-SQL-blue" height="20" alt="SQL" > <img src="https://img.shields.io/badge/Package-Pandas-add8e6" height="20" alt="Pandas" > <img src="https://img.shields.io/badge/Package-Numpy-add8e6" height="20" alt="Numpy" >  <img src="https://img.shields.io/badge/Package-Matplotlib-add8e6" height="20" alt="Matplotlib" > <img src="https://img.shields.io/badge/Package-SciPy-add8e6" height="20" alt="SciPy" > <img src="https://img.shields.io/badge/system-Docker-brightgreen" height="20" alt="Docker" > <img src="https://img.shields.io/badge/system-Postgres-brightgreen" height="20" alt="Postgres" > <img src="https://img.shields.io/badge/system-Linux-brightgreen" height="20" alt="Linux" >
## Summary

This repo includes snippets of code I've created over the past 2 years. The major of this code is made to handle complex automations for running a smart home and 
analyzing data gathered from said home. The full repository for my home automation includes over 156 running applications and is kept private for security and privacy reasons (for example my entire security system for my house is written in python.)


## Languages Used
 + [Python](https://docs.python.org/ "Python Docs")
 + [SQL](https://en.wikipedia.org/wiki/SQL "SQL wiki")
 + [YAML](https://en.wikipedia.org/wiki/YAML "YAML wiki")  
 + [Javascript](https://devdocs.io/javascript/ "Javascript Devdocs") 
 + [HTML](https://en.wikipedia.org/wiki/HTML "HTML wiki")
 + [CSS](https://en.wikipedia.org/wiki/Cascading_Style_Sheets "CSS wiki")
 + [Groovy](http://www.groovy-lang.org/ "Groovy") 
 + [C](https://devdocs.io/c/ "C Devdocs") 
 + [C++](https://devdocs.io/cpp/ "C++ Devdocs") 

## Technology Used
 + [Docker](https://www.docker.com/ "Docker")
 + [MQTT](https://mqtt.org/ "MQTT")
 + [Zwave](https://en.wikipedia.org/wiki/Z-Wave "Zwave")
 + [SciPy](https://www.scipy.org/ "SciPy Pack")
 + [Selenium](https://www.selenium.dev/ "Selenium Docs")
 + [TensorFlow](https://www.tensorflow.org/ "Tensorflow")
 + [Cython](https://docs.cython.org/en/latest/ "Cython")
 + Linux



## Databases

First databases used was a combination of [MariaDB](https://mariadb.org/ "MariaDB") and [yaml files](https://pypi.org/project/PyYAML/ "YAML Package"). MariaDB had many limitations,  and I almost gave up on SQL databases in favor of nonSQL databases like [MongoDB](https://www.mongodb.com/ "MongoDB") which is incredibly easy to use and works well with most python coding styles. I then found [PostgreSQL](https://www.postgresql.org/ "PostgreSQL"). PostgreSQL has many advanced features which overcome the normal limitations of other SQL databases. For example, Postgres easily handles the storing of [arrays](https://www.postgresql.org/docs/13/arrays.html "Array Data Type") and [json](https://www.postgresql.org/docs/13/datatype-json.html "JSON Data Type"). While table joins are great for organizing data, I've come across several use cases for storing shorter more complex arrays as a cleaner and more pythonic way to analyze data.

I also use [InfluxDB](https://www.influxdata.com/ "InfluxDB"). InfluxDB is written in [GO](https://golang.org/) and is great for storing large amounts of time series data for long term use. Combined with systems like [Grafana](https://grafana.com/) it can be an excellent way to easily visualize data. I use InfluxDB and Grafana for monitoring continues changes in data as it happens. For indebt analyzing of that data I still prefer the [SciPy](https://www.scipy.org/ "SciPy Pack") pack.

### Databases used
+ [SQlight](https://sqlite.org/index.html "SQlight")
+ [MySQL](https://www.mysql.com/ "MySQL")
+ [MariaDB](https://mariadb.org/ "MariaDB")
+ [MongoDB](https://www.mongodb.com/ "MongoDB")
+ [PostgreSQL](https://www.postgresql.org/ "PostgreSQL")
+ [InfluxDB](https://www.influxdata.com/ "InfluxDB")



## Highlights

### Systems Created

+ System for managing, controlling, and tracking environmental systems like the air conditioning. Monitors temperature, humidity, energy consumption, sun movement, luminance, and ultraviolet. Adjust temperature based on occupancy and anticipated need. 

+ Security System that uses detection of wifi and bluetooth, motion, and visual machine learning from [TensorFlow](https://www.tensorflow.org/).

+ System for tracking tasks that need to be done with an economic feedback point system. Analyzes and attempts to motivate occupants.

+ Complex system for tracking movement of personnel from room to room. Adjusts lights and notifications as needed.

+ Notification system across various platforms including area announcement, email, http, and mobile.

+ Lighting effects and automation.


### Task Tracking System


This system tracks tasks and analyzes the performance of those preforming the task. To the best of my knowledge this system is completely unique and shows high levels and innovation and creativity.



#### Task Tracking Front End
![Task Front End](https://github.com/Travis-Prall/resume/blob/main/pics/chore_front_end.png "Task Front End")
####Task Tracking Data
![Chore Data Graph](https://github.com/Travis-Prall/resume/blob/main/pics/chore_data.png "Chore Data")
####Task List
![Task List](https://github.com/Travis-Prall/resume/blob/main/pics/chore_list.png "Task List")


### Air Conditioning Data


This graph is data webscraped from APS using selenium. The data is stored in PostgresDB and then displayed in Grafana. This graph allows for instant visualization of the efficiency of my programs running my AC units.


![Grafana](https://github.com/Travis-Prall/resume/blob/main/pics/grafana_ac_data.png "Grafana AC Graph")
