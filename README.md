# am2alertapi

Prometheus Alertmanager to University of Washington AlertAPI adapter.

This script suitable for systemd deployment or Container


## Building container
Google Cloud Build build this directory

### For Development
```gcloud --project [PROJECT] builds submit --tag gcr.io/[PROJECT]/am2alertapi:dev-$(date "+%Y%m%d%H%M") .```

### For Release
```gcloud --project [PROJECT] builds submit --tag gcr.io/[PROJECT]/am2alertapi:rel-$(date "+%Y%m%d%H%M") .```

## Standalone deployment with systemd
Review/run `Standalone-deploy` to build virtual environment and set up files. Uses system files in systemd-deployment.
