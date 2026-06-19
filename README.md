# Ringg AI Take Home Assessment

This repository contains my solution for the Ringg AI Solutions Engineer take home assignment.

## Repository Contents

- Root cause analysis of the reported callback classification issue
- Customer impact assessment
- Immediate and long term remediation plan
- Monitoring and prevention recommendations
- Python audit script for identifying affected calls

## Audit Script

The audit utility (`ringg_callback_audit.py`) identifies:

1. Calls where callback requests were incorrectly recorded as `NOT_INTERESTED`
2. Failed CRM webhook deliveries
3. Payload inconsistencies such as missing callback timestamps

## Running the Script

```bash
python ringg_callback_audit.py
```

## Assumptions

- Structured callback fields are treated as the primary source of truth.
- Transcript inspection is used only as a lightweight audit fallback when callback extraction itself appears to have failed.
- The provided sample calls are representative of the broader issue reported by the customer.
