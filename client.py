import requests 
from Pyfhel import Pyfhel, PyCtxt
import os


url = 'http://192.168.1.5:5000/api' # server side
basePath = str(os.getcwd())


def createHE(userID):

    path = os.path.join(str(userID))
    os.makedirs(path)

    HE = Pyfhel()    
    HE.contextGen(p=65537, m=2**12) 
    HE.keyGen() # Generates both a public and a private key
    os.chdir(userID)

    HE.savepublicKey((userID+".pk"))
    HE.saveContext((userID+".con"))
    HE.savesecretKey((userID+"Private"+".pk"))
    balance= 0.0
    balance = HE.encryptFrac(balance)
    balance.to_file("balance.ctxt")
    f = open("transfer.txt","w")
    f.write("0")
    f.close()

def register():
    userName = input("Enter Username ")
    password = input("Enter Password ")
    iban = input("Enter Iban Address")
    jsonObject ={
            'username' : userName ,
            'password' : password ,
            'iban' : iban
    } 
    requests.post(url+'/users', json=jsonObject)

    createHE(userName)
    tempPath = (basePath+"//"+userName+"//")
    fPath = (tempPath+userName+".pk")

    files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))

    files = {'file': open((tempPath+"/transfer.txt"),'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))

    tempPath = (basePath+"//"+userName+"//")
    fPath = (tempPath+userName+".con")
    files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))

    tempPath = (basePath+"//"+userName+"//")
    fPath = (tempPath+"balance.ctxt")
    files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))


def getNewBalance(HE , userName , password):
    with requests.get(url+'/balance',  auth=(userName, password), stream=True) as r:
                r.raise_for_status()
                with open("balance.ctxt", 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):  
                        f.write(chunk)
    c_res = PyCtxt(pyfhel=HE, fileName="balance.ctxt", encoding=float)
    print(c_res.decrypt())

def getNewTransfer( userName , password):
    with requests.get(url+'/transferFile',  auth=(userName, password), stream=True) as r:
                r.raise_for_status()
                with open("transfer.txt", 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):  
                        f.write(chunk)
    

def doTransfer(userName , password , money):
    HE = Pyfhel()    
    HE.contextGen(p=65537, m=2**12) 
    os.chdir(basePath+"/"+userName)
    HE.restoreContext((userName+".con"))
    HE.restorepublicKey((userName+".pk"))
    HE.restoresecretKey((userName+"Private"+".pk"))
    f = open("transfer.txt","w")
    f.write("0")
    f.close()    
    moneyT = HE.encryptFrac(money)
    moneyT.to_file("temp.ctxt")
    try:
        tempPath = (basePath+userName+"/")
        fPath = (tempPath+"temp.ctxt")
        files = {'file': open(fPath,'rb')}
    except:
        tempPath = (basePath+"\\"+userName+"/")
        fPath = (tempPath+"temp.ctxt") 
        files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))

    fPath = (tempPath+"transfer.txt")
    files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))
    requests.post(url+'/deposit', auth=(userName, password))

# Para çekme yatırma işlemi için fonksiyon 
def moneyOperasyon(userName , password , op):
    HE = Pyfhel()    
    HE.contextGen(p=65537, m=2**12) 
    os.chdir(basePath+"/"+userName)
    HE.restoreContext((userName+".con"))
    HE.restorepublicKey((userName+".pk"))
    HE.restoresecretKey((userName+"Private"+".pk"))
    moneyT = 0.0
    try:
        moneyT = float(input("Enter money : "))
        opB = moneyT
    except:
        print ("Wrong !!!")
        return 
    moneyT = HE.encryptFrac(moneyT)
    moneyT.to_file("temp.ctxt")
    tempPath = (basePath+"//"+userName+"//")
    fPath = (tempPath+"temp.ctxt")
            
    files = {'file': open(fPath,'rb')}
    requests.post(url+'/fileUpload', files=files, auth=(userName, password))
    if op == 1:
        requests.post(url+'/deposit', auth=(userName, password))
    else:
        c_res = PyCtxt(pyfhel=HE, fileName="balance.ctxt", encoding=float)
        ourB = str(c_res.decrypt())
        if int(opB) > int(float(ourB)) :
            print(" Çekmek istediğiniz para bakiyenizden fazla !!! ")
        else:
            requests.post(url+'/withdraw', auth=(userName, password))
    getNewBalance(HE,userName,password)


def login():
    userName = input("Enter Username")
    password = input("Enter Password")
    print("1- Banka para yatırma")
    print("2- Banka para çekme")
    print("3- Banka para transferi")
    operasyon = input(":")
    


    if os.path.exists(basePath+"/"+userName) :

        HE = Pyfhel()    
        HE.contextGen(p=65537, m=2**12) 
        os.chdir(basePath+"/"+userName)
        HE.restoreContext((userName+".con"))
        HE.restorepublicKey((userName+".pk"))
        HE.restoresecretKey((userName+"Private"+".pk"))
        getNewTransfer(userName,password)
        f = open("transfer.txt","r")
        line = f.read()
        print(line)
        if (line != "0"): 
           doTransfer(userName ,password,float(line))
        f.close()
        getNewBalance(HE,userName,password)
        if operasyon =="1":
            moneyOperasyon(userName , password , 1)
        elif operasyon =="2":
            moneyOperasyon(userName,password,0)
        elif operasyon =="3":
            HE = Pyfhel()    
            HE.contextGen(p=65537, m=2**12) 
            os.chdir(basePath+"/"+userName)
            HE.restoreContext((userName+".con"))
            HE.restorepublicKey((userName+".pk"))
            HE.restoresecretKey((userName+"Private"+".pk"))
            moneyT = 0.0
            try:
                moneyT = float(input("Enter money : "))
                opB = moneyT
            except:
                print ("Wrong !!!")
                return 
            c_res = PyCtxt(pyfhel=HE, fileName="balance.ctxt", encoding=float)
            ourB = str(c_res.decrypt())
            if int(opB) > int(float(ourB)) :
                print(" Transfer istediğiniz para bakiyenizden fazla !!! ")
            else:
                moneyT = HE.encryptFrac(moneyT)
                moneyT.to_file("temp.ctxt")
                tempPath = (basePath+"//"+userName+"//")
                fPath = (tempPath+"temp.ctxt")
                iban = input("Enter karsi taraf iban")
                jsonObject ={
                    'iban' : iban,
                    'sendMoney' : opB
                } 
                        
                files = {'file': open(fPath,'rb')}
                requests.post(url+'/fileUpload', files=files, auth=(userName, password))
                requests.post(url+'/transfer',auth=(userName,password) ,json=jsonObject)
        else:
            print("Hatalı seçim")
    else:
        print("User file not found")

while(1):
    os.chdir(basePath)
    print("1- Register")
    print("2- Login")
    print("3- Exit")
    log_or_reg = input(": ")
    if log_or_reg =="1":
        register()


    elif log_or_reg=="2":
        login()
    elif log_or_reg=="3":
        break
    else:
        print("Wrong chooses")


