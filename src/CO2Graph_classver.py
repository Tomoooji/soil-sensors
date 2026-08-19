import csv
import serial
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.widgets as wg

class Graph:
    LOGFILE="testlog.txt"
    SAVEFILE="SaveData.txt"
    FORMAT="%Y/%m/%d %H:%M:%S.%f"

    def __init__(self,ref1=[400,432],ref2=[4000,327]):
        self.log_time=[]
        self.log_volt=[]
        self.log_conc=[]
        self.now_time=[]
        self.now_volt=[]
        self.now_conc=[]
        self.lim_time=dt.timedelta(minutes=5)
        self.lim_volt=(300,500)
        self.lim_conc=(350,1200)        
        self.P0,self.E0=ref1[0],ref1[1]
        self.P1,self.E1=ref2[0],ref2[1]
        self.k=1/(self.E0-self.E1)*np.log10(self.P1/self.P0)
        self.max_volt=self.E0
        self.running=True
        self.saving=False
    
    def loop(self):
        self.GUIsetup()
        with open(self.LOGFILE,"a") as self.log_file: 
            with open(self.SAVEFILE,"a") as self.save_file:
                self.connect()
                self.static()
                while self.running:
                    self.log()
                    self.update()
        
    def setup(self,mode=None):
        print(mode)
        if not mode:
            print(f"保存先ファイル({self.LOGFILE})の初期化を行いますか？")
            mode=input(">> Y/N/C : ")
        else:
            plt.close(self.fig1)
        match mode:
            case "Y":
                with open(self.LOGFILE,"w") as data:
                    print("",end="",file=data)
                    #print(f"{self.P0},{self.E0},{self.P1},{self.E1}",file=data)
                    
                return "reset"
            case "N":
                ...
                #with open(self.LOGFILE,"a") as data:
                    #print(f"{self.P0},{self.E0},{self.P1},{self.E1}",file=data)
                return "new"
            case "C":
                with open(self.LOGFILE,"r") as data:
                    log_raw=[[dt.datetime.strptime(time,self.FORMAT),float(volt),float(conc)] if not fourth else None for time,volt,conc,fourth in csv.reader(data)]
                    log_data=[data for data in log_raw[::-1] if data and data[0] > (dt.datetime.now()-self.lim_time)]
                    if len(log_data):
                        self.log_time=[val[0] for val in log_data]
                        self.log_volt=[val[1] for val in log_data]
                        self.log_conc=[val[2] for val in log_data]
                #with open(self.LOGFILE,"a") as data:
                    #print(f"{self.P0},{self.E0},{self.P1},{self.E1}",file=data)
                return "continue"
            case _:
                print("誤った文字が入力されました。")
                if input("プログラムを終了しますか?")=="N":
                    return self.setup()
                else:
                    self.close()
                    return "break"

    def GUIsetup(self):
        self.fig1,ax=plt.subplots(3,1)
        self.fig1.suptitle(f"Will you reset past data in {self.LOGFILE} ?")#(f"保存先ファイル({self.FILE})の初期化を行いますか？")
        reset=wg.Button(ax[0],"reset and new graph")#"リセットして新規表示")
        newgh=wg.Button(ax[1],"new graph without reset")#"リセットせず新規表示")
        contn=wg.Button(ax[2],"graph with past data")#"直前の値と一緒に表示")
        reset.on_clicked(lambda event:self.setup("Y"))
        newgh.on_clicked(lambda event:self.setup("N"))
        contn.on_clicked(lambda event:self.setup("C"))
        plt.show()

    def connect(self):
        try:
            self.ser=serial.Serial(port='COM8',baudrate=9600)#,timeout=0)
        except serial.serialutil.SerialException:
            print("接続失敗")
            if input("再接続を試みますか？")=="Y":
                self.connect()
            else:
                self.close()
    
    def log(self):
        gained_time=dt.datetime.now()
        row=self.ser.readline().decode().replace('\n','').replace('\r','')
        gained_volt=float(row if row else 0)
        if gained_volt>500:
            gained_volt=0
            return
        if gained_volt>self.max_volt:
            self.max_volt=gained_volt
            self.maxlab.set_text(f"max-mV:{self.max_volt}")
        calced_conc=self.calcconc(gained_volt)
        self.log_file.write(f"{gained_time.strftime(self.FORMAT)},{gained_volt},{calced_conc},\n")
        if self.saving:
            self.save_file.write(f"{gained_time.strftime(self.FORMAT)},{gained_volt},{calced_conc},\n")
        #"""
        if len(self.now_time)>1000:
            self.log_time.clear()
            self.log_volt.clear()
            self.log_conc.clear()
            del self.now_time[:300]
            del self.now_volt[:300]
            del self.now_conc[:300]
        #"""
        self.now_time.append(gained_time)
        self.now_volt.append(gained_volt)
        self.now_conc.append(calced_conc)
    
    def static(self):
        self.fig,self.ax=plt.subplots(2,2,gridspec_kw=dict(width_ratios=[1,1],height_ratios=[5,1]))
        self.reflab=self.fig.supxlabel(f"Ref:{self.P0}ppm→{self.E0}mV, {self.P1}ppm→{self.E1}mV")
        cid=self.fig.canvas.mpl_connect("close_event",lambda event:self.close())
        self.ax[0,0].set_title("Sensor[mV]")
        self.ax[0,1].set_title("CO2[ppm]")
        self.line_logV=self.ax[0,0].plot(0,0,color="pink")[0]
        self.line_nowV=self.ax[0,0].plot(0,0,color="green")[0]
        self.line_logC=self.ax[0,1].plot(0,0,color="pink")[0]
        self.line_nowC=self.ax[0,1].plot(0,0,color="green")[0]
        self.maxlab=self.ax[1,0].text(0.5,0.5,f"max-mV:{self.max_volt}",verticalalignment='center',horizontalalignment='center',transform=self.ax[1,0].transAxes)
        self.btn=wg.Button(self.ax[1,1],f"save to {self.SAVEFILE}")
        self.btn.on_clicked(lambda event:self.save())
        self.fig.suptitle(self.LOGFILE)
    
    def update(self):
        self.line_nowV.set_data(self.now_time,self.now_volt)
        self.ax[0,0].set_ylim(*self.lim_volt)
        self.ax[0,0].set_xlim((time:=dt.datetime.now())-self.lim_time,time)
        self.ax[0,0].grid()
        self.line_nowC.set_data(self.now_time,self.now_conc)
        self.ax[0,1].set_ylim(*self.lim_conc)
        self.ax[0,1].set_xlim((time:=dt.datetime.now())-self.lim_time,time)
        self.ax[0,1].grid()
        
        #self.reflab.set_text(f"Clib:{self.P0}ppm→{self.E0}mV, {self.P1}ppm→{self.E1}mV")
        plt.pause(0.1)
        
        self.lim_volt=self.ax[0,0].get_ylim()
        self.lim_conc=self.ax[0,1].get_ylim()
        self.ax[0,0].grid()
        self.ax[0,1].grid()

    def save(self):
        self.saving=not self.saving
        if self.saving:
            self.btn.label.set_text(f"saving to {self.SAVEFILE} now!")
            print(f"start saving as {self.SAVEFILE}")
            self.log_file.write(f"{self.P0},{self.E0},{self.P1},{self.E1}\n")
        else:
            self.btn.label.set_text(f"save to {self.SAVEFILE}")
            print(f"stop saving to {self.SAVEFILE}")
            #self.save_file.close()

    def close(self,event=None):
        if event:
            print(event)
        self.running=False
        print("close program")
    
    def calcconc(self,E):
        return self.P0*(10**(self.k*(self.E0-E)))

if __name__=="__main__":
    main=Graph()
    main.loop()