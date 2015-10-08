import requests
import dummylcd
import qrencode
from Tkinter import *
import tkFont
from time import sleep
import jsonrpclib
import datetime

class POS:

    def __init__(self,server_url, logfile = None):
        self.createGUI()
#        self.lcd = lcd.HD44780()
        self.lcd = dummylcd.stdout()
        self.server = jsonrpclib.Server(server_url)
        self.logfile = logfile

    def initTransaction(self):
        self.input=''
        self.amt=''
        self.backcounter=0
        self.enter=False
        self.qr_panel,self.address_panel,self.bitamount_panel,self.amount_panel,self.address_panel,self.end_panel=None,None,None,None,None,None

    #returns new address or ""
    def getNewAddress(self,label=None):
        address = ""
        self.wallet.getNewAddress()
        return address

    #returns wallet balance or -1
    def getWalletBalance(self):
        balance = -1
        res = self.server.getbalance();
        balance = res.get('confirmed',0) + res.get('unconfirmed',0)
        return balance

    #returns address balance or -1
    def getAddressBalance(self,address,confirmations='0'):
        balance = -1
        res = self.server.getaddressbalance(address)
        balance = float(res['confirmed'])
        if confirmations == 0:
            balance += float(res.get('unconfirmed',0))
        return balance

    #returns current bitcoin value or -1
    def toBTC(self,v,c='USD'):
        #TODO optionally bitcoinaverage
        payload = {'currency': c, 'value': v}
        to_btc_url = 'https://blockchain.info/tobtc'
        btotal=-1
        try:
            r = requests.get(to_btc_url, params=payload,verify=True)
            if r.status_code == 200:
                btotal=float(r.text) #TODO use Decimal or convert ot satoshi
        except:
            pass
        return btotal

    #returns last USD/BTC rate or -1
    def getBTCRate(self):
        #TODO optionally bitcoinaverage
        ticker_url = 'https://blockchain.info/ticker'
        rate = -1
        try:
            r = requests.get(ticker_url)
            rate = eval(r.text,{},{})['USD']['last']
        except:
            pass
        return rate

    #returns payment total, evaluating if necessary
    def getPaymentTotal(self):
        while True:
            self.getPayment(self.amt)
            if self.amt:
                try:
                    if eval(self.amt,{},{}) <= 0:
                        raise Exception('')
                    if self.amt==str(eval(self.amt,{},{})):
                        break
                    self.amt=str(eval(self.amt,{},{}))
                except:
                    self.amt='0'
        return self.amt

    #gets a single payment line and puts it in self.amt
    def getPayment(self,last_input=''):
        self.input = last_input
        if last_input == '' or last_input == '0':
            self.amt='x'
        old_amt=self.amt
        self.lcd.setBottomLine('$'+last_input)
        self.lcd.printLCD()
        while not self.input == self.amt and old_amt == self.amt:
            if not self.input == last_input:
                last_input=self.input
                self.lcd.setBottomLine('$'+last_input)
                self.lcd.printBottomLine()

    def waitForPaymentOrCancel(self,address,bitamount,confirmations=0):
        confirmed=False
        while not self.backcounter >= 3 and not confirmed:
            if self.getAddressBalance(address,confirmations) >= bitamount:
                confirmed = True
            else:
                sleep(2)
        return confirmed

    #waits for enter to be pressed
    def waitForEnter(self):
        while not self.enter:
            pass
            sleep(0.05)

    #returns payment-URI-encoded QR Code image(100x100px)
    def getQRCode(self,address, amount, label=None, message=None):
        amount = 'amount=' + str(amount) #+ 'X8'
        label = '' if not label else '&label='+label
        message = '' if not message else '&message='+message
        qr_str = 'bitcoin:'+address+'?'+amount + label + message
        print qr_str
        im = qrencode.encode(qr_str,3)
        return im[2].resize((300,300))

    #picks up character input from gui -- in conjunction to the bind_all call
    def key(self,event):
        key = self.getKeycodeValue(event.keycode)
        print 'keycode: '+str(event.keycode)
        if not key == '':
            if len(key) == 1:

                if not key == '\b':
                    if not key == '\n':
                        self.input+=key
                    self.backcounter=0
                self.enter=False
            if key == '\b':
                self.backcounter+=1
                self.input=self.input[:-1]
            if key == '\n':
                self.backcounter=0
                if not self.amt == self.input:
                    self.amt=self.input
                self.input=''
                self.enter=True

    #returns predefined character or '' if incompatable
    def getKeycodeValue(self,keycode):
        if keycode == 79:
            return '7'
        elif keycode == 80:
            return '8'
        elif keycode == 81:
            return '9'
        elif keycode == 82:
            return '-'
        elif keycode == 83:
            return '4'
        elif keycode == 84:
            return '5'
        elif keycode == 85:
            return '6'
        elif keycode == 86:
            return '+'
        elif keycode == 87:
            return '1'
        elif keycode == 88:
            return '2'
        elif keycode == 89:
            return '3'
        elif keycode == 90:
            return '0'
        elif keycode == 91:
            return '.'
        elif keycode == 106:
            return '/'
        elif keycode == 63:
            return '*'
        elif keycode == 104:
            return '\n'
        elif keycode == 22:
            return '\b'
        else:
            return ''

    #creates gui
    def createGUI(self):
        self.gui = Tk()
        w = self.gui.winfo_screenwidth()
        h = self.gui.winfo_screenheight()
        geom = str(w)+'x'+str(h)+'+0+0'
        self.gui.geometry(geom)
        self.gui.bind_all('<Key>',self.key)
        self.gui.configure(background='black')

    #sets gui to bitcoin accepted here image
    def setWaitingGUI(self):
        self.gui.configure(background='black')
        photo = PhotoImage(file='bitcoin_accepted.gif')
        self.wait_panel = Label(self.gui,image = photo,borderwidth=0)
        self.wait_panel.image = photo
        self.wait_panel.pack()

    #sets gui to payment screen
    def setPaymentGUI(self,img,address,bitamount,amount=None):
        self.gui.configure(background='white')
        img.save('qr.gif')
        photo = PhotoImage(file='qr.gif')
        self.qr_panel = Label(self.gui,image = photo)
        self.qr_panel.image = photo
        f=tkFont.Font(family="Helvetica",size=16)
        self.address_panel = Label(self.gui, text = address,font=f)
        self.address_panel.configure(background='white')
        f=tkFont.Font(family="Helvetica",size=20,weight=tkFont.BOLD)
        self.bitamount_panel = Label(self.gui, text= u'\u0E3F'+str(bitamount), font=f)
        self.bitamount_panel.configure(background='white')
        if amount != None:
            self.amount_panel = Label(self.gui, text = '$'+str(amount), font=f)
            self.amount_panel.configure(background='white')
        self.qr_panel.grid(column=0,row=0,columnspan=3,rowspan=3,padx=30,pady=30)
        self.address_panel.grid(column=0,row=3,padx=10)
        self.bitamount_panel.grid(column=3,row=2,padx=3)
        if amount != None:
            self.amount_panel.grid(column=3,row=1,padx=3)

    #clears gui
    def clearGUI(self):
        if self.qr_panel:
            self.qr_panel.grid_forget()
        if self.address_panel:
            self.address_panel.grid_forget()
        if self.bitamount_panel:
            self.bitamount_panel.grid_forget()
        if self.amount_panel:
            self.amount_panel.grid_forget()
        if self.address_panel:
            self.address_panel.grid_forget()
        if self.end_panel:
            self.end_panel.pack_forget()
        if self.wait_panel:
            self.wait_panel.pack_forget()

    #sets gui to confirmation screen
    def setConfirmationGUI(self,bitamount=None):
        str='Payment Confirmed'
        if bitamount:
            str+='\nAmount: '+bitamount
        f=tkFont.Font(family="Helvetica",size=28,weight=tkFont.BOLD)
        self.end_panel=Label(self.gui,text=str,font=f)
        self.end_panel.configure(background='white')
        self.end_panel.pack(pady=160)

    #sets gui to canceled screen
    def setCanceledGUI(self,bitamount=None):
        str='Payment Canceled'
        f=tkFont.Font(family="Helvetica",size=28,weight=tkFont.BOLD)
        self.end_panel=Label(self.gui,text=str,font=f)
        self.end_panel.configure(background='white')
        self.end_panel.pack(pady=160)

    #sets gui to canceled screen
    def setErrorGUI(self,str='Error'):
        f=tkFont.Font(family="Helvetica",size=28,weight=tkFont.BOLD)
        self.end_panel=Label(self.gui,text=str,font=f)
        self.end_panel.configure(background='white')
        self.end_panel.pack(pady=160)

    #executes the steps of a single transaction
    def newTransaction(self):
        try:
            self.setWaitingGUI()
            self.initTransaction()
            self.lcd.setTopLine('Payment Amount')
            self.lcd.printLCD()
            amount=self.getPaymentTotal()
            self.lcd.setTopLine('Payment Entered')
            self.lcd.printLCD()
            retries=3
            for x in range(retries):
                bitamount=self.toBTC(amount)
                if not bitamount == -1:
                    break
            if not bitamount:
                raise Exception('trouble accessing Blockchain')
            #catch both too big (blockchain returns -1) and too small amounts
            if bitamount < 0.0001:
                self.logEntry('BAD',amount,bitamount)
                self.lcd.setTopLine('Bad Amount')
                self.lcd.printLCD()
                self.enter=False
                self.waitForEnter()
                self.clearGUI()
                return
            for x in range(retries):
                address = ""
                try:
                    #res = self.server.addrequest(amount)
                    #address = res['address']
                    address=u'12CVhw1GZEKuSYva3ByqcxPtbQSoJ9dCPo'
                except:
                    pass #TODO
                if address:
                    break

            image=self.getQRCode(address,bitamount)
            self.clearGUI()
            self.setPaymentGUI(image,address,bitamount,amount)
            self.lcd.setTopLine('QR Code Ready')
            self.lcd.printLCD()
            confirmed=self.waitForPaymentOrCancel(address,bitamount)
            self.clearGUI()
            if confirmed:
                self.lcd.setTopLine('Payment Approved')
                self.lcd.printLCD()
                self.setConfirmationGUI()
                self.logEntry('OK',amount,address,bitamount)
            else:
                self.logEntry('CANC',amount,address,bitamount)
                self.lcd.setTopLine('Payment Canceled')
                self.lcd.printLCD()
                self.setCanceledGUI()
            #self.archiveAddress(address)
            self.enter=False
            self.waitForEnter()
            self.clearGUI()
        except Exception, err:
            print err, sys.exc_info()[0]
            self.lcd.setTopLine('Network Error')
            self.enter=False
            self.waitForEnter()
            self.clearGUI()

    def logEntry(self,code,amount,address,bitamount):
        if self.logfile:
            try:
                log = open(self.logfile,'a')
                log.write(",".join((datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),code,amount,address,str(bitamount))) + "\n")
                log.close()
            except Exception, err:
                print err


    #main loop for transactions
    def transactionLoop(self):
        while True:
            self.newTransaction()