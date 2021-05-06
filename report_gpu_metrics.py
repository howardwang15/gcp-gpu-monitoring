# Copyright 2021 Howard Wang
# Copyright 2019 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# NOTICE: This file has been modified by Howard Wang to add support for versions of the Python google-cloud-monitoring
# library >= 2.0.0

import time
import socket
import subprocess
import requests
import csv
import datetime
from google.cloud import monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp

metadata_server = "http://metadata/computeMetadata/v1/instance/"
metadata_flavor = {'Metadata-Flavor' : 'Google'}
data = requests.get(metadata_server + 'zone', headers = metadata_flavor).text
zone = data.split("/")[3]
project_id = data.split("/")[1]


client = monitoring_v3.MetricServiceClient()
project_name = client.common_project_path(project_id)
instance_id = requests.get(metadata_server + 'id', headers = metadata_flavor).text


def report_metric(value, t, instance_id, zone, project_id):
    series = monitoring_v3.types.TimeSeries()
    series.metric.type = 'custom.googleapis.com/{type}'.format(type=t)
    series.resource.type = 'gce_instance'
    series.resource.labels['instance_id'] = instance_id
    series.resource.labels['zone'] = zone
    series.resource.labels['project_id'] = project_id
    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval({ 'end_time': { 'seconds': seconds, 'nanos': nanos }})
    point = monitoring_v3.Point()
    point.value.int64_value = value
    point.interval = interval
    series.points.append(point)
    client.create_time_series(request={'name': project_name, 'time_series': [series]})


def get_nvidia_smi_utilization(gpu_query_name):
    csv_file_path = '/tmp/gpu_utilization.csv'
    usage = 0
    length = 0
    subprocess.check_call(['/bin/bash', '-c',
                           'nvidia-smi --query-gpu={} -u --format=csv'
                           ' > {}'.format(gpu_query_name, csv_file_path)])
    with open(csv_file_path) as csvfile:
        utilizations = csv.reader(csvfile, delimiter=' ')
        for row in utilizations:
            length += 1
            if length > 1:
                usage += int(row[0])
    return int(usage / (length - 1))


def get_gpu_utilization():
    return get_nvidia_smi_utilization("utilization.gpu")


def get_gpu_memory_utilization():
    return get_nvidia_smi_utilization("utilization.memory")


GPU_UTILIZATION_METRIC_NAME = "gpu_utilization"
GPU_MEMORY_UTILIZATION_METRIC_NAME = "gpu_memory_utilization"

while True:
    report_metric(get_gpu_utilization(),
                GPU_UTILIZATION_METRIC_NAME,
                instance_id,
                zone,
                project_id)
    report_metric(get_gpu_memory_utilization(),
                GPU_MEMORY_UTILIZATION_METRIC_NAME,
                instance_id,
                zone,
                project_id)
    time.sleep(30)

