The main file for the project is ‘main.py’ which imports the database models from ‘models.py’ and APIs from ‘api.py’, 'user_controller.py' and 'admin_controller.py'

The Database ‘db.sqlite3’ resides in the ‘instance’ subfolder. ‘templates’ folder contains all the html pages used in the project. ‘static’ folder contains js, pdf and csv files

In order to run the app, servers are to be set for main.py, redis, celery, mailhog, celery beat

Functionalities:
Features:
1. Login/Registration for User and Login for Admin using a simple HTML form along with token based authentication
2. User can search shows/venue as per relevant filters and can also sort the results 
3. User can book multiple shows in multiple venues across multiple days as long as the show is not houseful
4. User can view their bookings 
5. Admin can perform CRUD on Venues as well as Shows
6. Users can rate the shows they have booked. This rating then contributes to the public rating 
of a show
7. Users can book multiple tickets for the same show if it is available even on the same day as 
long as the time of the show is different and the show is not houseful
8. Users are also levied a service fee which depends on the number of tickets they have booked. 
This fee contributes to the profit
9. Admin can view analytics of a venue which shows the total revenue earned by the ticket sales 
as well as the profit
10. Admins can export the above summary in a form of csv
11. Task has been scheduled to send the users a monthly report of their bookings
12. Task has been scheduled to send daily reminder mails to the inactive users
13. Relevant caching has been applied to improve performance