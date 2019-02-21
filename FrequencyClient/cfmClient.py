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

    else:
        logger.error("Nothing else supported at the moment.")

if __name__ == "__main__":
    main()
