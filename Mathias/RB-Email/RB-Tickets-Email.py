#Check the Website
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from time import sleep

#Email
from email.message import EmailMessage
import ssl
import smtplib

# Intervall < 0 -> Exit after one Check
#########################################################
intervall = 60 # Minuten
#########################################################


# # # # # # # # # # # 
# # # Variables # # # 
# # # # # # # # # # # 
wasAvailableLastTime = False
testMode = False
AllowElsifChecks = False


#XPATH of Tickets
ticketXPATH = "//*[@id='nr25040991']"
soldOutXPATH = "//*[@id='products']/div[3]/div[1]"

#Website
URL = "https://tickets.redbullring.com/de/f1/f1-grand-prix-oesterreich-2025/tickets.html"

#Email info
email_receiver = 'mathias.kornschober08@gmail.com'
email_sender = 'F1Tickets.Redbullring@gmail.com'
email_password = 'fuit asfe qfpz qmqh'  



# # # # # # # # # # # 
# # # Functions # # # 
# # # # # # # # # # # 

def initBrowser(URL):
    options = Options()
    options.add_argument("--headless")  # Run Chrome headlessly if needed
    options.add_argument("--disable-dev-shm-usage")  # Disable certain shared memory usage that may cause some logs
    options.add_argument("--log-level=3")  # Set Chrome's log level to ERROR, which suppresses debugging info
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation", "disable-dev-shm-usage"])
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    title = driver.title
    sleep(2)
    return driver
def findCoordinate(ticketXPATH, driver):
    ticket = driver.find_element(By.XPATH, ticketXPATH)
    ticket_size = ticket.size
    yTickets = ticket_size['height'] #Gets Y-Coordinate of the Tickets
    return yTickets
def quitBrowser(driver):
    #Quit Broswer
    sleep(1)
    driver.quit()
def printCoordinates(yTicket, ySoldOut):
    print("yKarten:", yTicket)
    print("yAusverkauft:", ySoldOut)
def sendEmail(subject, body):
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['subject'] = subject
    em.set_content(body)
    context = ssl.create_default_context()
    #Send Mail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
def checkAvailability(yTicket, ySoldOut):
    global wasAvailableLastTime
    # Available
    if (yTicket < ySoldOut): # Tickets come BEFORE the soldout headline on Page = Still Available
        if (wasAvailableLastTime == True):
            print("Still Available, no Email send")
        elif (wasAvailableLastTime == False):
            sendEmail("F1 Tickets sind wieder verfügbar!   =)", "Es sind wieder neue F1 Ticket verfügbar: =) \nhttps://tickets.redbullring.com/de/f1/f1-grand-prix-oesterreich-2025/tickets.html")
            print("Available again, Email send")
        wasAvailableLastTime = True

    # Not Available
    elif (yTicket > ySoldOut): # Tickets come AFTER the soldout headline on Page = Sold Out
        if (wasAvailableLastTime == False):
            print("Still NOT Available, no Email send")
        elif (wasAvailableLastTime == True):
            sendEmail("Keine F1 Tickets mehr verfübar!    =(", "Es sind keine F1 Tickets mehr verfügbar: =( \nhttps://tickets.redbullring.com/de/f1/f1-grand-prix-oesterreich-2025/tickets.html")
            print("Not available again, Email send")
        wasAvailableLastTime = False
        print("\n\n")
def delay():
    if intervall < 0:
        exit()
    sleep(intervall)


#Change to while loop with time delay
while True:
    driver = initBrowser(URL)
    yTicket = findCoordinate(ticketXPATH, driver)
    ySoldOut = findCoordinate(soldOutXPATH, driver)
    quitBrowser(driver)
    printCoordinates(yTicket, ySoldOut)
    checkAvailability(yTicket, ySoldOut)
    delay()