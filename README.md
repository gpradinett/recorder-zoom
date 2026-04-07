docker build -t recorder-app .
docker run -it --name mi-grabador -v ./videos:/app/videos recorder-app