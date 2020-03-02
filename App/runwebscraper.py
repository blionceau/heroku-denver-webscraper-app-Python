
'''
Created on Jan 21, 2020
@author: Simeon
'''
# libraries
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from apscheduler.schedulers.blocking import BlockingScheduler
from pymongo import MongoClient
import requests
import urllib3
from datetime import date, timedelta
from pymongo.errors import PyMongoError
import os
import time
import sys
import pandas as pd 
import csv



# logging record 

'''
Created on Jan 17, 2020

@author: Simeon
'''


class Loggings:
    '''
    the loggings class is for flexible event logging to track down the events that take 
    place while the application is running. It records errors, exception, warnings, custom 
    info massages, etc.. in a logging file. it is a sort of substitute printing on your console. 
    '''
   
    def _getLog(self):
        # this sets the root logger to write to your console
        # by default the root logger is set to WARNING. 
        # here the root logger is set to NOTSET. 
        logging.basicConfig(level=logging.NOTSET)
        # setup multiple loggers for different sections of the application
        log_webscraper = logging.getLogger('webscraper')#logger[0]
        log_rootDB_process = logging.getLogger('CSV_addingCase#Root')#logger[1]
        log_mongodb_conn = logging.getLogger('Connect_Mongodb_DataPushing')#logger[2]
        log_mailgun = logging.getLogger('mailgun')#logger[3]
        log_apscheduler = logging.getLogger('jobScheduler')#logger[4]
        # Create file handler saved as logging_file_yyyy-mm-dd.log 
        file_handler = logging.FileHandler('logging_file_'+ str(date.today()) +'.log')
        # Create formatters and add it to handlers
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        # Add handlers to each logger created above
        logger = {'0': log_webscraper,'1':log_rootDB_process, '2':log_mongodb_conn, '3':log_mailgun, '4':log_apscheduler}
        [logger[key].addHandler(file_handler) for key in logger.keys()]
        
        return logger
        
        if __name__ == ('__main__'): 
    
            Loggings()._getLog()


# table dimensions
'''
Created on Jan 17, 2020

@author: Simeon
'''

class WebTableSizeCounter:
    '''
    this class is used to get the size of a table uploaded on a webpage.
    '''
    # typical object of this class:
    # table_size_count= webTableSizeCounter(browser.find_element_by_xpath("//table[@id='gridSearchResults']"))
    def __init__(self, table_gridSearchResults): # constructor initialization
        self.__table = table_gridSearchResults
        
    def get_cases_found_count(self):
        return (self.__table.find_elements_by_xpath("/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr/td/div/div/div/div[2]/div"))
    
    def get_row_count(self):
        return len(self.__table.find_elements_by_tag_name("tr"))

    def get_column_count(self):
        return len(self.__table.find_elements_by_xpath("//thead/tr/th"))
    
    def get_table_size(self):
        return {"rows": self.get_row_count(),
            "columns": self.get_column_count()}
        
# functions to interact with the website and to automatically extract data from it using selenium and chrome.exe

'''
Created on Jan 17, 2020

@author: Simeon
'''



class WebScraperFunctions:
    '''
    functions to scrape necessary information from denver county foreclosure webpage
    '''


    def __init__(self, chrome_options, chrome_driver_path, web_to_scrape):
        self.chrome_options = chrome_options
        self.chrome_driver_path = chrome_driver_path # "C:\\Users\\Simeon\\Anaconda\\chromedriver.exe" 
        self.web_to_scrape = web_to_scrape # "https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search"
       
    # returns the hyperlink to scrape
    def _getWebHyperlink(self):
        return self.web_to_scrape
    # return google chrome driver
    def _driver(self): 
        # heroku driver 
        driver = webdriver.Chrome(executable_path=os.environ.get(self.chrome_driver_path), chrome_options=self.chrome_options)
        # eclipse driver
        #driver = webdriver.Chrome(executable_path= self.chrome_driver_path, chrome_options=self.chrome_options)
        return driver 
    # date clicker to click in the opened-to field
    def _date_openedTo(self, browser):
        try:
            datepicker_to = browser.find_element(By.XPATH, "//input[@id='openedTo']")
            time.sleep(2) 
            datepicker_to.click()
            time.sleep(2)
        except Exception:
            browser.close()
            browser.quit()
            
    # date picker to select a date from a drop-down menu calendar to fill into the opened-to field
    def _date_picker_toDate(self, browser, openedToDate):
        try:
            datepicker_to_click = browser.find_element(By.XPATH, "//a[contains(text(), '"+str(openedToDate)+"')]")
            time.sleep(2)
            datepicker_to_click.click()
            time.sleep(2)
        except Exception:
            
            browser.close()
            browser.quit()

    # date-clicker to click in the opened-from field
    def _date_openedFrom(self, browser):
        try:
            datepicker_from = browser.find_element(By.XPATH, "//input[@id='openedFrom']")
            time.sleep(2)
            datepicker_from.click()
            time.sleep(2)
        except Exception:
            browser.close()
            browser.quit()
        
    # date-picker to select a date from a drop-down menu calendar to fill into the opened-from field   
    def _date_picker_fromDate(self, browser, openedFromDate):
        try:
            datepicker_from_click = browser.find_element(By.XPATH, "//a[contains(text(), '"+str(openedFromDate)+"')]") 
            time.sleep(2)
            datepicker_from_click.click()
            time.sleep(2)
        except Exception:
            browser.close()
            browser.quit()

    # select and click the search button
    def _search_button(self, browser):
        search_button = browser.find_element_by_id("searchButton")
        time.sleep(2)
        search_button.click()
        time.sleep(2)
    # select and click accept button
    def _accept_button(self, browser):
        accept_button = browser.find_element_by_id("acceptDisclaimerButton")
        time.sleep(3)
        accept_button.click()
    # toggle to previous month on on the calendar dropdown menu 
    # in case opened-from date has to be picked from last month
    def _date_picker_toggle_prev(self, browser):
        
        datepicker_toggle_month = browser.find_element(By.XPATH, "//span[contains(.,'Prev')]")
        time.sleep(2)
        datepicker_toggle_month.click()
        time.sleep(2)
    # this function is used when search-result contains only one case. 'note amount' is located on a different page, thus,
    # you we need to toggle using the tabForeclosure button
    def _oneCase_toggle_fclosure(self, browser):
        
        foreclosure_button = browser.find_element(By.XPATH, "//a[@id='tabForeclosures']/span")
        time.sleep(2)
        foreclosure_button.click()
        time.sleep(2)
   
    # it retrieves number of cases found on the search page
    def _number_of_cases(self, browser):
        casesFound = browser.find_element_by_xpath("//table[@id='mainTableContent']/tbody/tr/td/table/tbody/tr[2]/td[2]/table/tbody/tr/td/div/div/div/div[2]").text
        nuOfCases = int(''.join([num for num in casesFound if num in "1234567890"]))
        return nuOfCases
    # save an empty csv file
    def _zero_cases(self):
        nuOfCases = 0
        df_numOfCases = pd.DataFrame({'ZERO CASE': str(nuOfCases), 'Date': str(date.today())}, index = [0])                 
        df_numOfCases.to_csv( str(nuOfCases) +'_Cases_' + str(date.today()) + '.csv', index=False, encoding='utf-8')
        
# website launcher, data extraction and saving data in a csv file
'''
Created on Jan 17, 2020

@author: Simeon
'''



class WebpageLauncher:
    '''
    XPaths and locations of different fields that we interested in to scrape from the webpage
    
    # TABLE COLUMN NAMES: NAME PARTY TYPE CASE NUMBER STATUS ADDRESS NOTE AMOUNT AUCTION DATE ELECTION/DEMAND
    # XPATHs:
        # //table[@id='gridSearchResults']/thead/tr/th
        # //table[@id='gridSearchResults']/thead/tr/th[2]
        # //table[@id='gridSearchResults']/thead/tr/th[3]
        # //table[@id='gridSearchResults']/thead/tr/th[4]
        # //table[@id='gridSearchResults']/thead/tr/th[5]
        # //table[@id='gridSearchResults']/thead/tr/th[6]
        # //table[@id='gridSearchResults']/thead/tr/th[8]

    # TABLE DATA
    # ROW 1: 
        #//table[@id='gridSearchResults']/tbody/tr/td/a (hypyerLink >>/a)
        #//table[@id='gridSearchResults']/tbody/tr[2]/td[2]
        #//table[@id='gridSearchResults']/tbody/tr[2]/td[3]/a
        #//table[@id='gridSearchResults']/tbody/tr[2]/td[4]
        #//table[@id='gridSearchResults']/tbody/tr/td

    # HypterLinks
        # //a[contains(@href, '/ForeclosurePortal/Party.aspx/Index/359771?caseID=78155&attorney=
            False&digest=vJLK%2FQrKO4R6f4Cu63t39P1yMBmiBagz0Jd2roRJu1w')]
        # //a[contains(@href,'hyperLink')]>>> //a[@href]
        # // https://www.denvergov.org/hyperLink

    # Month toggling
        #xpath=//div[@id='ui-datepicker-div']/div/a/span
        #xpath=//span[contains(.,'Prev')]

    # ONE CASE WEBPAGE
        xpath=//div[@id='summaryAccordionCollapse']/table/tbody/tr/td/dl/dd[2] case number
        xpath=//div[@id='summaryAccordionCollapse']/table/tbody/tr/td[2]/dl/dd[3] status date
        xpath=//div[@id='summaryAccordionCollapse']/table/tbody/tr/td[3]/dl/dd[2] status
        xpath=//div[@id='summaryAccordionCollapse']/table/tbody/tr/td[3]/dl/dd[5] address
        xpath=//table[@id='gridParties']/tbody/tr[2]/td[2] name
        xpath=//table[@id='gridParties']/tbody/tr[2]/td type
        xpath=//table[@id='gridCaseEvents']/tbody/tr/td event
        xpath=//table[@id='gridDockets']/tbody/tr[4]/td[2]
        xpath=//table[@id='gridDockets']/tbody/tr[7]/td[2]
        xpath=//table[@id='gridDockets']/tbody/tr[7]/td[3]
        xpath=//table[@id='gridParties']/tbody/tr[2]/td[2]
        xpath=//table[@id='gridDockets']/tbody/tr[5]/td[2]

    '''
    '''
    private variables: use double underscore
    '''
    
    def __init__(self, web_scraper_func):
        self.__period = 1 # today time-window
        self.web_scraper = web_scraper_func # object

        # integer variables
        self.__openedToDate = 0
        self.__openedFromDate = 0
        self.__delta_date = 0
        self.__currentMonth = 0
        self.__nuOfCases = 0
        self.__nuOfRows = 0
        self.__nuOfColumns = 0
        self.__tableSize = 0
        # list variables
        self.__tableTitle = []
        self.__names = []
        self.__names_hypLink = []
        self.__partyTypes = []
        self.__caseNumbers = []
        self.__caseHypLink = []
        self.__caseStatus = []
        self.__addresses = []
        self.__noteAmounts = []
        self.__auctionDates = []
        self.__election_Demands = []
        # boolean variables
        self.__chromeLaunched = False
        self.__webpageLaunched = False
        self.__isTableGrid = False
        self.__isOneCase = False
        self.__isElection_Demands_1 = False
        self.__isElection_Demands_2 = False
        # string variables
        self.__summaryAccCollapse = ""
        self.__events = ""
        self.__parties = ""
        self.__caseDockets = ""
    #  a setter method to change the value of a private variable period when we want to change 
    # the default  time-window from one day to any range up to 30 days from today going backwards
           
    def setPeriod(self, period): 
        self.__period = period
    # a getter method to retrun the number of cases found from search result
    def getNuOfCases(self):
        return self.__nuOfCases
    # two methods responsible for performing all automatic clicks using selenium and to scrape data
    # from denver forclosure webpage
    
    def _web_scrape_oneCase(self):
        
        '''
        function to extract data from search results of one case
      
        '''
        self.__summaryAccCollapse = "//div[@id='summaryAccordionCollapse']"
        self.__parties = "//table[@id='gridParties']"
        self.__events = "//table[@id='gridCaseEvents']"
        self.__caseDockets = "//table[@id='gridDockets']"
        
        return self.__parties, self.__summaryAccCollapse, self.__events, self.__caseDockets
    
        
    def _web_scrape_table(self):
        
        '''
        function to extract data from a web-page containing a table with more than one foreclosure case
        '''
        # reminder on how logger is defined
        # logger = {'0': log_webscraper,'1':log_rootDB_process, '2':log_mongodb_conn,...
        #'3':log_mailgun, '4':log_apscheduler}
        
        
        _logging = Loggings() # returns logger-dictionary
        _logger = _logging._getLog()['0'] #  logger = {'0': log_webscraper,.....}

        # month, date : currentMonth, openedToDate, openedFromDate
        self.__currentMonth = int(date.today().month)
        self.__openedToDate = int(date.today().day) 
        
        if self.__period == 1:
            self.__openedFromDate = int(date.today().day) # period == 1 -->> today's date
        else:
            self.__openedFromDate =  int(pd.date_range(end = pd.datetime.today(), periods = self.__period).day[0])# 2 for starting from yesterday
            #print("self.__openedFromDate", self.__openedFromDate)
        # webdriver
        try:
            browser = self.web_scraper._driver()
            browser.implicitly_wait(5)
            self.__chromeLaunched = True
        except requests.ConnectionError as e:
            _logger.exception('chrome browser has failed.\n' + str(e))# exception includes errors and trace backs
            _logger.error('ConnectionError')
            time.sleep(2)
            browser.close()
            browser.quit()
            exit
            
        if self.__chromeLaunched == True:
            try:
                webHyperlink = self.web_scraper._getWebHyperlink()
                browser.get(webHyperlink)   
                time.sleep(2)
                self.__webpageLaunched = True
            
            except NoSuchElementException as e:
                _logger.info('Denver web-page has failed to launch\n.' )
                _logger.error('NoSuchElementException')
                _logger.exception(str(e))
                time.sleep(2)
                browser.close()
                browser.quit()
                sys.exit(1)
        # compute delta-days between specified time window
        self.__delta_date = self.__openedToDate - self.__openedFromDate
    
        if(self.__delta_date >= 0) and self.__webpageLaunched == True:
            # clicks in the openedTo field 
            self.web_scraper._date_openedTo(browser) 
            try:
                # pick a opened-to date
                self.web_scraper._date_picker_toDate(browser, self.__openedToDate)
            except NoSuchElementException as e:
                _logger.info('toDate: '+ str(self.__openedToDate)) 
                _logger.error('NoSuchElementException')
                _logger.exception('date_picker_toDate has failed.\n' + str(e))                
                browser.close()  
                browser.quit()
                sys.exit(1)
            # clicks in the openedFrom field 
            self.web_scraper._date_openedFrom(browser)
            
            try:
                # pick openedFrom date
                self.web_scraper._date_picker_fromDate(browser, self.__openedFromDate)
                self.__fromDatePicked = True
                   
            except NoSuchElementException as e: 
                _logger.info('openedFromDate: ' + str(self.__openedFromDate))
                _logger.exception('date_picker_FromDate has failed.\n' + str(e))                
                browser.close()
                browser.quit()
                exit(1)
                 
        else: # handle dates from last month
            self.web_scraper._date_openedTo(browser)
            
            try:
                self.web_scraper._date_picker_toDate(browser, self.__openedToDate)
              
            except NoSuchElementException as e:
                _logger.info('openedToDate: ' + str(self.__openedToDate))
                _logger.error(' NoSuchElementException')
                _logger.exception('date_picker_toDate has failed.\n' +str(e))              
                browser.close()
                browser.quit()
                sys.exit(1)
                
            try:
                self.web_scraper._date_openedFrom(browser)
                self.web_scraper._date_picker_toggle_prev(browser)
            except Exception as e:
                _logger.info('toggle to previous month.\n' )
                _logger.error('NoSuchElementException')
                _logger.exception(str(e))
                browser.close()
                browser.quit()
                exit(1)

            try:
                self.web_scraper._date_picker_fromDate(browser, self.__openedFromDate)

            except NoSuchElementException as e:  
                _logger.info('openedToDate: ' + str(self.__openedFromDate))
                _logger.error('NoSuchElementException')
                _logger.exception('date_picker_toDate has failed.\n' +str(e))                
                browser.close()
                browser.quit()
                exit(1)

        try: # clicks search button, then clicks accept button
            self.web_scraper._search_button(browser)
            self.web_scraper._accept_button(browser)
        # catch several exceptions that can be raised when the above steps do not run as expected
        except requests.ConnectionError as e:
            _logger.info('Connection error encountered')
            _logger.exception(str(e))
            

        except requests.Timeout as e:
            _logger.info('Timeout Error')
            _logger.exception(str(e))
            

        except requests.RequestException as e:
            _logger.info('Server rejected the requests, too many requests')
            _logger.exception(str(e))
            
            
        except ConnectionRefusedError as err:
            _logger.info('Portal Connection refused by the server')
            _logger.error(str(err))
            
    
        except urllib3.exceptions.NewConnectionError as err:
            _logger.info('Portal New connection timed out')
            _logger.error(str(err))
            

        except urllib3.exceptions.MaxRetryError as err:
            _logger.info('Portal Max tries exceeded')
            _logger.error(str(err))
             
        except urllib3.exceptions.ConnectTimeoutError as err:
            _logger.info('Timeout error')
            _logger.error(str(err))

        except urllib3.exceptions.ClosedPoolError as err:
            _logger.info('ClosedPoolError')
            _logger.error(str(err))
            
        except urllib3.exceptions.HTTPError as err:
            _logger.info('HTTPError')
            _logger.error(str(err))
            


        if (0 < self.__currentMonth <= 12  and 0 < self.__openedFromDate <=31 and 0 < self.__openedToDate <= 31):
            
            try : 
                self.__nuOfCases = self.web_scraper._number_of_cases(browser)
                self.__isTableGrid = True
                self.__isOneCase = False
                
            except:
                
                self.__isTableGrid = False
                self.__isOneCase = True
                self.__nuOfCases = 1
                
            if self.__nuOfCases > 0 and self.__isTableGrid == True : 
                _logger.info('cases found: '+ str(self.__nuOfCases))
                # use webTableSizeCounter object to retrieve the size of the table from the search-results webpage
                table_size_count = WebTableSizeCounter(browser.find_element_by_xpath("//table[@id='gridSearchResults']"))

                self.__nuOfRows = table_size_count.get_row_count()
                self.__nuOfColumns = table_size_count.get_column_count()
                self.__tableSize = table_size_count.get_table_size()
                

                for i in range(1, self.__nuOfColumns + 1):
                    # extract titles from the table and append them to tableTittle list
                    self.__tableTitle.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/thead/tr/th["+str(i)+"]").text)

                for i in range(1, self.__tableSize['rows']):

                    # extract and append data from the table and append it to each corresponding field 
                    self.__names.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(1)+"]").text)
                    self.__partyTypes.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(2)+"]").text)
                    self.__caseNumbers.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(3)+"]").text)
                    self.__caseStatus.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(4)+"]").text)
                    self.__addresses.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(5)+"]").text)
                    self.__noteAmounts.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(6)+"]").text)
                    self.__auctionDates.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(7)+"]").text)
                    self.__election_Demands.append(browser.find_element_by_xpath("//table[@id='gridSearchResults']/tbody/tr["+str(i)+"]/td["+str(8)+"]").text)
                # dataFrame of the above lists   
                try: 
                    df_searchResults = pd.DataFrame({self.__tableTitle[0]:self.__names, 
                                                     self.__tableTitle[1]:self.__partyTypes, 
                                                     self.__tableTitle[2]:self.__caseNumbers,
                                                     self.__tableTitle[3]:self.__caseStatus, 
                                                     self.__tableTitle[4]:self.__addresses, 
                                                     self.__tableTitle[5]:self.__noteAmounts,
                                                     self.__tableTitle[6]:self.__auctionDates, 
                                                     self.__tableTitle[7]:self.__election_Demands}) 
                except Exception  as e:
                    _logger.exception(str(e))
                # save the above dataFrame to a csv file
                try:
                    df_searchResults.to_csv( str(self.__nuOfCases) +'_Cases_'  + str(date.today()) + '.csv', index=False,
                                            encoding='utf-8')
                except Exception as e:
                    _logger.exception(str(e))
                # logger confirms in the file was saved 
                _logger.info('CSV file successfully saved: ' +str(self.__nuOfCases) +'_Cases_'  + str(date.today()))
                time.sleep(10)
                browser.close()
                browser.quit()

            elif self.__nuOfCases == 0:
                # logger to confirm if there is no cases
                self.web_scraper._zero_cases()
                _logger.info('success: '+ str(self.__nuOfCases) + '_case posted')
                time.sleep(3)
                browser.close()
                browser.quit()
                
                
            elif self.__nuOfCases > 0 and self.__isOneCase == True:
                # logger to confirm is one case was found
                _logger.info('success: ' + str(self.__nuOfCases) + '_case posted')
                
                # extract and append data to lists
                self.__tableTitle = ['NAME', 'PARTY TYPE', 'CASE NUMBER','STATUS','ADDRESS','NOTE AMOUNT','AUCTION DATE', 'ELECTION/DEMAND']
                self.__names.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[0]) + "/tbody/tr[2]/td[2]").text)
                self.__partyTypes.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[0]) + "/tbody/tr[2]/td").text)
                self.__caseNumbers.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[1]) + "/table/tbody/tr/td/dl/dd[2]").text)
                self.__caseStatus.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[1]) + "/table/tbody/tr/td[3]/dl/dd[2]").text)
                self.__addresses.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[1]) + "/table/tbody/tr/td[3]/dl/dd[5]").text)
                self.__auctionDates.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[2]) + "/tbody/tr/td").text)
                
                # election/demand data scraper. note election/demand date can be located at a different 
                # position depending on the case filing stage status 
                if self.__isElection_Demands_1 == False and self.__isElection_Demands_2 == False:
                    self.__election_Demands.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[3]) + "/tbody/tr[7]/td[2]").text)
                    self.__isElection_Demands_1 == True
                elif self.__isElection_Demands_1 == True: 
                    self.__election_Demands.append(browser.find_element_by_xpath(str(self._web_scrape_oneCase()[3]) + "/tbody/tr[7]/td[2]").text)
                    self.__isElection_Demands_2 == True
                else: 
                    _logger.info('election/demand not found:','isElection_Demands_1: ',self.__isElection_Demands_1, ' isElection_Demands_2: ',self.__isElection_Demands_2)

                # note amount is located to a separate page that we can reach by toggling using Foreclosure button
                self.web_scraper._oneCase_toggle_fclosure(browser)
                self.__noteAmounts.append(browser.find_element_by_xpath("//div[@id='detailsContent']/div[2]/table/tbody/tr/td/table/tbody/tr[5]/td[2]").text)
                
                # data frame to save data 
                try:
                    
                   
                    df_searchResults = pd.DataFrame({self.__tableTitle[0]:self.__names, 
                                                     self.__tableTitle[1]:self.__partyTypes, 
                                                     self.__tableTitle[2]:self.__caseNumbers,
                                                     self.__tableTitle[3]:self.__caseStatus, 
                                                     self.__tableTitle[4]:self.__addresses, 
                                                     self.__tableTitle[5]:self.__noteAmounts,
                                                     self.__tableTitle[6]:self.__auctionDates, 
                                                     self.__tableTitle[7]:self.__election_Demands}) 
                except Exception as e:
                    _logger.exception(str(e))
                except ValueError as err:
                    _logger.error(str(err))
                try:
                    # save a csv file
                    df_searchResults.to_csv(str(self.__nuOfCases) +'_Cases_'  + str(date.today()) + '.csv', index=False,
                                            encoding='utf-8')
                    # logger confirms if the file is saved
                    _logger.info('CSV file successfully saved: ' +str(self.__nuOfCases) +'_Cases_'  + str(date.today()))
                except Exception as e:
                    _logger.exception(str(e))
                except UnboundLocalError as err:
                    _logger.error(str(err))
                    
                time.sleep(10)
                browser.close()
                browser.quit()
                

            else:
                _logger.inf('Something is wrong! ---->>>> Number of cases is negative.')
                time.sleep(3)
                browser.close()
                browser.quit()
                sys.exit(1) # exit with error

        elif (12 < self.__currentMonth) or (self.__currentMonth < 0):
            _logger.info('failure! ---->>>> current_month out of range.')
            time.sleep(3)
            browser.close()
            browser.quit()
            sys.exit(1)
            
        elif (31 < self.__openedFromDate) or (self.__openedFromDate < 0) or (31 < self.__openedToDate) or (self.__openedToDate < 0):
            _logger.info('failure! ---->>>> (openedFromDate|| openedToDate) out of range')
            time.sleep(3)
            browser.close()
            browser.quit()
            sys.exit(1)
            
        else:
            _logger.info('failure! ---->>>> total failure')
            time.sleep(3)
            browser.close()
            browser.quit()
            sys.exit(1)
# login information of mailgun and mongodb account

'''
Created on Jan 17, 2020

@author: Simeon
'''

class MailGunLogIn :
    '''
    Login credentials of mailgun and mongodb
    
    gmail:
    API key: 
    API base URL: 
    yahoo:
    sandbox = "" # sandbox for yahoo
    requests_msg_url = "".format(sandbox)
    key = "" # API KEY for yahoo mail

    '''
    def __init__(self):
        '''
        Constructor
        '''
    #-------------- mailgun -----------------------------
        self.sandbox = ""  # sandbox for yahoo
        self.requests_msg_url = "".format(self.sandbox)
        self.key = ""  # API KEY for yahoo mail
        self.sender = "
        self.recipient = ""
        self.subject = "Denver Foreclosures Notification"     
# denverforeclosures20@yahoo.com
    # getters
    def getSandbox(self):
        return self.sandbox
    def getRequestsMsgURL(self):
        return self.requests_msg_url
    def getKEY(self):
        return self.key
    def getSender(self):
        return self.sender
    def getRecipient(self):
        return self.recipient
    def getSubject(self):
        return self.subject
    
class MongodbLogIn:
    
    def __init__(self):
        '''
        Constructor
        '''
        #-------------- mongodb -----------------------------
        self.username = ''
        self.password = ''
        self.db = '' 
        self.cluster_name = 'denver_search'
        self.collection_name = 'daily_data'
        
    def getUsername(self):
        return self.username
    def getPassword(self):
        return self.password
    def getdBName(self):
        return self.db
    def getClusterName(self):
        return self.cluster_name
    def getCollectionName(self):
        return self.collection_name
# adding a root in the csv file before pushing it into mongodb      
        
'''
Created on Jan 17, 2020

@author: Simeon
'''


class MongodbDataPreprocess:
    
    '''
    process a csv file containing data of foreclosure cases: open a csv file 
    and add a root to use when pushing data into mongodb database
    '''
    def __init__(self, numOfCases, csvFilePath):
        self.__numOfCases = numOfCases
        self.__csvFilePath = csvFilePath
        
    def _update_root_dict(self, dict1, dict2): 
        return(dict1.update(dict2))

    def _open_csvFile(self):
        
        _logging = Loggings() # return logger-dictionary
        _logger = _logging._getLog()['1'] #  logger = {....'1':log_rootDB_process,.....}
        # read csv file and add it to data-dictionary
        _data = {}
        try:
            with open(self.__csvFilePath) as csvFile:
                csvReader = csv.DictReader(csvFile)
                if self.__numOfCases != 0:
                    for rows in csvReader:
                        _id = rows['CASE NUMBER']
                        _data[_id] = rows
                    _logger.info('success: root added ')
                else:
                    for rows in csvReader:
                        _id = rows['ZERO CASE']
                        _data[_id] = rows
                    _logger.info('success: root added ')
        except Exception as e:
            _logger.info('failure: adding a root to the csv file')
            _logger.exception(str(e))
                
        return _data
    
    def _db_data_process(self):  
        # adding a root today's date as _id of data to push in mongodb
        _root_dict = {"_id":str(date.today())} #dict1
        self._update_root_dict(_root_dict, self._open_csvFile())
        return _root_dict
# mongodb client
'''
Created on Jan 17, 2020

@author: Simeon
'''

class MongoDB:
    '''
    login mongo_db, make a connection to your cluster -->database-->collection name
        
    '''
       
    def __init__(self, username, password, db, cluster_name, collection_name):
        self.__username = username
        self.__password = password
        self.__db = db
        self.__cluster_name = cluster_name
        self.__collection_name = collection_name
       
    
    def _connect_mongo(self):
        """ A util for making a connection to mongo_db
        <username>: 
        <password>: 
        <database>: 
        
        mongodb+srv://<username>:<password>@<database>
        """
        
        _logging = Loggings()
        _logger = _logging._getLog()['2']# logger= {...'2':log_mongodb_conn,....}


        if self.__username and self.__password:
            mongo_uri = 'mongodb+srv://%s:%s@%s' % (self.__username, self.__password, self.__db)
            conn_cluster = MongoClient(mongo_uri)
            mongodb_db = conn_cluster[self.__cluster_name]
            mongodb_collection = mongodb_db[self.__collection_name]
            
        else:
            _logger.error('Provide valid username and password!')
        
        return mongodb_collection
    # a function to use when you need to delete data from your collection database
    def _del_db_data(self, _mongodb_collection, date):  
        return _mongodb_collection.delete_many( { "_id" : str(date) } ) # "2020-01-08"
    # used to insert data or document into your collection
    def _insert_data_mongodb(self, _mongodb_collection, dict_input_file):
        return _mongodb_collection.insert_one(dict_input_file)
    # below functions are used when you need to process data fetched from your database back to 
    # a Python platform for further processes
    #-----------------------------------
    # to retrieve data from your database based on the _id :date 
    def _fetch_data_mongodb(self, _mongodb_collection, _date):
        return _mongodb_collection.find({"_id": str(_date)}) # {"_id": str(date.today())
    # to delete an _id from your fetched data from mongo database
    def _del_id_mongoData(self, _mongodb_collection, _date):
        # Expand the cursor and construct the DataFrame
        df_data = pd.DataFrame(list(self._fetch_data_mongodb(_mongodb_collection, _date)))
        # Delete the _id
        if '_id' in df_data:
            del df_data['_id']
        return df_data
    # to make a dataframe for retrieved data from your database
    def _df_mongodb_data(self, _db_data):
        
        _name = []
        _type = []
        _caseNumber = []
        _status = []
        _address = []
        _amount = []
        _auctionDate = []
        _electionDemDate = []
        _title =['NAME', 'PARTY TYPE', 'CASE NUMBER','STATUS','ADDRESS','NOTE AMOUNT','AUCTION DATE', 'ELECTION/DEMAND']

        for _case_index in _db_data.keys():
            for _record in _db_data[_case_index]:
                _name.append(_record[_title[0]])
                _type.append(_record[_title[1]])
                _caseNumber.append(_record[_title[2]])
                _status.append(_record[_title[3]])
                _address.append(_record[_title[4]])
                _amount.append(_record[_title[5]])
                _auctionDate.append(_record[_title[6]])
                _electionDemDate.append(_record[_title[6]])

        df_mngdb_data = pd.DataFrame({
            _title[0]: _name, 
            _title[1]: _type, 
            _title[2]: _caseNumber,
            _title[3]: _status, 
            _title[4]: _address, 
            _title[5]: _amount,
            _title[6]: _auctionDate,
            _title[7]: _electionDemDate
            })
        return df_mngdb_data
# Mailgun to send emails

'''
Created on Jan 17, 2020

@author: Simeon
'''


class MailGun:
    # MailGun class to send emails from python
    '''
    sends emails
    '''
    def __init__(self, sandbox, requests_msg_url, key, sender, recipient, subject):
        self.__sandbox = sandbox
        self.__requests_msg_url = requests_msg_url
        self.__key = key # API KEY
        self.__sender = sender
        self.__recipient = recipient
        self.__subject = subject
        
       
    # method to send an email without any attachment when there is no cases found
    def send_no_attachment(self):
        return requests.post(
            self.__requests_msg_url, 
            auth=("api", self.__key), 
            data={"from":self.__sender , "to": self.__recipient, "subject": self.__subject,
                "text":" There was not any new case posted since yesterday at the UTC time zone.\n\n For more information visit (https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search) \n\nRegards,\n\n Denver Foreclosures"})
    # method to send an email with an attachment of cases    
    def send_attachment(self, numOfCases, attachFileName, inputFilePath ):
        return requests.post(
            self.__requests_msg_url, 
            auth=("api", self.__key), 
            files = {("attachment", (attachFileName, open(inputFilePath, 'rb').read()))},
            data={"from":self.__sender , "to": self.__recipient, "subject": self.__subject,
                "text":'Denver county has posted ' + str(numOfCases) + " case(s) since yesterday at the UTC time zone(See the attached CSV file).\n\n For more information visit (https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search).\n\nRegards,\n\n Denver Foreclosures"}) 
    def send_email(self, numOfCases, inputFilePath):
        
        if numOfCases!= 0:
            attachFileName = str(numOfCases) +'_Cases_'  + str(date.today()) + '.csv'
            self.send_attachment(numOfCases, attachFileName, inputFilePath)
        else:
            self.send_no_attachment()

# fetch data from mongodb

'''
Created on Jan 17, 2020

@author: Simeon
'''


class JobAPScheduler:
    '''
    jobScheduling to schedule when the application should run
    
    '''
    def __init__(self, chrome_options, chrome_driver_path, web_to_scrape, period):
        self.__chrome_options = chrome_options # to run selenium without launching the web
        self.__chrome_driver_path = chrome_driver_path # "C:\\Users\\Simeon\\Anaconda\\chromedriver.exe" 
        self.__web_to_scrape = web_to_scrape # "https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search"
        self.__period = period
        
    def app_scheduled_job(self):
        # get login information of mailgun 
        _mgunLogin = MailGunLogIn()
        _sandbox = _mgunLogin.getSandbox()
        _requests_msg_url = _mgunLogin.getRequestsMsgURL()
        _gunKEY = _mgunLogin.getKEY()
        _sender = _mgunLogin.getSender()
        _recipient = _mgunLogin.getRecipient()
        _subject = _mgunLogin.getSubject()
        # mongodb login info
        _mongoLogin = MongodbLogIn()
        _username = _mongoLogin.getUsername()
        _password = _mongoLogin.getPassword()
        _db = _mongoLogin.getdBName()
        _clusterName = _mongoLogin.getClusterName()
        _collection_name = _mongoLogin.getCollectionName()
        # objects
        _mail_gun = MailGun(_sandbox, _requests_msg_url, _gunKEY, _sender, _recipient, _subject)
        #_mongo_db = MongoDB(_username, _password, _db, _clusterName, _collection_name)
        
        _logging = Loggings()
        
        # loggers
        _logger_mongo = _logging._getLog()['2']# logger= {...'2':log_mongodb_conn,....}
        _logger_mailgun = _logging._getLog()['3']
        _logger_scheduler = _logging._getLog()['4']
        

        _scraper_func = WebScraperFunctions(self.__chrome_options, self.__chrome_driver_path, self.__web_to_scrape)
        _launcher = WebpageLauncher(_scraper_func)
        _launcher.setPeriod(self.__period)
        _launcher._web_scrape_table()
        _numOfCases = _launcher.getNuOfCases()
        # inputfile to insert in mongodb database and to send via mailgun as an attachment
        _inputFilePath = str(_numOfCases) +'_Cases_'  + str(date.today()) + '.csv'
        
        try:
            #_mngdb_coll = _mongo_db._connect_mongo() # return mongoDB_collection_name
            _logger_mongo.info('collection reached: Success')
        except PyMongoError as err: 
            _logger_mongo.error(str(err))
            _logger_mongo.info('collection reached: Failure')
        except Exception as e:
            _logger_mongo.exception(str(e))
        # MongodbDataPreprocess class.MongodbDataPreprocess()method   
        _data = MongodbDataPreprocess(_numOfCases, _inputFilePath)
        _db_inputFile = _data._db_data_process()# add a root 

        # comment it before deploying the application. It is used to avoid duplicates keys during test run
        #try:
            #_mongo_db._del_db_data(_mngdb_coll, str(date.today())) # 2020-01-10-comment this line
        #except UnboundLocalError as err:
        #    _logger_mongo.error(str(err))
        try:
            #_mongo_db._insert_data_mongodb(_mngdb_coll, _db_inputFile) # insert data in mongo_db
            _logger_mongo.info('data insertion: success ')
        except PyMongoError as err:
            _logger_mongo.error(str(err)) 

        try:
            _mail_gun.send_email(_numOfCases, _inputFilePath)
            _logger_mailgun.info('Success: email sent')
        except Exception as e:
            _logger_mailgun.exception(str(e))  

        # to clean up after us when the App runs on Heroku
        if os.path.exists(_inputFilePath): 
            os.remove(_inputFilePath)
        else:
            _logger_scheduler.error('inputFile does not exist')
            _logger_scheduler.info()
        # delete yesterdays logging record
        _loggingFile = 'logging_file_'+ str(date.today() - timedelta(days=1))+'.log' 
        
        if os.path.exists(_loggingFile): 
            os.remove(_loggingFile)
        else:
            _logger_scheduler.info('_loggingFile from yesterday does not exist')
         
        
        

# main method to run the application
'''
Created on Jan 17, 2020

@author: Simeon

'''

# main method
def runMe():
  
    '''
    main method to run the web-scraper. user has to provide :
    # her login info of mongodb and mailgun
    # chrome driver exe.file path
    # hyper-link of the web-site to scrape
    User can rest the period depending on the search time-window by using setPeriod method
    
    '''
    

    # logger for mongo-db, mail-gun and apscheduler
    _logging = Loggings()
    _logger_mongo = _logging._getLog()['2']  # logger= {...'2':log_mongodb_conn,....}
    _logger_mailgun = _logging._getLog()['3']
    _logger_scheduler = _logging._getLog()['4']
    
    
    #--------------------------- chrome settings------------------------------
    # chrome driver and hyper-link of the web-site to scrape  
    # chrome_driver_path = "C:\\Users\\Simeon\\Anaconda\\chromedriver.exe" 
    #web_to_scrape = "https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search"
    #--------------------------- end settings---------------------------------
    
    
    #--------------------------- HEROKU  Chrome settings-----------------------
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    # chrome path for heroku 
    chrome_driver_path = "CHROMEDRIVER_PATH"
    # machine chrome path 
    #chrome_driver_path = "C:\\Users\\Simeon\\AppData\\Local\\Programs\\chromedriver.exe" 
    web_to_scrape = "https://www.denvergov.org/ForeclosurePortal/Home.aspx/Search"
    #--------------------------- end settings---------------------------------
    # Args parser
    
    
    # --------------------- jobScheduling ---------------------
    #sched = BlockingScheduler()

#     @sched.scheduled_job('interval', minutes= 2)
#     #def timed_job():
#         #print('This job is run every 6 hours.')
#         #runMe()
#     @sched.scheduled_job('cron', day_of_week='mon-sat', minutes= int(sys.argv[2]))
#     
    _period = 2 # 1< _period <=31 1 will always return 0
    
    if 1<= _period <= 31:
        _sched = JobAPScheduler(chrome_options, chrome_driver_path, web_to_scrape, _period)

        try:
            # Schedule a job to run once from Monday to Friday(day_of_week='mon-fri') at 23:30 (pm) until yyyy-mm-dd 00:00:00
            #sched.add_job(_sched.app_scheduled_job, 'cron', day_of_week='mon-sun', hour=15, minute=54)
            #sched.add_job(_sched.app_scheduled_job, 'interval', seconds=60) # every minute
            _sched.app_scheduled_job()
            _logger_scheduler.info('add job_scheduler: success')
        except Exception as e:
            _logger_scheduler.exception(str(e))
            _logger_scheduler.error('jobScheduling Error ')    
        except TypeError as err:
            _logger_scheduler.scheduler.error(str(err))
        try: 
            #sched.start()
            _logger_scheduler.info('jobScheduling start: success')
        except Exception as e:
            _logger_scheduler.error('jobScheduling start Error')
            _logger_scheduler.exception(str(e))
            
    else:
        _logger_scheduler.error('wrong _period. It should be 1<= _period <= 31, but you have provided, '  + str(_period) +".")

if __name__ =='__main__':
    runMe()

