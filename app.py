import os
from threading import Thread

from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, SubscribeOptions, MQTTMessage

PORT = 8080
COMMUNITYSTRING = '3aezBkWG'


class App(Thread):
    def __init__(self, mqtt_client, *args, **kwargs):
        super().__init__(*args, daemon=True, **kwargs)
        self.mqtt_client = mqtt_client

    def run(self):
        snmpEngine = engine.SnmpEngine()
        config.addV1System(snmpEngine, COMMUNITYSTRING, COMMUNITYSTRING)
        ntfrcv.NotificationReceiver(snmpEngine, self.cbFun)
        self.add_transport(snmpEngine, PORT)
        snmpEngine.transportDispatcher.jobStarted(1)
        try:
            print("Trap Listener started .....")
            print("To Stop Press Ctrl+c")
            print("\n")
            snmpEngine.transportDispatcher.runDispatcher()
        except:
            snmpEngine.transportDispatcher.closeDispatcher()
            raise

    def add_transport(self, snmpEngine, PORT):
        """
        :param snmpEngine:
        :return:
        """
        try:
            config.addTransport(
                snmpEngine,
                udp.domainName,
                udp.UdpTransport().openServerMode(('0.0.0.0',
                                                   int(PORT)))
            )
        except Exception as e:
            print("{} Port Binding Failed the Provided Port {} is in Use".format(e, PORT))

    def cbFun(self, snmpEngine, stateReference, contextEngineId, context, *_):
        print(stateReference)
        execContext = snmpEngine.observer.getExecutionContext(
            'rfc3412.receiveMessage:request'
        )
        print('#Notification from %s \n#ContextEngineId: "%s" \n#SecurityName "%s"' %
              (execContext['transportAddress'],
               contextEngineId,
               execContext['securityName'])
              )
        payload = context[-1][-1]
        print(f'#Payload: {payload}')
        mqtt_client.publish(f'fac/{payload}')


if __name__ == "__main__":
    while True:
        mqtt_client = mqtt.Client(client_id='fac')
        mqtt_client.tls_set(
            '/opt/tls/ca_certificate.pem',
            '/opt/tls/client_certificate.pem',
            '/opt/tls/client_key.pem'
        )
        mqtt_client.connect(os.environ['MQTT_HOSTNAME'], 8883)
        mqtt_client.loop_start()
        mqtt_client.on_connect = print
        app = App(mqtt_client)
        app.start()
        app.join()
