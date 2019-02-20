import os
import time
import argparse,textwrap
import logging
import grpc
from concurrent import futures
import rpcCFM_pb2 as ClusterMessages 
import rpcNFM_pb2 as NodeMessages 
import rpcCFM_pb2_grpc as ClusterRPC
import rpcNFM_pb2_grpc as NodeRPC

VersionStr="19.02.20 Build 1"

logger = logging.getLogger(__name__)
_VerboseLevel = logging.ERROR

# just a wrapper routine for a thread sleeping.  In case needs to be OS specific or something
def Sleep(seconds):
    try:
        time.sleep(seconds)
        
    except BaseException:
        pass

def SleepMs(milliseconds):
    Sleep(float(milliseconds)/1000.0)    

class ClusterFrequencyManager(ClusterRPC.ClusterFrequencyManagerServiceServicer):
    def __init__(self):
        pass
    
def runAsService(hostAddr,hostPort):
    print("Launching as service at {0}:{1}. Version: {2}".format(hostAddr,hostPort,VersionStr))

    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        ClusterRPC.add_ClusterFrequencyManagerServiceServicer_to_server(ClusterFrequencyManager(),server)

    except Exception as Ex:
        logger.error("Error Cluster Frequency Manager server:")
        logger.error(str(Ex))
        return
    
    try:
        server.add_insecure_port(hostAddr +':' + str(hostPort))
        server.start()
        logger.debug("CFM Started")
    except Exception as Ex:
        logger.error("Error Starting CFM:")
        logger.error(str(Ex))
        return

    # server returns, so let's just spin for a while
    try:
        while True:
            time.sleep(1000)

    except KeyboardInterrupt:
        server.stop(0)

def validateNodes(nodeList):
    retArray=[]
    for entry in nodeList:
        if not ':' in entry:
            logger.error("NFM node must be in form of ip:port")
            return False
        parts = entry.split(':')
        if len(parts) != 2:
            logger.error("NFM node must be in form of ip:port")
            return False
        ip = parts[0]
        port = parts[1]
        try:
            port = int(port)
        except:
            logger.error("NFM node must be in form of ip:port")
            return False

        retArray.append({ip:port})

    return retArray            

def main():
    parser = argparse.ArgumentParser(description='Cluster Frequency Manager')
    parser.add_argument("-c","--connect",help="ip:port to listen on.",type=str,required=False)
    parser.add_argument("-v","--verbose",help="prints information, values 0-3",type=int)
    parser.add_argument("nodes", nargs="*", type=str,
                        help=textwrap.dedent('''\
                        nodes where NFM is running.  Form is IP:Port IP:Port IP:Port... .''')) 

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

    if len(args.nodes) < 1:
        print("ERROR: You must specify at least one target NFM Node.")
        return

    nodeMap = validateNodes(args.nodes)
    if False == nodeMap:
        return

    print(nodeMap)
    if None == args.connect:
        args.connect = "0.0.0.0:6000"
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
