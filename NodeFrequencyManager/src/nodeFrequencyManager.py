#
#   BSD LICENSE
# 
#   Copyright(c) 2007-2019 Intel Corporation. All rights reserved.
#   All rights reserved.
# 
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions
#   are met:
# 
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     * Neither the name of Intel Corporation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
# 
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# 
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

VersionStr="19.03.19 Build 2"

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

def range_expand(s):
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l,h = map(int, i.split('-'))
            r+= range(l,h+1)
    return r    

def set_max_cpu_freq(maxfreq, cpurange):
    for x in cpurange:
        maxName = "/sys/devices/system/cpu/cpu" + str(x) + "/cpufreq/scaling_max_freq"
        logger.info("Writing " + str(maxfreq) + " to " + maxName)
        if False == WriteToFile(maxName,str(maxfreq)):
            return False

    return True

def get_cstates():
	stateList = []
	states = os.listdir("/sys/devices/system/cpu/cpu0/cpuidle/")
	for state in states:
		stateFileName = "/sys/devices/system/cpu/cpu0/cpuidle/" + state + "/name"
		stateFile = open(stateFileName,'r')
		statename = stateFile.readline().strip("\n")
		stateList.append(statename)
		stateFile.close()
	return stateList


def set_min_cpu_freq(minfreq,cpurange):
    for x in cpurange:
        minName = "/sys/devices/system/cpu/cpu" + str(x) + "/cpufreq/scaling_min_freq"
        logger.info("Writing " + str(minfreq) + " to " + minName)
        if False == WriteToFile(minName,str(minfreq)):
            return False

    return True

def set_cstate(cstate,enable,cpurange):
    # Get list of cstate dirs to iterate through to find the cstate name
    cstates = os.listdir("/sys/devices/system/cpu/cpu0/cpuidle")

    for x in cpurange:
        for y in cstates:
            name = ReadFromFile("/sys/devices/system/cpu/cpu0/cpuidle/" + y + "/name")
            if (name == cstate):
                stateName = "/sys/devices/system/cpu/cpu" + str(x) + "/cpuidle/" + str(y) + "/disable"
                logger.info("Writing '" + str(enable) + "' to " + stateName)
                if False == WriteToFile(stateName,str(str(enable))):
                    return False

    return True

def set_cpu_freq(setfreq,cpurange):
    for x in cpurange:
        setName = "/sys/devices/system/cpu/cpu" + str(x) + "/cpufreq/scaling_setspeed"
        logger.info("Writing " + str(setfreq) + " to " + setName)
        minFile = open(setName,'r')
        current = minFile.readline().strip("\n")
        minFile.close()
        if current == "<unsupported>":
            errorStr = ("Error, cannot set frequency for core " + str(x) + " " + current + " Need '-g userspace'")
            logger.error(errorStr)
            return False
        else:
            if False == WriteToFile(setName,str(str(setfreq))):
                return False

        errorStr = "OK"
        return True
        
def set_governor(gov,cpurange):
    for x in cpurange:
        govName = "/sys/devices/system/cpu/cpu" + str(x) + "/cpufreq/scaling_governor"
        logger.info("Writing '" + str(gov) + "' to " + govName)
        if False == WriteToFile(govName,str(str(gov))):
            return False

    return True
        

def ReadFromFile(Filename):
    try:
        file = open(Filename,'rt')
        if None == file:
            return "N/A"
    except Exception:
        return "Error Reading From File: {0}".format(Filename)

    return file.read().strip()
    
def WriteToFile(Filename,value):
    global errorStr
    errorStr = "OK"

    try:
        value=str(value)
        file = open(Filename,'wt')
        if None == file:
            return "N/A"

        file.write(value)
        file.close()
        #logger.info("Success Writing [{0} to File: {1}".format(value,Filename))
        
    except Exception as Ex:
        errorStr = "Error Writing [{0}] to File: {1}: {2}".format(value,Filename,Ex)
        #logger.error("Error Writing [{0} to File: {1}: {2}".format(value,Filename,Ex))
        return False
        
    return True

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
        global coreCount,errorStr
        
        if coreNum < 0 or coreNum > coreCount-1:
            errorStr = "Invalid Core Number {} specified".format(coreNum)
            return False

        return WriteToFile(GetBaseDir() + "/cpu"  + str(coreNum) + "/cpufreq/" + stat,value)
        
    def _getCoreCurrentFrequency(self,coreNum):
        global coreCount,errorStr
        if coreNum < 0 or coreNum > coreCount-1:
            errorStr = "Invalid Core Number {} specified".format(coreNum)
            return False
            
        return self._getCoreFrequencyStat(coreNum,"cpuinfo_cur_freq")
        
    def _setCoreFrequency(self,coreNum,frequency):
        global coreCount, errorStr
        errorStr = "OK"
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
            frequency = coreMax
            return set_cpu_freq(frequency,[coreNum,])
        
        if frequency < coreMin:
            errorStr = "Cannot set core #{0} frequency to {1}, minimum is {2}".format(coreNum,frequency,coreMin)
            return False

        return set_cpu_freq(frequency,[coreNum,])

        # Might fail if you try to set max to be > min
        # if False == self._setCoreFrequencyStat(coreNum,"scaling_max_freq",frequency):
        #     self._setCoreFrequencyStat(coreNum,"scaling_min_freq",frequency)
        #     return self._setCoreFrequencyStat(coreNum,"scaling_max_freq",frequency)
            
        # return self._setCoreFrequencyStat(coreNum,"scaling_min_freq",frequency)

    def _setCoreFrequencyPercent(self,coreNum,percentage):
        global coreCount, errorStr
        if coreNum < 0 or coreNum > coreCount-1:
            errorStr = "Invalid coreNum: {0}".format(coreNum)
            return False
            
        coreMin = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_min_freq"))
        coreMax = int(self._getCoreFrequencyStat(coreNum,"cpuinfo_max_freq"))
        
        restultingFreq = (coreMax-coreMin) * (float(percentage)/100.0) + coreMin
        return self._setCoreFrequency(coreNum,restultingFreq)
            
    def _setAllCoreFrequency(self,frequency):
        global errorStr
        retCode = True
        errCode = "OK"

        for coreNum in range(0,coreCount):
            if False == self._setCoreFrequency(coreNum,frequency):
                retCode = False
                errCode = errorStr

        errorStr = errCode
        return retCode

    def _setAllCoreFrequencyPercent(self,Percent):
        global errorStr
        retCode = True
        errCode = "OK"

        for coreNum in range(0,coreCount):
            if False == self._setCoreFrequencyPercent(coreNum,Percent):
                retCode = False
                errCode = errorStr
                
        errorStr = errCode
        return retCode
                
    def _doRandom(self):
        import random
        global errorStr
        retCode = True
        errCode = "OK"

        for coreNum in range(0,coreCount):
            percent = random.randint(0,100)
            if False == self._setCoreFrequencyPercent(coreNum,percent):
                retCode = False
                errCode = errorStr
            
                
        errorStr = errCode
        return retCode
                
    def _doSine(self):
        from math import sin,pi
        global errorStr

        retCode = True
        errCode = "OK"

        Fs=8000
        f=500
        sample=coreCount
        a=[0]*sample
        for n in range(sample):
            a[n]=sin(2*pi*f*n/Fs)/2
        
        for coreNum in range(0,coreCount):
            if False == self._setCoreFrequencyPercent(coreNum,a[coreNum]*100 + 50):
                global errorStr
                retCode = False
                errCode = errorStr
                
        errorStr = errCode
        return retCode

    def Set_Core_Frequency(self, request, context):
        global errorStr

        logger.info("Processing Set_Core_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        for core in coreList:
            responseCode = self._setCoreFrequency(core,request.Frequency)

            response.Success = responseCode
            response.Reason = errorStr

        return response

    def Set_Core_Percent_Frequency(self, request, context):
        global errorStr

        logger.info("Processing Set_Core_Percent_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        for core in coreList:
            responseCode = self._setCoreFrequencyPercent(core,request.Frequency)
            response.Success = responseCode
            response.Reason = errorStr

        return response

    def Set_Core_Govenor(self, request, context):
        global errorStr
        logger.info("Processing Set_Core_Govenor request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        responseCode = set_governor(request.Core_Govenor,coreList)
        response.Success = responseCode
        response.Reason = errorStr

        return response

    def Set_Core_CState(self, request, context): 
        global errorStr
        logger.info("Processing Set_Core_CState request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        
        responseCode = set_cstate(request.Core_CState,request.State,coreList)
        response.Success = responseCode
        response.Reason = errorStr

        return response


    def Set_Core_Max_Frequency(self, request, context): 
        global errorStr
        logger.info("Processing Set_Core_Max_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        
        responseCode = set_max_cpu_freq(request.Frequency,coreList)
        response.Success = responseCode
        response.Reason = errorStr

        return response

    def Set_Core_Min_Frequency(self, request, context): 
        global errorStr
        logger.info("Processing Set_Core_Min_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        coreList = range_expand(request.Core_List)
        
        responseCode = set_min_cpu_freq(request.Frequency,coreList)
        response.Success = responseCode
        response.Reason = errorStr

        return response


    def Set_All_Core_Frequency(self, request, context):
        global errorStr
        logger.info("Processing Set_All_Core_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setAllCoreFrequency(request.Frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response
       
    def Set_All_Core_Percent_Frequency(self, request, context):
        global errorStr
        logger.info("Processing Set_All_Core_Percent_Frequency request")
        response = messagesNFD.ServiceResponse()
        errorStr="OK"

        responseCode = self._setAllCoreFrequencyPercent(request.Frequency)
        response.Success = responseCode
        response.Reason = errorStr

        return response

    def Get_Node_CPU_Info(self, request, context):
        global errorStr,coreCount
        logger.info("Processing Get_Node_CPU_Info request")

        response = messagesNFD.NodeCPU_Info()
        response.CoreCount = coreCount
        for governor in self._getCoreFrequencyStat(0,"scaling_available_governors").split(' '):
            response.Supported_Scaling_Governor.append(governor)

        for cState in get_cstates():
            response.Supported_CState.append(cState)

        response.Response.Success = True
        response.Response.Reason = "OK"

        return response

    def Get_Core_Frequency_Info(self, request, context):
        global errorStr
        logger.info("Processing Get_Core_Frequency request")

        response = messagesNFD.CoreFrequencyInfo()

        if request.CoreNumber < 0 or request.CoreNumber > coreCount-1:
            errorStr = "Invalid coreNum: {0}".format(request.CoreNumber)

        else:
            response.MaxFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"cpuinfo_max_freq"))
            response.MinFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"cpuinfo_min_freq"))
            response.CurrentFrequency = int(self._getCoreFrequencyStat(request.CoreNumber,"cpuinfo_cur_freq"))
            response.Current_Scaling_Governor = self._getCoreFrequencyStat(request.CoreNumber,"scaling_governor")
        
        response.Response.Success = errorStr == "OK"
        response.Response.Reason = errorStr

        return response
        
    def Set_Random_Frequencies(self, request, context):
        global errorStr
        errorStr = "OK"
        logger.info("Setting frequencies to random pattern")
        response = messagesNFD.ServiceResponse()
        
        response.Success = self._doRandom()
        response.Reason = errorStr

        return response

    def Set_SineWave_Frequencies(self, request, context):
        global errorStr
        errorStr = "OK"
        logger.info("Setting frequencies to sine wave pattern")
        response = messagesNFD.ServiceResponse()
        
        response.Success = self._doSine()
        response.Reason = errorStr

        return response
    
def runAsService(hostAddr,hostPort):
    global VersionStr
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
        logger.info("NFM {0} Started".format(VersionStr))

    except Exception as Ex:
        logger.error("Error Starting NFM:")
        logger.error(str(Ex))
        return

    # server returns, so let's just spin for a while
    try:
        while True:
            SleepMs(100)

    except KeyboardInterrupt:
        server.stop(0)

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
