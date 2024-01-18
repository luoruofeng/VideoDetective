可以将警告发送给MQ，提供给业务系统使用。这里我们以kafka为例。

## Docker启动KAFKA
```shell
docker-compose down
docker-compose up -d
```

## 测试
```shell

#创建主题
# --partitions: 主题的总共分区数，broker数量的倍数。
# --replication-factor: 主题的分区的副本数。
# --bootstrap-server: Kafka 入口点的地址。
docker run -it --rm --network=kafka_kafka-net confluentinc/cp-kafka:7.4.4  kafka-topics --create --topic monitoring_alarm --partitions 6 --replication-factor 2  --bootstrap-server kafka1:9092,kafka2:9092,kafka3:9092

#查询topics
docker run -it --rm --network=kafka_kafka-net confluentinc/cp-kafka:7.4.4    kafka-topics --list --bootstrap-server kafka1:9092,kafka2:9092,kafka3:9092

#查询主题详情
docker run -it --rm --network=kafka_kafka-net confluentinc/cp-kafka:7.4.4    kafka-topics --describe --topic monitoring_alarm --bootstrap-server kafka1:9092,kafka2:9092,kafka3:9092 

#删除主题
docker run -it --rm --network=kafka_kafka-net confluentinc/cp-kafka:7.4.4    kafka-topics  --delete --topic monitoring_alarm --bootstrap-server kafka1:9092,kafka2:9092,kafka3:9092 

#消费主题
docker run -it --rm --network=kafka_kafka-net confluentinc/cp-kafka:7.4.4  kafka-console-consumer --topic monitoring_alarm --bootstrap-server kafka1:9092,kafka2:9092,kafka3:9092 --from-beginning
```
