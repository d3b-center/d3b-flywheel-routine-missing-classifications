# d3b-flywheel-routine-missing-classifications

This script can be run to update any missing file classifications on Flywheel in acquisitions with other files with valid classifications.

To run:

```bash
pip3 install -r requirements.txt
python3 fw_add_missing_file_classifications_dataView.py
```

Operation depends on one environment variable:

| Environment Key | Description |
|-----------------|-------------|
| FLYWHEEL_API_TOKEN | Your API token for Flywheel. It looks like `chop.flywheel.io:<random_alphanum>`.<br> D3b has a gsuite service account for this `flywheel@d3b.center`. |
