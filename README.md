# resume
## Summary

This section includes snippets of code I've created over the past 2 years. The major of this code is made to handle complex automations for running a smart home and anylazing data gathered from said home. The full repository for my home automation includes over 156 running applications and is kept private for security and privacy reasons (for example my entire security system for my house is written in python.)

##### Systems
+ System for managing, controlling, and tracking environmental systems like the air conditining.
+ System for tracking tasks that need to be done.
+ Complex system for tracking movement of personel from room to room.
+ Notification system across variuos plateforms
+ Lighting effects and automation 


## Databases

First database used was SQLight. I then upgraded to MariaDB and using yaml. MariaDB had many limitations and I almost gave up on SQL databases in favor of nonSQL databases like MongeDB which is incredibly easy to use and works really well with most python coding styles. I then found PostgreSQL. PostgreSQL has many advanced features which overcome the normal limitations of other SQL databases. For example, Postgres easily handles the storing of arrays and json. While table joins are great for oranizing data, I've come across several use cases for storing shorter more complex arrays as a cleaner and more pythonic way to anaylze data.

I also use InfluxDB. InfluxDB is written in GO and is great for storing large amounts of time seroius data for long term use. Combined with systems like Grafana it can be an excellent way to easily visualize data. I use InfluxDB and Grafana mostly for monitoring continues changes in data as it happens. For indebt anayzing of that data I still prefere the Scipy pack.

### Databases used
+ SQLight
+ MySQL
+ MariaDB
+ MongoDB
+ PostgreSQL
+ InfluxDB



## Highlights

### Task Tracking System

This system tracks tasks and anaylzes the preformance of those preforming the task. To the best of my knowledge this system is completely unique and shows high levels and inovation and creativity.

#### Task Tracking Front End
![Task Front End](https://github.com/Travis-Prall/resume/blob/main/pics/chore_front_end.png "Task Front End")
####Task Tracking Data
![Chore Data Graph](https://github.com/Travis-Prall/resume/blob/main/pics/chore_data.png "Chore Data")
####Task List
![Task List](https://github.com/Travis-Prall/resume/blob/main/pics/chore_list.png "Task List")


### Air Conditioning Data

This graph is data webscraped from APS. The data is stored in PostgresDB and then displayed in Grafana. This graph allows for instant visualation of the effecientcy of my programs running my AC units.

![Grafana](https://github.com/Travis-Prall/resume/blob/main/pics/grafana_ac_data.png "Grafana AC Graph")
