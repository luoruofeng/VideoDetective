from confluent_kafka import Producer, KafkaException, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import json
from video_detective import util
from video_detective.detective import Item
import queue
import threading
import logging

MONITORING_ALARM_KAFKA: queue.Queue[list[Item]] = None

class KafkaProducer:
    def __init__(self, bootstrap_servers, topic, partitions, replication_factor, shut_down_event:threading.Event):
        global MONITORING_ALARM_KAFKA
        MONITORING_ALARM_KAFKA = queue.Queue(maxsize=0)
        bootstrap_servers_str = ""
        for bs in bootstrap_servers:
            bootstrap_servers_str += (bs["bootstrap_server"]+",")
        bootstrap_servers_str = bootstrap_servers_str[:-1]
        logging.info(f"bootstrap_servers_str:{bootstrap_servers_str}")
        self.producer = Producer({'bootstrap.servers': bootstrap_servers_str})
        self.bootstrap_servers = bootstrap_servers_str
        self.topic = topic
        self.partitions = partitions
        self.replication_factor = replication_factor
        self.shut_down_event = shut_down_event
        self.create_topic()
        # 启动一个线程来循环处理队列中的消息
        self._start_producer_thread()

    def _start_producer_thread(self):
        def producer_thread():
            while not self.shut_down_event.is_set():
                items = MONITORING_ALARM_KAFKA.get()
                if items is not None:
                    self.produce_messages(items)

        # 启动线程
        import threading
        threading.Thread(target=producer_thread, daemon=True).start()

    def topic_exists(self,admin_client):
        """Check if the given topic exists in Kafka cluster."""
        # Get metadata about all topics
        metadata = admin_client.list_topics(timeout=10)
        # Check if topic_name is in the metadata
        logging.info(f"kafka已经存在的topics:{metadata.topics}")
        return self.topic in metadata.topics

    def create_topic(self):
        # 创建AdminClient实例
        admin_client = AdminClient({
            'bootstrap.servers': self.bootstrap_servers
        })

        if self.topic_exists(admin_client):
            return

        # 定义新主题
        topic = NewTopic(self.topic, num_partitions=self.partitions, replication_factor=self.replication_factor)

        # 创建主题
        fs = admin_client.create_topics([topic])

        # 等待主题创建完成
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                logging.info("kafka主题： {} 创建".format(topic))
            except KafkaException as e:
                error = e.args[0]
                if error.code() == KafkaError.TOPIC_ALREADY_EXISTS:
                    logging.info("kafka主题： {} 已经存在".format(topic))
                else:
                    logging.info("kafka创建主题失败 {}: {}".format(topic, e))

    def produce_messages(self, items):
        logging.info(f"报警- id:{items[0].detective_id} 报警物体:{[{'name':item.class_name,'confidence':item.confidence ,'x':item.center_x,'y':item.center_y,} for item in items]}")
        def acked(err, msg):
            if err is not None:
                logging.info("分发消息到kafka失败: {}".format(err.str()))
            else:
                logging.info(f"分发消息到kafka成功: {msg}")
        for item in items:
            message = json.dumps(vars(item))
            self.producer.produce(self.topic,key=str(item.time), value=message, callback = acked)
        