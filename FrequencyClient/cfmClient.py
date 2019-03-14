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
import sys
import time
import argparse,textwrap
import logging
import grpc
from pprint import pprint as print
from concurrent import futures
import rpcCFM_pb2 as ClusterMessages 
import rpcCFM_pb2_grpc as ClusterRPC

VersionStr="19.03.08 Build 1"

logger = logging.getLogger(__name__)
_VerboseLevel = logging.ERROR

class ArgParser(object):
    def __init__(self):
        parser = argparse.ArgumentParser(description='CLI for Cluster Frequency Manager',usage='''cvmClient -s CMF_IP:Port [-v] <command> [<args>]

Commands are:
   setClusterFixedFrequency     Sets entire cluster to specified frequency
   setClusterPercentFrequency   Sets entire cluster to specified frequency percentage
   getNodeFrequencyRange        Reports the min/max frequency for a node 
   getNodeInfo                  Reports the # of cores, available frequency governors and CStates
   getNodeCoreInfo              Reports the Min/Max core frequency, Current Frequency and governor for a core
   setClusterSineWave           Sets cluster to a sinewave frequency
   randomizeClusterFrequency    Randomized frequency
   getClusterNodes              Lists all nodes in the cluster
   setNodeFrequency             sets Freqency of specified cores on node to frequency
   setNodeFrequencyPercent      sets Freqency of specified cores on node to frequency percentage
   setNodeGovernor              sets the governor for specified cores on node
   setNodeCState                sets specified CState on specified cores to enable/disable
''')
        

        gArgs=['-s','-server','--v','--verbose']
        globalArgs=[]
        actionArgs=[]

        index = 1
        for foo in range(1,len(sys.argv)):
            arg = sys.argv[index]
            isGlobal=False
            for legalGlobArg in gArgs:
                if legalGlobArg in arg:
                    globalArgs.append(sys.argv[index])
                    index += 1
                    globalArgs.append(sys.argv[index])
                    isGlobal=True
                    break

            if False == isGlobal:
                actionArgs.append(arg)

            index += 1
            if index >= len(sys.argv):
                break

        parser.add_argument("-s","--server",help="ip:port that CMF is listenign on.",type=str,required=True)
        parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)

        try:
            args = parser.parse_args(globalArgs)
            if None == args.verbose:
                _VerboseLevel = 0
            else:
                _VerboseLevel = args.verbose

        except Exception as Ex:
            print(str(Ex))
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

        if not ":" in args.server:
            logger.error("Invalid connection information: " + args.server)
            return    

        #### Go do what was asked ####
        self.target = args.server.strip()

        if len(actionArgs) < 1:
            logger.error("No Commnd given")
            parser.print_help()
            exit(1)


        if not hasattr(self, actionArgs[0]):
            print ('Unrecognized command')
            parser.print_help()
            exit(1)
        
        logger.info("Connecting to CFM at {}".format(self.target))
        getattr(self, actionArgs[0])(actionArgs[1:])

                
    def setClusterFixedFrequency(self,argList):
        parser = argparse.ArgumentParser(description="Set entire cluster to specified frequency")
        parser.add_argument("-f","--frequency",type=int)
        args = parser.parse_args(argList)

        ClusterRequest = ClusterMessages.SetClusterFrequencyRequest()
        ClusterRequest.Frequency = args.frequency
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Cluster_Core_Frequency(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Cluster_Frequency()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the governor set to userspace?")

                else:
                    logger.info("Successful call to Set_Cluster_Frequency()")

        except Exception as ex:
            errorStr = "{0} calling Set_Cluster_Frequency()".format(ex)
            logger.error(errorStr)

    def setClusterPercentFrequency(self,argList):
        parser = argparse.ArgumentParser(description="Set entire cluster to specified frequency percentage")
        parser.add_argument("-f","--frequency",type=int)
        args = parser.parse_args(argList)

        ClusterRequest = ClusterMessages.SetClusterFrequencyPercentRequest()
        ClusterRequest.Frequency = args.frequency
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Cluster_Core_Frequency_Percent(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Cluster_Core_Frequency_Percent()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the governor set to userspace?")

                else:
                    logger.info("Successful call to Set_Cluster_Core_Frequency_Percent()")

        except Exception as ex:
            errorStr = "{0} calling Set_Cluster_Core_Frequency_Percent()".format(ex)
            logger.error(errorStr)

    def setClusterSineWave(self,argList):
        ClusterRequest = ClusterMessages.Empty()
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Cluster_SineWave_Frequencies(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Cluster_SineWave_Frequencies()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the governor set to userspace?")

                else:
                    logger.info("Successful call to Set_Cluster_SineWave_Frequencies()")

        except Exception as ex:
            errorStr = "{0} calling Set_Cluster_SineWave_Frequencies()".format(ex)
            logger.error(errorStr)

    def getClusterNodes(self,argList):
        ClusterRequest = ClusterMessages.Empty()
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Get_Cluster_Nodelist(ClusterRequest)                 
                if False == response.Response.Success:
                    errorStr = "{0} calling Get_Cluster_Nodelist()".format(response.Response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Get_Cluster_Nodelist()")
                    print("--- Node Frequency Manager Nodes ---")
                    for node in response.Node:
                        print(node.Node_ID)
                    

        except Exception as ex:
            errorStr = "{0} calling Get_Cluster_Nodelist()".format(ex)
            logger.error(errorStr)

    def getNodeFrequencyRange(self,argList):
        parser = argparse.ArgumentParser(description="Gets the Min and Max Frequency Range for a node")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        args = parser.parse_args(argList)

        ClusterRequest = ClusterMessages.NodeIdentifier()
        ClusterRequest.Node_ID = args.node
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Get_Node_Frequency_Range(ClusterRequest)                 
                if False == response.Response.Success:
                    errorStr = "{0} calling Get_Node_Frequency_Range()".format(response.Response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Get_Node_Frequency_Range()")
                    print("Node {} Frequency Range: Max: {} Min:{}".format(args.node,response.MaxFrequency,response.MinFrequency))
                    

        except Exception as ex:
            errorStr = "{0} calling Get_Node_Frequency_Range()".format(ex)
            logger.error(errorStr)

    def getNodeCoreInfo(self,argList): 
        parser = argparse.ArgumentParser(description="Gets the info of a specific core on a specific node")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        parser.add_argument("-c","--corenum",help='core number to get info on',type=int,required=True)
        args = parser.parse_args(argList)

        ClusterRequest = ClusterMessages.NodeCoreIdentifier()
        ClusterRequest.Node_ID = args.node
        ClusterRequest.CoreNumber = args.corenum
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Get_Node_Core_Info(ClusterRequest)                 
                if False == response.Response.Success:
                    errorStr = "{0} calling Get_Core_FreGet_Node_Core_Infoquency_Info()".format(response.Response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Get_Core_Frequency_Info()")
                    print("Node {} Core {} Frequency Range: Max: {} Min:{} Current Freq: {} Current Scaling Governor: {}".format(args.node,args.corenum,response.MaxFrequency,response.MinFrequency,response.CurrentFrequency,response.Current_Scaling_Governor))
                    
        except Exception as ex:
            errorStr = "{0} calling Get_Node_Core_Info()".format(ex)
            logger.error(errorStr)            

    def getNodeInfo(self,argList): 
        parser = argparse.ArgumentParser(description="Gets info on specific core on a node")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        args = parser.parse_args(argList)

        ClusterRequest = ClusterMessages.NodeIdentifier()
        ClusterRequest.Node_ID = args.node
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Get_Node_CPU_Info(ClusterRequest)                 
                if False == response.Response.Success:
                    errorStr = "{0} calling Get_Node_CPU_Info()".format(response.Response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Get_Node_CPU_Info()")
                    coreCount = response.CoreCount
                    govStr = ",".join(response.Supported_Scaling_Governor)
                    csStr = ",".join(response.Supported_CState)
                    print("Node: {0} Core Count: {1} Available Governors: {2} Available CStates: {3}".format(args.node,coreCount,govStr,csStr))

        except Exception as ex:
            errorStr = "{0} calling Get_Node_CPU_Info()".format(ex)
            logger.error(errorStr)            

    def setNodeFrequency(self,argList):
        parser = argparse.ArgumentParser(description="Sets the cores of a node to a frequency")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        parser.add_argument("-c","--cores",type=str,required=True)
        parser.add_argument("-f","--frequency",type=int,required=True)

        args = parser.parse_args(argList)
        
        ClusterRequest = ClusterMessages.SetNodeCoreFrequencyRequest()
        ClusterRequest.Node_ID = args.node
        ClusterRequest.Core_List = args.cores
        ClusterRequest.Frequency = args.frequency
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Node_Core_Frequency(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Node_Core_Frequency()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the governor set to userspace?")

                else:
                    logger.info("Successful call to Set_Node_Core_Frequency()")

        except Exception as ex:
            errorStr = "{0} calling Set_Node_Frequency()".format(ex)
            logger.error(errorStr)

    def setNodeFrequencyPercent(self,argList):
        parser = argparse.ArgumentParser(description="Sets the cores of a node to a frequency")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        parser.add_argument("-c","--cores",type=str,required=True)
        parser.add_argument("-f","--frequency",type=float,required=True)

        args = parser.parse_args(argList)
        
        ClusterRequest = ClusterMessages.SetNodeCoreFrequencyPercentRequest()
        ClusterRequest.Node_ID = args.node
        ClusterRequest.Core_List = args.cores
        ClusterRequest.Frequency = args.frequency
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Node_Core_Frequency_Percent(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Node_Core_Frequency_Percent()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the govenror set to userspace?")

                else:
                    logger.info("Successful call to Set_Node_Core_Frequency_Percent()")

        except Exception as ex:
            errorStr = "{0} calling Set_Node_Core_Frequency_Percent()".format(ex)
            logger.error(errorStr)

    def setNodeGovernor(self,argList):
        parser = argparse.ArgumentParser(description="Sets the frequency governor for the cores of a node")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        parser.add_argument("-c","--cores",help='ex. 1-4,6,7,32-50',type=str,required=True)
        parser.add_argument("-g","--governor",help='run getNodeInfo to find out available governors',type=str,required=True)

        args = parser.parse_args(argList)
        
        ClusterRequest = ClusterMessages.SetNodeGovenorRequest()
        ClusterRequest.Node_ID = args.node
        ClusterRequest.Core_List = args.cores
        ClusterRequest.Core_Govenor = args.governor
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Node_Core_Govenor(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Node_Core_Govenor()".format(response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Set_Node_Core_Govenor()")

        except Exception as ex:
            errorStr = "{0} calling Set_Node_Core_Govenor()".format(ex)
            logger.error(errorStr)

    def setNodeCState(self,argList):
        parser = argparse.ArgumentParser(description="Sets the cstate of cores on  a node")
        parser.add_argument("-n","--node",help='fqdn of where the NFM service is running',type=str,required=True)
        parser.add_argument("-c","--cores",type=str,required=True)
        parser.add_argument("-m","--name",help='name of CState (ex. POLL,C1,C1E,C6)', type=str,required=True)
        grpEnableDisable = parser.add_mutually_exclusive_group()

        grpEnableDisable.add_argument("-e","--enable",help='enable  CState', action='store_true')
        grpEnableDisable.add_argument("-d","--disable",help='disable  CState', action='store_true')

        args = parser.parse_args(argList)
        
        ClusterRequest = ClusterMessages.SetNodeCStateRequest()
        ClusterRequest.Node_ID = args.node.strip()
        ClusterRequest.Core_List = args.cores
        ClusterRequest.Core_CState = args.name.strip()

        if True == args.enable:
            ClusterRequest.State = 0
        else:
            ClusterRequest.State = 1
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Node_Core_CState(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Node_Core_CState()".format(response.Reason)
                    logger.error(errorStr)

                else:
                    logger.info("Successful call to Set_Node_Core_CState()")

        except Exception as ex:
            errorStr = "{0} calling Set_Node_Core_CState()".format(ex)
            logger.error(errorStr)

    def randomizeClusterFrequency(self,argsList):
        ClusterRequest = ClusterMessages.Empty()
        
        try:
            with grpc.insecure_channel(self.target) as channel:
                rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
                response = rpcStub.Set_Cluster_Random_Frequencies(ClusterRequest)                 
                if False == response.Success:
                    errorStr = "{0} calling Set_Cluster_Frequency_Random()".format(response.Reason)
                    logger.error(errorStr)
                    logger.error("Is the governor set to userspace?")

                else:
                    logger.info("Successful call to Set_Cluster_Frequency_Random()")

        except Exception as ex:
            errorStr = "{0} calling Set_Cluster_Frequency_Random()".format(ex)
            logger.error(errorStr)
        
    
def main():
    doWork = ArgParser()


if __name__ == "__main__":
    main()
