from ..core.util.unit import *
from ..core.experiment import Experiment
if __name__ == '__main__':
    from lab.in_lab import *
# --- do not change anything above this line ---



@Experiment(True, ts_in)
def exp(tof):
    t0 = 2*s
    t1 = 5*s # MOT load time
    t2 = 500*ms # time between [MOT load finished = ZM off] and [PGC start = B off]
    # t3 = 10*ms # time of flight TOF
    t3 = tof
    t4 = 300*us # MOT probe shine time
    t5 = 100*ms
    # t6 = t3 -200*us # TOF EMCCD trigger after MOT drop
    t6 = t3-3*ms
    if (t6<=100*us):
        t6=100*us
    t7 = 1*ms # TOF EMCCD trigger pulse width
    t8 = t0+t1+t2 - 300*ms
    t9 = 1*ms
    t10 = 100*ms
    t11 = 5*ms # camera exposure time
    t0_zm = t0-1*s
    t_MotOff2Boff = 500*us
    t12 = 50*us # time between AOM off and servo1303 unlock
    t13 = -2.5*ms # time between [B off = PGC start] and [servo651 ramp to PGC freq]
    t14 = 2.5*ms # PGC duration time
    t_trigWidth = 100*us

    # time points that depends on the above time parameters
    t_PgcStart = t0+t1+t2 # time point, PGC start = B off
    t_TofStart = t0+t1+t2+t14

            
    @TSChannel(channel=1, polarity=0)
    def ts1_IGBT0():
        return [(t0+t1+t2),(t0+t1+t2+2*s)]

    @TSChannel(channel=2, polarity=0)
    def ts2_IGBT12():
        return []

    @TSChannel(channel=3, polarity=1)
    def ts3_IGBT34():
        return []

    @TSChannel(channel=4, polarity=0)
    def ts4_niDacTrig():
        return []

    @TSChannel(channel=5, polarity=1)
    def ts5_FieldUnlock():
        return [0, (t0+t1+t2+10*ms)]

    @TSChannel(channel=6, polarity=0)
    def ts6_ZmrpShutter():
        return [(t0+t1),(t0+t1+t2+2*s)]

    @TSChannel(channel=7, polarity=1)
    def ts7_MotAomTTL():
        return [(t0+t1+t2+t14),(t0+t1+t2+t14+t3), (t0+t1+t2+t14+t3+t4), (t0+t1+t2+t14+t6+t11+100*ms)]

    @TSChannel(channel=8, polarity=0)
    def ts8_ZMAomTTL():
        return [t0_zm, (t0+t1)]

    @TSChannel(channel=9, polarity=0)
    def ts9_servo1303RampTrig():
    #     return [(t0+t1+t2+t13),(t0+t1+t2+t11+1*ms)]
        return []


    @TSChannel(channel=10, polarity=0)
    def ts10_EMCCD_trigger():
        ret = [] # ret is short for result
        N = 1 # when MOT is fully loaded, take N pictures 
        for n in range(0, N):
            ret.append(t8 +t10*n)
            ret.append(t8+ t10*n +t9)
        ret.extend( [(t0+t1+t2+t6+t14), (t0+t1+t2+t6++t14+t7)] )
    #     print(ret)
        return ret


    @TSChannel(channel=11, polarity=1)
    def ts11_MotShutterTTL():
        return [t0,(t0+t1+t2+t6+t11+1*ms+500*ms)]

    @TSChannel(channel=12, polarity=0)
    def ts12_servo1303UlkTTL():
    #     return [(t0+t1+t2+t12),(t0+t1+t2+1*s)]
        return []

    # @TSChannel(channel=13, polarity=0)
    # def ts13_651offsetLockVcoRampTrig():
    # #     return [(t0+t1+t2+t13),(t0+t1+t2+t11+1*ms)]
    #     return [(t_PgcStart+t13),(t_PgcStart+t13+100*us),(t_PgcStart+t14), (t_PgcStart +t14+t_trigWidth),(t0+t1+t2+t6+t11+100*ms),(t0+t1+t2+t6+t11+100*ms+100*us)]


    @TSChannel(action=pulse, channel=13, polarity=0)
    def ts13_651offsetLockVcoRampTrig():
        return [(t_PgcStart+t13),(t_PgcStart+t14),(t0+t1+t2+t6+t11+100*ms),]

    @TSChannel(channel=14, polarity=0)
    def ts14_326intensityServoSetpointRampTrig():
        return [(t_PgcStart+t13),(t_PgcStart+t13+t_trigWidth),(t_PgcStart),(t_PgcStart+t_trigWidth),(t_PgcStart+t14+500*us), (t_PgcStart +t14+500*us+t_trigWidth)]

    @TSChannel(channel=15, polarity=0)
    def ts15_MotAomServoUlkTTL():
        return [(t0+t1+t2+t14), (t0+t1+t2+t14+t6+t11+100*ms)]

    @TSChannel(channel=16, polarity=0)
    def ts16_coilVrefTrig():
        return []

    @TSChannel(channel=17, polarity=0)
    def ts17_410451IntensityServoSetpointRampTrig():
        return [(t_PgcStart+t13),(t_PgcStart+t13+t_trigWidth),(t_PgcStart),(t_PgcStart+t_trigWidth),(t_PgcStart+t14+500*us), (t_PgcStart +t14+500*us+t_trigWidth)]

    @TSChannel(channel=18, polarity=0)
    def ts18_410451IntensityServoDisableTTL():
        return [(t_TofStart), (t0+t1+t2+t14+t6+t11+100*ms)]

    @TSChannel(channel=19, polarity=1)
    def ts19_410451AomRfSwitchTTL():
        return [(t0+t1+t2+t14),(t0+t1+t2+t14+t3), (t0+t1+t2+t14+t3+t4), (t0+t1+t2+t14+t6+t11+100*ms)]

async def main():
    for tof in [1, 2, 3, 4]:
        await exp(tof=tof*ms)

