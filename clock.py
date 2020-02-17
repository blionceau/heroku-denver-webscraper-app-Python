'''
Created on Jan 23, 2020

@author: Simeon
'''

# +++++++++++++++++++++++ RESOLVES IMPORT ISSUEs++++++++++++++++
# when you want to run the clock.py module as a script from the command line
# import sys
# from pathlib import Path 
# file = Path(__file__).resolve()
# parent, root = file.parent, file.parents[1]
# sys.path.append(str(root))
# 
# # Additionally remove the current file's directory from sys.path
# try:
#     sys.path.remove(str(parent))
# except ValueError: # Already removed
#     pass

# +++++++++++++++++++++++ END ++++++++++++++++++++++++++
#from AppForeclosures import runwebscraper
#from .AppForeclosures import runMe
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

# @sched.scheduled_job('interval', minutes= 2)
# def timed_job():
#     print('This job is run every 6 hours.')
#     #runwebscraper.runMe()
@sched.scheduled_job('cron', day_of_week='mon-sat', hour=17, minutes = '20-25')
def scheduled_job(args):
    print('This job is run every weekday at 11 pm.')
    #runwebscraper.runMe()
sched.start()