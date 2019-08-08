# am2alertapi

Prometheus Alertmanager to University of Washington AlertAPI adapter.

This script suitable for systemd deployment or Container


## Building container
Google Cloud Build build this directory for use in Managed Container Infrastructure
Require credentials in uwit-mci-svcs or service account

```gcloud --project uwit-mci-svcs builds submit --tag gcr.io/uwit-mci-svcs/am2alertapi:$(date "+%Y%m%d%H%M") .```

## Standalone deployment with systemd
Review/run `Standalone-deploy` to build virtual environment and set up files. Uses system files in systemd-deployment.