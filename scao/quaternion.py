import numpy as np

class Quaternion:
    def __init__(self,a,b,c,d):
        norm = a**2+b**2+c**2+d**2
        self.a = a/norm
        self.b = b/norm
        self.c = c/norm
        self.d = d/norm
        self.tmsave = None
        self.tminvsave = None
    def inv(self):
        return Quaternion(self.a,-self.b,-self.c,-self.d)
    def vec(self):
        return np.array([[self.a],[self.b],[self.c],[self.d]])
    def __mul__(self,value):
        return Quaternion(
            self.a*value.a - self.b*value.b - self.c*value.c - self.d*value.d,
            self.b*value.a + self.a*value.b - self.d*value.c + self.c*value.d,
            self.c*value.a + self.d*value.b + self.a*value.c - self.d*value.d,
            self.d*value.a - self.c*value.b + self.b*value.c + self.a*value.d,
        )
    def tm(self): #transfer matrix from Rr to Rv i.e. X_Rr = M * X_Rv
        if self.tmsave is None:
            q0,q1,q2,q3 = self.a,sef.b,self.c,self.d
            self.tmsave = np.array(
                [[2*(q0**2+q1**2)-1, 2*(q1*q2-q0*q3)  , 2*(q1*q3+q0*q2)  ],
                 [2*(q1*q2+q0*q3)  , 2*(q0**2+q2**2)-1, 2*(q2*q3-q0*q1)  ],
                 [2*(q1*q3-q0*q2)  , 2*(q2*q3+q0*q1)  , 2*(q0**2+q3**2)-1]]
            )
        return self.tmsave
    def tminv(self): #transfer matrix from Rr to Rv i.e. X_Rr = M * X_Rv
        if self.tminvsave is None:
            self.tminvsave = np.linalg.inv(self.tm())
        return self.tminvsave