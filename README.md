# GPU monitoring service for GCP compute engines

When training deep neural networks, knowing how GPU utilization and memory usage is crucial to understanding resource efficiency during training and inference.

Although GCP GPU compute engine instances come with the NVIDIA drivers installed, using `nvidia-smi` does not provide a reliable way of monitoring GPU metrics through a very long period of time.

This script logs GPU utilization and memory to GCP Montoring metrics explorer.

## Setup
Copied from https://cloud.google.com/compute/docs/gpus/monitor-gpus

1. Clone repo
2. Move script to root directory: `sudo cp report_gpu_metrics.py /root/`
3. Temporarily allow access to the /lib/systemd/system/ directory: `sudo chmod 777 /lib/systemd/system/`
4. Enable the GPU metrics agent
```
cat <<-EOH > /lib/systemd/system/gpu_utilization_agent.service
[Unit]
Description=GPU Utilization Metric Agent
[Service]
PIDFile=/run/gpu_agent.pid
ExecStart=/bin/bash --login -c '/opt/conda/bin/python /root/report_gpu_metrics.py'
User=root
Group=root
WorkingDirectory=/
Restart=always
[Install]
WantedBy=multi-user.target
EOH
```

5. Reset the permissions on the /lib/systemd/system directory: `sudo chmod 755 /lib/systemd/system/`
6. Reload the system daemon: `sudo systemctl daemon-reload`
7. Enable the gpu monitoring service: `sudo systemctl --no-reload --now enable /lib/systemd/system/gpu_utilization_agent.service`

## Viewing metrics
Go to the GCP Monitoring console and select Metrics Explorer. Search for `gpu_utilization`. Note that you can filter utilization by specific compute instance ids.
