import sys
sys.path.append('..')
import os
from math import *
import time
import numpy as np
from scao.quaternion import Quaternion
from scao.scao import SCAO
from scao.stabAlgs import PIDRW, PIDMT
import rcpy.mpu9250 as mpu9250
import rcpy.motor as motor
from flask import Flask
from threading import Thread
import logging
from hardware.hardwares import Hardware


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

imu = mpu9250.IMU(enable_dmp = True, dmp_sample_rate = 100, enable_magnetometer = True)

mots = [motor.Motor(1), motor.Motor(2), motor.Motor(3)] #x,y,z

# Algorithmes de stabilisation

lx,ly,lz = 0.1,0.1,0.1 #longueur du satellite selon les axes x,y,z
m = 1 #masse du satellite
M = np.array([[0.],[0.],[0.]]) # vecteur du moment magnétique des bobines
I = np.diag((m*(ly**2+lz**2)/3,m*(lx**2+lz**2)/3,m*(lx**2+ly**2)/3)) # Tenseur inertie du satellite
J = 1 # moment d'inertie des RW
SCAOratio = 0
RW_P = 3
RW_dP = 2
RW_D = 3
MT_P = 0
MT_dP = 0
MT_D = 50000

#####
# paramètres hardware
n_windings = 500
r_wire = 125e-6
r_coil = 75e-4
U_max = 5
mu_rel = 31
J = 1 # moment d'inertie des RW
# r_coil, r_wire, n_coils, mu_rel, U_max
mgt_parameters = r_coil, r_wire, n_windings, mu_rel, U_max
#####

stab = SCAO(PIDRW(RW_P,RW_dP,RW_D),PIDMT(MT_P,MT_dP,MT_D),SCAOratio,I,J) #stabilisateur
hardW = Hardware(mgt_parameters, 'custom coil')  #hardware (bobines custom)

Qt = Quaternion(.5,.5,.5,.5)

class Runner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.M = np.array([[0],[0],[0]])
        self.U = np.array([[0],[0],[0]]) #tension
        self.W = np.array([[0],[0],[0]])
        self.B = np.array([[0],[0],[0]])
        self.Q = Quaternion(1,0,0,0)

    def run(self):
        nbitBeforeMagMeasure = round(1/0.1)
        nbit = 0
        while True:
            if nbit%nbitBeforeMagMeasure == 0:
                for mot in mots:
                    mot.set(0)
                mot.set(0)
                time.sleep(.1)
                state = imu.read()
                self.Q = Quaternion(*state['quat'])
                self.B = self.Q.V2R(np.array([[i*10**-6] for i in state['mag']]))
                stab.setMagneticField(self.B)

            else:
                state = imu.read()
                self.Q = Quaternion(*state['quat'])
                self.W = self.Q.V2R(np.array([[i*pi/360] for i in state['gyro']]))

                # Sauvegarder les valeurs actuelles:
                stab.setAttitude(self.Q)
                stab.setRotation(self.W)

                # Prise de la commande de stabilisation
                dw, self.M = stab.getCommand(Qt) #dans Rv
                self.U, self.M = hardW.getRealCommand(dw, self.M)

                for nomot, mot in mots:
                    mot.set(-self.U[nomot][0]/U_max)
                time.sleep(.1)
            nbit += 1

runner = Runner()
runner.start()

app=Flask(__name__)

@app.route('/')
def index():
    state = imu.read()

    Q = Quaternion(*state['quat'])
    W = Q.V2R(np.array([[i*pi/360] for i in state['gyro']]))

    return repr(runner.M)+"<br/>"+repr(W)+"<br/>"+repr(runner.B)+"<br/>"+repr(Q.vec())

app.run(host='0.0.0.0')