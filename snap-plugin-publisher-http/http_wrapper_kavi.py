#!/usr/bin/env python

import os
import socket
import logging
import requests

import sys
dirpath = os.path.dirname(__file__)

sys.path.insert(1, dirpath+ '../../')

import snap_plugin.v1 as snap

from google.protobuf import text_format

LOG = logging.getLogger(__name__)
h = logging.FileHandler('/tmp/snap_plugin.log', 'a')
h.setLevel('DEBUG')
LOG.addHandler(h)



class HTTP(snap.Publisher):
    """Generic HTTP publisher plugin."""

    def update_catalog(self, config):
        LOG.debug("GetMetricTypes called")
        metrics = []
        keys = ("float64", "int64", "string")

        self._args.required_config = False
        print("self._args.required_config", self._args.required_config)

        print("snap.Publisher ")

        for key in ("float", "int"):
            metric = snap.Metric(
                namespace=[
                    snap.NamespaceElement(value="intel"),
                    snap.NamespaceElement(value="logs"),
                    snap.NamespaceElement(value="*")

                ],
                data="str",
                version=1,
                tags={"mtype": "gauge"},
                description="http publisher {}".format(key),
            )
            metrics.append(metric)
        return metrics



    def publish(self, metrics, config):
        """Publishes metrics to a HTTP endpoint."""
        # 'http://13.59.141.92:4000/ingestion/alert


        print("coming here")
        config['server_protocol'] = 'http'
        config['server_name'] = '13.59.141.92'
        config['server_port'] = '4000'
        config['request_uri'] = 'ingestion/alert'

        LOG.debug(
            "server_protocol:%s server_name:%s server_port:%s request_uri:%s" %
                (config['server_protocol'], config['server_name'],
                 config['server_port'], config['request_uri']))

        metrics_url = "%s://%s:%s/%s" % (
                config['server_protocol'],
                config['server_name'],
                config['server_port'],
                config['request_uri'] or '')

        LOG.debug("metrics_url:%s" % metrics_url)

        session = requests.Session()
        # For later
        # session.auth = requests.auth.HTTPBasicAuth(config['http_user'], config['http_pass'])

        metrics_payload = []
        if len(metrics) > 0:
            for metric in metrics:
                try:
                    metric.data
                except e:
                    LOG.debug("Eh? metric has no data: %s" % e)
                    continue

                metric_namespace = ['']
                # For some reason pop() is making python blow up
                # for nse in metric.namespace.pop():
                for nse in metric.namespace._pb:
                    metric_namespace.append(nse.Value)
                metric_namespace = '/'.join(metric_namespace)

                LOG.debug(
                    "Saw metric timestamp:%s namespace:%s data:%s unit:%s tags:%s description:%s" %
                    (metric.timestamp, metric_namespace, metric.data, metric.unit, metric.tags,
                     metric.description))


                print(metric.timestamp, metric_namespace, metric.data, metric.unit, metric.tags,
                     metric.description)

                config['batch_size'] = 1000

                if len(metrics_payload) >= config['batch_size']:
                    for m in metrics_payload:
                        LOG.debug("metric: %s" % m)
                    try:
                        session.post(metrics_url, data='\n'.join(metrics_payload))
                    except e:
                        LOG.debug("Exception sending metrics: %s" % e)
                    else:
                        LOG.debug("Sent %s metrics" % len(metrics_payload))

                    metrics_payload = []

            if len(metrics_payload):
                for m in metrics_payload:
                    LOG.debug("metric: %s" % m)

                try:
                    session.post(metrics_url, data='\n'.join(metrics_payload))
                except e:
                    LOG.debug("Exception sending metrics: %s" % e)
                else:
                    LOG.debug("Sent %s metrics" % len(metrics_payload))


    def get_config_policy(self):
        return snap.ConfigPolicy(
            [
                None,
                [
                    (
                        "server_protocol",
                        snap.StringRule(default='http')
                    ),
                    (
                        "server_name",
                        snap.StringRule(required=True)
                    ),
                    (
                        "server_port",
                        snap.IntegerRule(required=True)
                    ),
                    (
                        "request_uri",
                        snap.StringRule()
                    ),
                    (
                        "batch_size",
                        snap.IntegerRule(default=1000)
                    ),
                    (
                        "plugin_running_on",
                        snap.StringRule(default=socket.getfqdn())
                    ),
                ]
            ],
        )

if __name__ == "__main__":
    #HTTP("http_wrapper.py", 1).stop_plugin()
    HTTP("http_wrapper.py", 1).start_plugin()
