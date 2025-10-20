# Bedrock Knowledge Base Vector Upload Failure - Troubleshooting Runbook

---
**RUNBOOK METADATA**  
**Incident IDs**: INC-2025-KB-001  
**Keywords**: Bedrock, Knowledge Base, S3, vector storage, 403, access denied, PutObject, sidekick-kb-vectors-dev-275666109134  
**Affected Services**: Amazon Bedrock Knowledge Base, S3 Vector Storage, AI/ML Platform  
**Use Case**: Resolves Bedrock Knowledge Base sync failures due to missing S3 permissions  
---

## Overview

This runbook provides step-by-step procedures for diagnosing and resolving S3 bucket permission issues that prevent Amazon Bedrock Knowledge Base from uploading vector embeddings to the S3 vector store.

**Severity**: High  
**Expected Resolution Time**: 10-20 minutes  
**On-Call Team**: AI/ML Platform Engineering

---

## Symptoms

- Bedrock Knowledge Base sync jobs failing with "Access Denied" errors
- 403 Forbidden errors in CloudWatch logs for Knowledge Base operations
- Vector embeddings not being stored in S3 bucket
- Knowledge Base status showing "Failed" or "Sync Failed"
- CloudTrail logs showing denied S3 PutObject operations from bedrock.amazonaws.com
- Users unable to query recently added documents

---

## Immediate Actions (First 5 Minutes)

### 1. Verify the Issue
```bash
# Check the specific vector bucket that's failing
BUCKET_NAME="sidekick-kb-vectors-dev-275666109134"

# Verify bucket exists and is accessible
aws s3 ls s3://${BUCKET_NAME}/ --region us-east-1

# Check recent CloudTrail events for S3 access denials
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=${BUCKET_NAME} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 20 \
  --query 'Events[?contains(CloudTrailEvent, `AccessDenied`) || contains(CloudTrailEvent, `403`)]'

# Check Knowledge Base sync status
aws bedrock-agent list-knowledge-bases \
  --query 'knowledgeBaseSummaries[*].[knowledgeBaseId,name,status]' \
  --output table
```

### 2. Establish Communication
- Create Slack channel: `#incident-kb-vector-upload`
- Page on-call AI/ML engineer via PagerDuty
- Update status page: "Investigating Knowledge Base sync issues"
- Notify stakeholders: AI/ML team, Product team

### 3. Gather Initial Data
- When did the sync failures start?
- Recent infrastructure changes (last 24 hours)
- Current bucket policy configuration
- Knowledge Base ID and configuration

---

## Diagnostic Steps

### Step 1: Check S3 Bucket Policy

**Objective**: Verify bucket policy allows Bedrock to write vector embeddings

```bash
# Retrieve current bucket policy
BUCKET_NAME="sidekick-kb-vectors-dev-275666109134"

aws s3api get-bucket-policy \
  --bucket ${BUCKET_NAME} \
  --query Policy \
  --output text | jq .
```

**What to Look For**:
- Does the policy include `s3:PutObject` permission? ← **CRITICAL**
- Is `bedrock.amazonaws.com` listed as a principal?
- Are the resource ARNs correct (both bucket and bucket/*)?
- Are the condition keys properly configured?

**Common Issue - Missing s3:PutObject**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockKnowledgeBaseAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
        // ❌ MISSING: "s3:PutObject" - This causes the failure!
      ],
      "Resource": [
        "arn:aws:s3:::sidekick-kb-vectors-dev-275666109134",
        "arn:aws:s3:::sidekick-kb-vectors-dev-275666109134/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "275666109134"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:us-east-1:275666109134:knowledge-base/*"
        }
      }
    }
  ]
}
```

**Expected Correct Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockKnowledgeBaseAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",      ← ✅ MUST BE PRESENT
        "s3:DeleteObject",   ← Optional but recommended
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::sidekick-kb-vectors-dev-275666109134",
        "arn:aws:s3:::sidekick-kb-vectors-dev-275666109134/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "275666109134"
        },
        "ArnLike": {
          "aws:SourceArn": "arn:aws:bedrock:us-east-1:275666109134:knowledge-base/*"
        }
      }
    }
  ]
}
```

---

### Step 2: Verify Bucket Encryption Settings

**Objective**: Ensure encryption settings don't block Bedrock access

```bash
# Check bucket encryption configuration
aws s3api get-bucket-encryption --bucket ${BUCKET_NAME}

# Check bucket public access block settings
aws s3api get-public-access-block --bucket ${BUCKET_NAME}
```

**Expected**:
- Encryption: S3-managed (SSE-S3) or KMS with proper key policy
- Public access: Should be blocked (this is correct)

---

### Step 3: Review Recent Infrastructure Changes

**Objective**: Identify what changed to cause the issue

```bash
# Check CloudFormation stack updates
aws cloudformation describe-stack-events \
  --stack-name sidekick-knowledge-base-dev \
  --max-items 20 \
  --query 'StackEvents[?ResourceType==`AWS::S3::BucketPolicy`]'

# Check CloudTrail for bucket policy changes
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=${BUCKET_NAME} \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 50 \
  --query 'Events[?EventName==`PutBucketPolicy`]'
```

**Common Causes**:
1. **Infrastructure deployment**: CDK/CloudFormation update with incomplete policy
2. **Manual policy edit**: Someone removed s3:PutObject by mistake
3. **Security hardening**: Overly restrictive policy applied
4. **Copy-paste error**: Policy copied from read-only example

---

### Step 4: Check Knowledge Base Configuration

**Objective**: Verify Knowledge Base is configured correctly

```bash
# Get Knowledge Base details
KB_ID="YOUR_KB_ID"  # Replace with actual KB ID

aws bedrock-agent get-knowledge-base \
  --knowledge-base-id ${KB_ID}

# Check data source configuration
aws bedrock-agent list-data-sources \
  --knowledge-base-id ${KB_ID}

# Get latest sync job status
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id ${KB_ID} \
  --max-results 5
```

**Look for**:
- Storage configuration pointing to correct S3 bucket
- Recent failed ingestion jobs
- Error messages in job details

---

### Step 5: Test Bedrock's Access Directly

**Objective**: Simulate what Bedrock is trying to do

```bash
# Create a test file
echo "test vector data" > test-vector.json

# Try to upload as if we were Bedrock (this will fail with current policy)
aws s3 cp test-vector.json s3://${BUCKET_NAME}/test/test-vector.json

# This should fail with "Access Denied" if policy is missing PutObject
# Note: This tests with your credentials, not Bedrock's, but validates bucket accessibility
```

---

## Resolution Strategy

### Fix: Add Missing s3:PutObject Permission

**When to Use**: Bucket policy is missing `s3:PutObject` permission (most common)

**Steps**:

1. **Backup Current Policy**
   ```bash
   BUCKET_NAME="sidekick-kb-vectors-dev-275666109134"
   
   # Save current policy for rollback
   aws s3api get-bucket-policy \
     --bucket ${BUCKET_NAME} \
     --query Policy \
     --output text > bucket-policy-backup-$(date +%Y%m%d-%H%M%S).json
   
   echo "Policy backed up to: bucket-policy-backup-$(date +%Y%m%d-%H%M%S).json"
   ```

2. **Create Corrected Policy**
   ```bash
   # Get your AWS account ID
   ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   REGION="us-east-1"
   
   cat > corrected-bucket-policy.json << EOF
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "BedrockKnowledgeBaseAccess",
         "Effect": "Allow",
         "Principal": {
           "Service": "bedrock.amazonaws.com"
         },
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::${BUCKET_NAME}",
           "arn:aws:s3:::${BUCKET_NAME}/*"
         ],
         "Condition": {
           "StringEquals": {
             "aws:SourceAccount": "${ACCOUNT_ID}"
           },
           "ArnLike": {
             "aws:SourceArn": "arn:aws:bedrock:${REGION}:${ACCOUNT_ID}:knowledge-base/*"
           }
         }
       }
     ]
   }
   EOF
   
   echo "Corrected policy created: corrected-bucket-policy.json"
   ```

3. **Apply Corrected Policy**
   ```bash
   # Apply the corrected policy
   aws s3api put-bucket-policy \
     --bucket ${BUCKET_NAME} \
     --policy file://corrected-bucket-policy.json
   
   echo "✅ Policy applied successfully!"
   
   # Verify the policy was applied correctly
   aws s3api get-bucket-policy \
     --bucket ${BUCKET_NAME} \
     --query Policy \
     --output text | jq .
   ```

4. **Test Upload Capability**
   ```bash
   # Test that uploads now work
   echo "test upload at $(date)" > test-upload.txt
   
   aws s3 cp test-upload.txt s3://${BUCKET_NAME}/test/test-upload.txt
   
   # Should succeed with no errors
   if [ $? -eq 0 ]; then
     echo "✅ Upload test successful!"
     # Clean up test file
     aws s3 rm s3://${BUCKET_NAME}/test/test-upload.txt
   else
     echo "❌ Upload test failed - further investigation needed"
   fi
   ```

**Expected Result**: Policy update takes effect immediately (within seconds)

**Rollback Plan**: If issues occur, restore original policy:
```bash
aws s3api put-bucket-policy \
  --bucket ${BUCKET_NAME} \
  --policy file://bucket-policy-backup-*.json
```

---

## Verification Steps

### 1. Verify Policy Update
```bash
# Confirm s3:PutObject is now in the policy
aws s3api get-bucket-policy \
  --bucket ${BUCKET_NAME} \
  --query Policy \
  --output text | jq '.Statement[].Action' | grep -i putobject

# Should return: "s3:PutObject"
```

**Expected**: Policy now includes `s3:PutObject` action

---

### 2. Trigger Knowledge Base Sync
```bash
# Start a new ingestion job to test the fix
KB_ID="YOUR_KB_ID"  # Replace with actual KB ID
DATA_SOURCE_ID="YOUR_DATA_SOURCE_ID"  # Replace with actual data source ID

aws bedrock-agent start-ingestion-job \
  --knowledge-base-id ${KB_ID} \
  --data-source-id ${DATA_SOURCE_ID}

# Get the ingestion job ID from the response
INGESTION_JOB_ID="<job-id-from-response>"

# Monitor the job status
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id ${KB_ID} \
  --data-source-id ${DATA_SOURCE_ID} \
  --ingestion-job-id ${INGESTION_JOB_ID}
```

**Expected**: Ingestion job status should be "IN_PROGRESS" then "COMPLETE"

---

### 3. Monitor CloudWatch Logs
```bash
# Check for successful S3 operations in CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=${BUCKET_NAME} \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --max-results 10

# Should see successful PutObject events from bedrock.amazonaws.com
```

**Expected**: No more 403 errors; successful PutObject operations visible

---

### 4. Verify Vector Storage
```bash
# List objects in the vector bucket to confirm uploads
aws s3 ls s3://${BUCKET_NAME}/ --recursive | head -20

# Should see vector embedding files being created
```

**Expected**: New vector files appearing in the bucket

---

### 5. Test Knowledge Base Queries
```bash
# Test querying the Knowledge Base
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id ${KB_ID} \
  --retrieval-query text="test query" \
  --retrieval-configuration '{"vectorSearchConfiguration":{"numberOfResults":5}}'

# Should return relevant results without errors
```

**Expected**: Successful query responses with relevant documents

---

## Post-Resolution Actions

### 1. Update Incident Status
```
Incident: INC-2025-KB-001
Status: Resolved
Resolution: Added missing s3:PutObject permission to vector bucket policy
Root Cause: Infrastructure deployment updated bucket policy but omitted 
            s3:PutObject action, preventing Bedrock from writing vector embeddings
Resolution Time: 12 minutes
Impact: Knowledge Base sync failures for 45 minutes; no new documents indexed
```

### 2. Communication
- Post resolution summary in incident channel
- Update status page: "Knowledge Base sync functionality restored"
- Notify stakeholders of resolution
- Document timeline and actions taken

### 3. Update Infrastructure Code
```bash
# If using CDK/CloudFormation, update the infrastructure code
# to include s3:PutObject in the bucket policy

# Example CDK fix in knowledge_base_stack.py:
# Change:
#   actions=["s3:GetObject", "s3:ListBucket"]
# To:
#   actions=["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]

# Commit and deploy the fix
git add infra/stacks/knowledge_base_stack.py
git commit -m "fix: Add s3:PutObject permission to KB vector bucket policy"
git push origin main
```

### 4. Preventive Measures
- [ ] Add automated tests for S3 bucket policies in CI/CD
- [ ] Create CloudWatch alarm for Knowledge Base sync failures
- [ ] Add policy validation to infrastructure deployment process
- [ ] Document required S3 permissions for Bedrock Knowledge Base
- [ ] Create pre-deployment checklist for S3 policy changes
- [ ] Add S3 permission checks to monitoring dashboard
- [ ] Schedule quarterly review of all Bedrock-related S3 policies
- [ ] Create runbook for common Bedrock permission issues

---

## Common Pitfalls and Tips

### Pitfall 1: Forgetting Both Bucket and Object ARNs
```json
// WRONG - Only bucket ARN
"Resource": "arn:aws:s3:::bucket-name"

// CORRECT - Both bucket and objects
"Resource": [
  "arn:aws:s3:::bucket-name",
  "arn:aws:s3:::bucket-name/*"
]
```

### Pitfall 2: Wrong Service Principal
```json
// WRONG - Using IAM role instead of service principal
"Principal": {
  "AWS": "arn:aws:iam::123456789012:role/BedrockRole"
}

// CORRECT - Bedrock service principal
"Principal": {
  "Service": "bedrock.amazonaws.com"
}
```

### Pitfall 3: Missing Condition Keys
- Always include `aws:SourceAccount` to prevent cross-account access
- Always include `aws:SourceArn` to limit to specific Knowledge Bases
- These conditions are security best practices

### Pitfall 4: Testing with Wrong Credentials
- Your admin credentials will work even if Bedrock's don't
- Always trigger an actual Knowledge Base sync to test
- Check CloudTrail for Bedrock service events, not your user events

### Pitfall 5: Not Updating Infrastructure Code
- Fixing the policy manually is temporary
- If you redeploy infrastructure, the faulty policy will return
- Always update CDK/CloudFormation/Terraform code

---

## Infrastructure Code Fix

**For CDK (Python)**:
```python
# In infra/stacks/knowledge_base_stack.py

# BEFORE (Faulty):
faulty_policy = iam.PolicyDocument(
    statements=[
        iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:ListBucket",
                # Missing s3:PutObject!
            ],
            # ... rest of policy
        )
    ]
)

# AFTER (Corrected):
corrected_policy = iam.PolicyDocument(
    statements=[
        iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:PutObject",      # ✅ Added
                "s3:DeleteObject",   # ✅ Added (optional but recommended)
                "s3:ListBucket",
            ],
            # ... rest of policy
        )
    ]
)
```

**Deploy the fix**:
```bash
cd infra
cdk diff sidekick-knowledge-base-dev
cdk deploy sidekick-knowledge-base-dev
```

---

## Quick Reference Commands

```bash
# Set variables
BUCKET_NAME="sidekick-kb-vectors-dev-275666109134"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Get current policy
aws s3api get-bucket-policy --bucket ${BUCKET_NAME} --query Policy --output text | jq .

# Backup policy
aws s3api get-bucket-policy --bucket ${BUCKET_NAME} --query Policy --output text > backup.json

# Apply corrected policy
aws s3api put-bucket-policy --bucket ${BUCKET_NAME} --policy file://corrected-policy.json

# Test upload
echo "test" > test.txt && aws s3 cp test.txt s3://${BUCKET_NAME}/test/

# Check CloudTrail for Bedrock events
aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=${BUCKET_NAME}

# Trigger KB sync
aws bedrock-agent start-ingestion-job --knowledge-base-id ${KB_ID} --data-source-id ${DS_ID}

# Monitor sync status
aws bedrock-agent get-ingestion-job --knowledge-base-id ${KB_ID} --data-source-id ${DS_ID} --ingestion-job-id ${JOB_ID}
```

---

## Escalation Path

**Level 1**: On-call AI/ML Engineer (0-15 minutes)  
**Level 2**: AI/ML Platform Lead (15-30 minutes)  
**Level 3**: VP Engineering (30-60 minutes)  
**Level 4**: AWS Support - Bedrock Team (if AWS service issue suspected)

---

## Related Documentation

- [Amazon Bedrock Knowledge Base S3 Permissions](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-permissions.html)
- [S3 Bucket Policy Examples for Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-s3-policies.html)
- [Troubleshooting Bedrock Knowledge Base](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-troubleshooting.html)
- [S3 Access Denied Troubleshooting](https://aws.amazon.com/premiumsupport/knowledge-center/s3-troubleshoot-403/)
- [Internal: Bedrock Knowledge Base Architecture](link)
- [Internal: Production Incident Response Playbook](link)

---

**Document Owner**: AI/ML Platform Engineering Team  
**Last Updated**: October 20, 2025  
**Review Frequency**: Quarterly  
**Emergency Contact**: aiml-oncall@acmecorp.com  
**Slack Channel**: #aiml-platform-sre
