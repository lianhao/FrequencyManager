import os
import time
import argparse
import logging
import grpc
from concurrent import futures
import rpcNFM_pb2 as messagesNFD # Simplified usage
import rpcNFM_pb2_grpc as rpcNFD

procInfoDir="/sys/devices/system/cpu"
desiredFreqStats=["cpuinfo_min_freq","scaling_driver","cpuinfo_cur_freq","energy_performance_preference","cpuinfo_max_freq","scaling_cur_freq","scaling_governor","scaling_available_governors"]

coreCount = 0
errorStr=""
sysFreqInfo={}

VersionStr="19.02.20 Build 2"

logger = logging.getLogger(__name__)

# just a wrapper routine for a thread sleeping.  In case needs to be OS specific or something
def Sleep(seconds):
    try:
        time.sleep(seconds)
        
    except BaseException:
        pass

def SleepMs(milliseconds):
    Sleep(float(milliseconds)/1000.0)    

def GetBaseDir():
    global procInfoDir
    return procInfoDir
        
def ReadFromFile(Filename):
    try:
        file = open(Filename,'rt')
        if None == file:
            return "N/A"
    except Exception:
        return "Error Reading From File: {0}".format(Filename)

    return file.read().strip()
    
def WriteToFile(Filename,value):
    try:
        value=str(value)
        file = open(Filename,'wt')
        if None == file:
            return "N/A"

        file.write(value)
        file.close()
        
    except Exception as Ex:
        global errorStr
        errorStr = "Error Writing [{0} to File: {1}: {2}".format(value,Filename,Ex)
        return False
        
    return True
    #return file.write(read().strip()

class NodeFrequencyManager(rpcNFD.NodeFrequencyManagerServiceServicer):
    def __init__(self):
        try:
            self._getFrequencyInfo()
        except:
            pass

    def _getFrequencyInfo(self):
        retMap={}
        global coreCount
        for cpuDir in os.listdir(GetBaseDir()):
                if not 'cpu' in cpuDir:
                    continue
                
                if cpuDir in ['cpufreq','cpuidle']: #don't want these directories
                    continue
                    
                coreCount+=1

                nextDir = GetBaseDir() + "/"  + cpuDir + "/cpufreq"
                for statRoot, statDirs, statFiles in os.walk(nextDir):
                    for file in statFiles:
                        if file in desiredFreqStats:
                            readFile = GetBaseDir() + "/"  + cpuDir + "/cpufreq/" + file
                            key = "{0}.{1}".format(cpuDir,file)
                            
                            retMap[key] = ReadFromFile(readFile)
                            
        
        
        return retMap
        
    def _getCoreFrequencyStat(self,coreNum,stat):
        global coreCount
        if coreNum < 0 or coreNum > coreCount-1:
            return -1
            
        return ReadFromFile(GetBaseDir() + "/cpu"  + str(coreNum) + "/cpufreq/" + stat)

    def _setCoreFrequencyStat(self,coreNum,stat,value):
        global coreCount
        
        if coreNum < 0 or coreNum > coreCount-1:
            return -1
            
        if WriteToFile(GetBaseDir() + "/cpu"  + str(coreNum) + "/cpufreq/" + stat,value):
            return True
        return WriteToFile(GetBaseDir() + "/cpu"  + str(coreNum) + "/cpufreq/" + stat,value)
        
        
    def _getCoreCurrentFrequency(self,coreNum):
        global coreCount
        if coreNum < 0 or coreNum > coreCount-1:
            return -1
            
        return self._getCoreFrequencyStat(coreNum,"cpuinfo_cur_freq")
        
    def _setCoreFrequency(self,coreNum,frequency):
        global coreCount, errorStr

        try:
            coreNum = int(coreNum)
            frequency = int(frequency)
        except:
            errorStr = "Invalid coreNum/Frequency: {0}/{1}".format(coreNum,frequency)
            return False
            
        if coreNum < 0 or coreNum > coreCount-1:
            errorStr = "Invalid coreNum: {0}".format(coreNum)
            return False
            
        coreMin = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_min_freq"))
        coreMax = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_max_freq"))
        
        if frequency > coreMax:
            errorStr = "Cannot set core #{0} frequency to {1}, maximum is {2}".format(coreNum,frequency,coreMax)
            return False
        
        if frequency < coreMin:
            errorStr = "Cannot set core #{0} frequency to {1}, minimum is {2}".format(coreNum,frequency,coreMin)
            return False

        # Might fail if you try to set max to be > min
        if False == self._setCoreFrequencyStat(coreNum,"scaling_max_freq",frequency):
            self._setCoreFrequencyStat(coreNum,"scaling_min_freq",frequency)
            return self._setCoreFrequencyStat(coreNum,"scaling_max_freq",frequency)
            
        return self._setCoreFrequencyStat(coreNum,"scaling_min_freq",frequency)
        

    def _setCoreFrequencyPercent(self,coreNum,percentage):
        global coreCount
        if coreNum < 0 or coreNum > coreCount-1:
            return False
            
        coreMin = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_min_freq"))
        coreMax = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_max_freq"))
        
        restultingFreq = (coreMax-coreMin) * (float(percentage)/100.0) + coreMin
        return self._setCoreFrequency(coreNum,restultingFreq)
            
    def _setAllCoreFrequency(self,frequency):
        for coreNum in range(0,coreCount):
            self._setCoreFrequency(coreNum,frequency)

        return True

    def _setAllCoreFrequencyPercent(self,Percent):
        for coreNum in range(0,coreCount):
            if False == self._setCoreFrequencyPercent(coreNum,Percent):
                global errorStr
                logger.error(errorStr)
                
        return True
                
    def _doRandom(self):
        import random
        for coreNum in range(0,coreCount):
            percent = random.randint(0,100)
            if not self._setCoreFrequencyPercent(coreNum,percent):
                pass
                #print (coreNum,percent)
                
    def _doSine(self):
        from math import sin,pi

        Fs=8000
        f=500
        sample=coreCount
        a=[0]*sample
        for n in range(sample):
            a[n]=sin(2*pi*f*n/Fs)/2
        
        for coreNum in range(0,coreCount):
            self._setCoreFrequencyPercent(coreNum,a[coreNum]*100 + 50)

    def Set_Core_Frequency(self, request, context):
        logger.info("Processing Set_Core_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setCoreFrequency(request.coreNum,request.Frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response
    
    def Set_All_Core_Frequency(self, request, context):
        logger.info("Processing Set_All_Core_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setAllCoreFrequency(request.Frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response

    def Set_Core_Percent_Frequency(self, request, context):
        logger.info("Processing Set_Core_Percent_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setCoreFrequencyPercent(request.coreNum,request.Frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response
        
    def Set_All_Core_Percent_Frequency(self, request, context):
        logger.info("Processing Set_All_Core_Percent_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setAllCoreFrequencyPercent(request.frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response

    def Get_Core_FrequencyInfo(self, request, context):
        logger.info("Processing Get_Core_Frequency request")

        response = messagesNFD.CoreFrequencyInfo()
        errorStr="OK"
        response.CoreNumber = request.CoreNumber
        response.MaxFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"cpuinfo_max_freq"))
        response.MinFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"cpuinfo_min_freq"))
        response.CurrentFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"scaling_cur_freq"))
        successResp = messagesNFD.ServiceResponse()
        successResp.Success = errorStr == "OK"
        successResp.Reason = errorStr
        response.Response = successResp

        return response

    def Set_Random_Frequencies(self, request, context):
        logger.info("Setting frequencies to reandom pattern")
        response = messagesNFD.CoreFrequencyInfo()
        self._doRandom()
        response.Success = True
        response.Reason = "OK"

        return response

    def Set_SineWave_Frequencies(self, request, context):
        logger.info("Setting frequencies to sine wave pattern")
        response = messagesNFD.ServiceResponse()
        self._doSine()
        response.Success = True
        response.Reason = "OK"

        return response

    
def runAsService(hostAddr,hostPort):
    print("Launching Node Frequency Manager at {0}:{1}. Version: {2}".format(hostAddr,hostPort,VersionStr))

    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rpcNFD.add_NodeFrequencyManagerServiceServicer_to_server(NodeFrequencyManager(),server)

    except Exception as Ex:
        logger.error("Error Starting NFM:")
        logger.error(str(Ex))
        return
    
    try:
        server.add_insecure_port(hostAddr +':' + str(hostPort))
        server.start()
        logger.debug("NFM Started")
    except Exception as Ex:
        logger.error("Error Starting NFM:")
        logger.error(str(Ex))
        return

    # server returns, so let's just spin for a while
    try:
        while True:
            SleepMs(1000)

    except KeyboardInterrupt:
        server.stop(0)


# Go initialize some stuff to be used later            
#sysFreqInfo = getFrequencyInfo()

#SetAllCoreFrequencyPercent(43)
#SetAllCoreFrequencyPercent(1)
#doRandom()

#raw_input(" Press Key to set to Min")
#SetAllCoreFrequencyPercent(0)

#raw_input("Press Key to set to half")
#SetAllCoreFrequencyPercent(50)

#raw_input("Press Key to set to full")
#SetAllCoreFrequencyPercent(100)

#raw_input("Press Key to set to pretty")
#doSine()
#doRandom()

#if False:
#  for percent in range (0,101,10):
#    print("Setting All Cores Frequency to {0} percent".format(percent))
#    SetAllCoreFrequencyPercent(percent)
#    Sleep(4)
    

def main():
    parser = argparse.ArgumentParser(description='Node Frequency Manager')
    parser.add_argument("-c","--connect",help="ip:port to listen on.",type=str,required=False)
    parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)

    try:
        args = parser.parse_args()
        if None == args.verbose:
            _VerboseLevel = 0
        else:
            _VerboseLevel = args.verbose

    except:
        return

    if 3 <= _VerboseLevel:
        _VerboseLevel = logging.DEBUG

    elif 2 == _VerboseLevel:
        _VerboseLevel = logging.INFO

    elif 1 == _VerboseLevel:
        _VerboseLevel = logging.WARNING

    else:
        _VerboseLevel = logging.ERROR

    logging.basicConfig(level=_VerboseLevel,format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M')

    if None == args.connect:
        args.connect = "0.0.0.0:5000"
        logger.info("Connection information not provided, using default: " + args.connect)

    if not ":" in args.connect:
        logger.error("Invalid connection information: " + args.connect)
        return    

    parts = args.connect.split(':')
    if not len(parts) == 2:
        logger.error("Invalid connection information: " + args.connect)
        return
    ip = parts[0]
    try:
        port = int(parts[1])
    except Exception:
        logger.error("Invalid connection information: " + args.connect)
        return

    #getFrequencyInfo()
    runAsService(ip,port)

if __name__ == "__main__":
    main()
