# WORM Storage and Object Lock

This document explains how to configure immutable Write-Once-Read-Many (WORM) storage utilizing cloud-based S3 Object Lock and physical optical media. Operators need this reference when digital evidence must be preserved in a state that cryptographically and structurally prevents deletion, tampering, or overwriting, either for a defined retention period or indefinitely.

## Why it matters

Standard cloud storage heavily relies on identity and access management (IAM). This allows administrators or attackers with credential access to silently modify or delete files. Object Lock and physical WORM media remove the ability to mutate data, even from privileged users or root accounts. This enforced, infrastructure-level immutability is often a strict legal requirement for the long-term preservation of digital evidence and for establishing an unbreakable chain of custody.

## Tools

| Tool | Platform | Notes |
| --- | --- | --- |
| `aws` CLI | both | Primary interface for configuring S3 Object Lock (works for Wasabi/B2) |
| `rclone` | both | Can interact with S3 remotes safely; does not natively manage lock policies |
| Optical Drives | both | Physical BD-R (Blu-ray Recordable) archival WORM media |

## The mechanics of Object Lock

S3 Object Lock operates on a write-once-read-many model and requires bucket versioning to be enabled. It offers two primary protection mechanisms:
1. **Retention Periods:** A fixed time window (e.g., 5 years) during which the object cannot be deleted or overwritten.
   - *COMPLIANCE mode:* Cannot be bypassed by anyone, not even the AWS root account.
   - *GOVERNANCE mode:* Can be bypassed by users with specific administrative permissions (e.g., `s3:BypassGovernanceRetention`).
2. **Legal Hold:** An indefinite lock that remains in effect until removed by an authorized user, independent of any retention period.

Both Backblaze B2 and Wasabi offer S3-compatible Object Lock that responds to the standard `aws s3api` commands.

## Auditing and Compliance Monitoring

Establishing a WORM bucket is not a set-and-forget operation; continuous auditing is required to prove that the locks have remained in force throughout the lifecycle of the case. Using cloud-native auditing tools (such as AWS CloudTrail), operators must log all API calls interacting with the `s3:PutObjectRetention` and `s3:PutObjectLegalHold` endpoints. Any attempt to modify a lock policy, even if blocked by COMPLIANCE mode, serves as a crucial signal of potential insider threat or external compromise.

## Practical recipes

The following commands use the standard AWS CLI to configure true WORM storage on an S3-compatible backend.

```bash
# 1. Create an S3 bucket with Object Lock enabled at creation
# Note: Object Lock must typically be enabled at bucket creation time
aws s3api create-bucket \
    --bucket my-evidence-bucket \
    --object-lock-enabled-for-bucket

# 2. Enable bucket versioning (a strict hard prerequisite for Object Lock)
aws s3api put-bucket-versioning \
    --bucket my-evidence-bucket \
    --versioning-configuration Status=Enabled

# 3. Apply a default COMPLIANCE retention lock to the entire bucket
aws s3api put-object-lock-configuration \
    --bucket my-evidence-bucket \
    --object-lock-configuration '{ "ObjectLockEnabled": "Enabled", "Rule": { "DefaultRetention": { "Mode": "COMPLIANCE", "Days": 1825 } } }'

# 4. Upload an object and explicitly set a COMPLIANCE retention date
aws s3api put-object \
    --bucket my-evidence-bucket \
    --key "manifests/batch-01.sha256" \
    --body "./manifests/batch-01.sha256" \
    --object-lock-mode COMPLIANCE \
    --object-lock-retain-until-date "2030-01-01T00:00:00Z"

# 5. Apply an indefinite Legal Hold to a critical evidence archive
aws s3api put-object-legal-hold \
    --bucket my-evidence-bucket \
    --key "evidence/originals/archive.zip" \
    --legal-hold Status=ON

# 6. Verify the current retention status of an object
aws s3api get-object-retention \
    --bucket my-evidence-bucket \
    --key "evidence/originals/archive.zip"
```

## Pitfalls

- **Using GOVERNANCE instead of COMPLIANCE:** Using GOVERNANCE mode provides a false sense of security for digital evidence. Because it can be bypassed by privileged IAM users, it does not meet the strict immutability requirements of forensic WORM storage. Always use COMPLIANCE mode.
- **Forgetting Bucket Versioning:** Object Lock relies on versioning. If versioning is suspended, Object Lock operations will fail, and data may be exposed to overwrite attacks.
- **Infinite Lock Traps:** Accidentally setting a retention period that is excessively long (e.g., 100 years) in COMPLIANCE mode will lock the bucket. The infrastructure provider will continue to bill for this storage, and neither you nor their support team can delete it.
- **Per-Object Negligence:** Assuming Object Lock automatically applies to all objects uploaded. Unless a default bucket retention policy is configured and verified, immutability must be applied manually per-object during upload.

## See also

- [Rclone Immutable Remotes](rclone-immutable-remotes.md)
- [Chain of Custody Principles](../custody/chain-of-custody-principles.md)
- [Legal Considerations](../custody/legal-considerations.md)
