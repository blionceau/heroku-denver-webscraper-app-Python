# heroku-denver-webscraper-app
An application to scrape data of foreclosures  in Denver county, Colorado, USA.

- This application daily scrapes https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search (i.e., the website for foreclosures in Denver county, colorado, USA).
- Heroku job scheduler is set to run at 7:00 am. Besides, an APScheduler can also be considered. Thus, an automated email notification with an attachment in the csv file is daily sent to a specified receiver's email address. The recipient should have a MailGun account.
- Mongodb is used to store the data.
- The user can change the search window by changing the variable _period which is already set as 2 by default(e.g., _period = 2, the search will be done between today and yesterday).

- Requirements:
    - APScheduler==3.6.3
    - certifi==2019.11.28
    - chardet==3.0.4
    - dnspython==1.16.0
    - idna==2.8
    - numpy==1.18.1
    - pandas==0.25.3
    - pymongo==3.10.1
    - python-dateutil==2.8.1
    - pytz==2019.3
    - requests==2.22.0
    - selenium==3.141.0
    - six==1.14.0
    - tzlocal==2.0.0
    - urllib3==1.25.7



