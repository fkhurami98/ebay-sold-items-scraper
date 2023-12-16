- To run the docker images in detached mode, run the following command:
```
docker-compose up -d --build

```

- To stop and remove all containers, run the following command:
``` 
docker-compose down
```

- To access a containers shell, run the following command:
```
docker exec -it container_name_or_id bash
```