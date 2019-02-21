cp ../../src/*.py .
cp ../../src/*.proto .
docker build --no-cache --build-arg http_proxy=$http_proxy --build-arg https_proxy=$http_proxy --build-arg HTTP_PROXY=$http_proxy --build-arg HTTPS_PROXY=$http_proxy --network=host -t patrickkutch/nodefrequencymanager .
