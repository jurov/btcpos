#!/usr/bin/python
import posgui
import threading
import Queue

identifier=''
forwardingaddress=''
password=''
logfile=None
#eg: identifier='6ne3m2m7-6534-2k6l-2h1b-59v2xm0g8yio'
#    password='mypassword'
#    forwardingaddress='17yHkgQooxxMdB7iqNbBXDrV8YdMrMes5d'
#    logfile='/path/to/posgui.csv'

p= posgui.POS('http://localhost:7777', logfile)
t= threading.Thread(target=p.transactionLoop)
t.start()
p.gui.mainloop()
