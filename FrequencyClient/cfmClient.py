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
import argparse,textwrap
import logging
import grpc
from concurrent import futures
import rpcCFM_pb2 as ClusterMessages 
import rpcCFM_pb2_grpc as ClusterRPC

VersionStr="19.02.20 Build 1"

logger = logging.getLogger(__name__)
_VerboseLevel = logging.ERROR

def Set_Cluster_Frequency(target,frequency):
    ClusterRequest = ClusterMessages.SetClusterFrequencyRequest()
    ClusterRequest.Frequency = frequency
    
    try:
        with grpc.insecure_channel(target) as channel:
            rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
            response = rpcStub.Set_Cluster_Core_Frequency(ClusterRequest)                 
            if False == response.Success:
                errorStr = "{0} calling Set_Cluster_Frequency()".format(response.Reason)
                logger.error(errorStr)

            else:
                logger.info("Successful call to Set_Cluster_Frequency()")

    except Exception as ex:
        errorStr = "{0} calling Set_Cluster_Frequency()".format(ex)
        logger.error(errorStr)

def Set_Cluster_Frequency_Percent(target,frequencyPct):
    ClusterRequest = ClusterMessages.SetClusterFrequencyPercentRequest()
    ClusterRequest.Frequency = frequencyPct
    
    try:
        with grpc.insecure_channel(target) as channel:
            rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
            response = rpcStub.Set_Cluster_Core_Frequency_Percent(ClusterRequest)                 
            if False == response.Success:
                errorStr = "{0} calling Set_Cluster_Core_Frequency_Percent()".format(response.Reason)
                logger.error(errorStr)

            else:
                logger.info("Successful call to Set_Cluster_Core_Frequency_Percent()")

    except Exception as ex:
        errorStr = "{0} calling Set_Cluster_Core_Frequency_Percent()".format(ex)
        logger.error(errorStr)

def Set_Cluster_Frequency_Sinewave(target):
    ClusterRequest = ClusterMessages.Empty()
    
    try:
        with grpc.insecure_channel(target) as channel:
            rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
            response = rpcStub.Set_Cluster_SineWave_Frequencies(ClusterRequest)                 
            if False == response.Success:
                errorStr = "{0} calling Set_Cluster_SineWave_Frequencies()".format(response.Reason)
                logger.error(errorStr)

            else:
                logger.info("Successful call to Set_Cluster_SineWave_Frequencies()")

    except Exception as ex:
        errorStr = "{0} calling Set_Cluster_SineWave_Frequencies()".format(ex)
        logger.error(errorStr)

def Get_NodeList(target):
    ClusterRequest = ClusterMessages.Empty()
    
    try:
        with grpc.insecure_channel(target) as channel:
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

def Get_Node_Frequency_Info(target,NodeName):
    ClusterRequest = ClusterMessages.NodeIdentifier()
    ClusterRequest.Node_ID = NodeName
    
    try:
        with grpc.insecure_channel(target) as channel:
            rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
            response = rpcStub.Get_Node_Frequency_Range(ClusterRequest)                 
            if False == response.Response.Success:
                errorStr = "{0} calling Get_Node_Frequency_Range()".format(response.Response.Reason)
                logger.error(errorStr)

            else:
                logger.info("Successful call to Get_Node_Frequency_Range()")
                print("Node {} Frequency Range: Max: {} Min:{}".format(NodeName,response.MaxFrequency,response.MinFrequency))
                

    except Exception as ex:
        errorStr = "{0} calling Get_Node_Frequency_Range()".format(ex)
        logger.error(errorStr)

def Set_Cluster_Frequency_Random(target):
    ClusterRequest = ClusterMessages.Empty()
    
    try:
        with grpc.insecure_channel(target) as channel:
            rpcStub = ClusterRPC.ClusterFrequencyManagerServiceStub(channel)
            response = rpcStub.Set_Cluster_Random_Frequencies(ClusterRequest)                 
            if False == response.Success:
                errorStr = "{0} calling Set_Cluster_Frequency_Random()".format(response.Reason)
                logger.error(errorStr)

            else:
                logger.info("Successful call to Set_Cluster_Frequency_Random()")

    except Exception as ex:
        errorStr = "{0} calling Set_Cluster_Frequency_Random()".format(ex)
        logger.error(errorStr)

def main():
    parser = argparse.ArgumentParser(description='CLI for Cluster Frequency Manager')
    parser.add_argument("-c","--connect",help="ip:port that CMF is listenign on.",type=str,required=True)
    parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)
    
    cmdGroup = parser.add_mutually_exclusive_group()
    cmdGroup.add_argument('--getnodes',help='returns list of all registered NFM nodes',action='store_true')
    cmdGroup.add_argument('--getnodefrequencyrange',help='get frequency range of CPU on node',type=str)
    cmdGroup.add_argument('--randomize',help='randomize all core frequencies in cluster',action='store_true')
    cmdGroup.add_argument('--sinewave',help='change all core frequencies to be in wave pattern',action='store_true')

    cmdGroup.add_argument('--setclusterfixed',help='set all cores in cluster to specified frequency',type=int)
    cmdGroup.add_argument('--setclusterpercent',help='set all cores in cluster to specified frequency percentage',type=float)


    try:
        args = parser.parse_args()
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


    if not ":" in args.connect:
        logger.error("Invalid connection information: " + args.connect)
        return    

    #### Go do what was asked ####
    target = args.connect.strip()
    logger.info("Connecting to CFM at {}".format(target))
    if args.randomize:
        Set_Cluster_Frequency_Random(target)        

    elif args.sinewave:
        Set_Cluster_Frequency_Sinewave(target)        

    elif None != args.setclusterfixed:
        Set_Cluster_Frequency(target,args.setclusterfixed)        

    elif None != args.setclusterpercent:
        Set_Cluster_Frequency_Percent(target,args.setclusterpercent)        

    elif args.getnodes:
        Get_NodeList(target)

    elif None != args.getnodefrequencyrange:
        Get_Node_Frequency_Info(target,args.getnodefrequencyrange)

    else:
        logger.error("Nothing else supported at the moment.")

if __name__ == "__main__":
    main()
