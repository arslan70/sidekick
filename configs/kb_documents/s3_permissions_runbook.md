# S3 Permissions Troubleshooting Runbook

---
**RUNBOOK METADATA**  
**Incident IDs**: INC-2025-5001  
**Keywords**: S3, permissions, 403, forbidden, access denied, file upload, PutObject, bucket policy  
**Affected Services**: File Upload Service, S3 Storage Backend, acmecorp-uploads bucket  
**Use Case**: Resolves S3 permission denied errors preventing file uploads  
---

## Incident Reference

**Incident ID**: INC-2025-5001  
**Incident Title**: File Upload Failures - S3 Permission Denied  
**Affected Bucket**: acmecorp-uploads  
**Related Incidents**: INC-2025-5001

## Overview

This runbook provides step-by-step procedures for diagnosing and resolving S3 bucket permission issues that cause file upload failures and 403 Forbidden errors in production environments. This runbook specifically addresses incidents like INC-2025-5001 where users experience 403 Forbidden errors when uploading files to S3.

**Severity**: High  
**Expected Resolution Time**: 15-30 minutes  
**On-Call Team**: Platform Engineering - SRE

---

## Symptoms

- Users receiving "Upload Failed" errors when attempting to upload files
- 403 Forbidden errors in application logs
- CloudWatch logs showing "Access Denied" errors from S3 API calls
- File upload service returning permission denied responses
- S3 PutObject operations failing consistently
- Upload success rate dropped to 0%

---

## Immediate Actions (First 5 Minutes)

### 1. Verify the Issue
```bash
# Check recent S3 API errors in CloudWatch
aws logs filter-log-events \
  --log-group-name /aws/ecs/file-upload-service \
  --filter-pattern "403" \
  --start-time $(date -u -d '30 minutes ago' +%s)000 \
  --limit 20

# Check S3 bucket exists and is accessible
aws s3 ls s3://acmecorp-uploads/ --region us-east-1

# Verify bucket location and status
aws s3api get-bucket-location --bucket acmecorp-uploads
```

### 2. Establish War Room
- Create Slack channel: `#incident-s3-permissions`
- Page on-call SRE via PagerDuty
- Update status page: "Investigating file upload issues"
- Notify stakeholders: Engineering leadership, Product team

### 3. Gather Initial Data
- Number of affected users (check error logs)
- When did the issue start? (check CloudWatch metrics)
- Recent deployments or configuration changes (last 24 hours)
- Current bucket policy and IAM role configuration

---

## Diagnostic Steps

### Step 1: Check Bucket Policy

**Objective**: Verify bucket policy allows required S3 operations

```bash
# Retrieve current bucket policy
aws s3api get-bucket-policy \
  --bucket acmecorp-uploads \
  --query Policy \
  --output text | jq .

# Check bucket ACL
aws s3api get-bucket-acl --bucket acmecorp-uploads

# Verify public access block settings
aws s3api get-public-access-block --bucket acmecorp-uploads
```

**What to Look For**:
- Does the policy include `s3:PutObject` permission?
- Is the correct IAM role/principal specified?
- Are the resource ARNs correct?
- Is the policy syntax valid JSON?

**Common Issues**:
1. **Missing s3:PutObject**: Policy only has `s3:GetObject` and `s3:ListBucket`
2. **Wrong Principal**: Policy references old or incorrect IAM role
3. **Incorrect Resource ARN**: Missing `/*` suffix for object-level operations
4. **Overly Restrictive Conditions**: IP restrictions or time-based conditions blocking access

**Expected Policy Structure**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowFileUploadService",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/FileUploadServiceRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",      ← MUST BE PRESENT
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::acmecorp-uploads",
        "arn:aws:s3:::acmecorp-uploads/*"  ← MUST INCLUDE /*
      ]
    }
  ]
}
```

---

### Step 2: Verify IAM Role Permissions

**Objective**: Ensure the service's IAM role has necessary permissions

```bash
# Get the IAM role used by the file upload service
aws ecs describe-services \
  --cluster production \
  --services file-upload-service \
  --query 'services[0].taskDefinition' \
  --output text

# Get task definition to find IAM role
aws ecs describe-task-definition \
  --task-definition file-upload-service:latest \
  --query 'taskDefinition.taskRoleArn' \
  --output text

# Check IAM role policies
aws iam get-role --role-name FileUploadServiceRole

# List attached policies
aws iam list-attached-role-policies --role-name FileUploadServiceRole

# Get inline policies
aws iam list-role-policies --role-name FileUploadServiceRole

# View specific policy document
aws iam get-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/FileUploadServicePolicy \
  --version-id v1 \
  --query 'PolicyVersion.Document'
```

**What to Look For**:
- Does the IAM role policy include `s3:PutObject`?
- Is the bucket ARN correctly specified?
- Are there any Deny statements blocking access?
- Is the role's trust policy correct?

**Expected IAM Policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::acmecorp-uploads",
        "arn:aws:s3:::acmecorp-uploads/*"
      ]
    }
  ]
}
```

---

### Step 3: Check for Conflicting Policies

**Objective**: Identify any policies that might be denying access

```bash
# Check for Service Control Policies (SCPs) if using AWS Organizations
aws organizations list-policies-for-target \
  --target-id 123456789012 \
  --filter SERVICE_CONTROL_POLICY

# Check for permission boundaries on the IAM role
aws iam get-role --role-name FileUploadServiceRole \
  --query 'Role.PermissionsBoundary'

# Simulate the PutObject operation to see what's blocking it
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/FileUploadServiceRole \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::acmecorp-uploads/test-file.txt
```

**Common Conflicts**:
1. **Explicit Deny in SCP**: Organization-level policy blocking S3 writes
2. **Permission Boundary**: Limits maximum permissions for the role
3. **Bucket Policy Deny**: Explicit deny statement overriding allow
4. **S3 Block Public Access**: Incorrectly configured blocking legitimate access

---

### Step 4: Review Recent Changes

**Objective**: Identify what changed to cause the issue

**Check**:
1. **Recent Deployments** (last 24 hours)
   ```bash
   # Check ECS service deployment history
   aws ecs describe-services \
     --cluster production \
     --services file-upload-service \
     --query 'services[0].deployments'
   
   # Check CloudFormation stack updates
   aws cloudformation describe-stack-events \
     --stack-name file-upload-infrastructure \
     --max-items 20
   ```

2. **IAM Policy Changes**
   ```bash
   # Check CloudTrail for IAM policy modifications
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::IAM::Policy \
     --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
     --max-results 50
   ```

3. **S3 Bucket Policy Changes**
   ```bash
   # Check CloudTrail for S3 bucket policy changes
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=ResourceName,AttributeValue=acmecorp-uploads \
     --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
     --max-results 50
   ```

4. **Configuration Changes**
   - Infrastructure-as-Code updates (Terraform, CloudFormation, CDK)
   - Manual console changes
   - Automated policy updates

---

### Step 5: Test Permissions Directly

**Objective**: Confirm the exact permission issue

```bash
# Assume the service role (if you have permission)
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/FileUploadServiceRole \
  --role-session-name debug-session

# Export temporary credentials
export AWS_ACCESS_KEY_ID=<AccessKeyId>
export AWS_SECRET_ACCESS_KEY=<SecretAccessKey>
export AWS_SESSION_TOKEN=<SessionToken>

# Test upload operation
echo "test content" > test-upload.txt
aws s3 cp test-upload.txt s3://acmecorp-uploads/test/test-upload.txt

# Check the error message
# Expected: "Access Denied" or "403 Forbidden" if permissions are missing
```

---

## Resolution Strategies

### Option 1: Update Bucket Policy (Most Common)

**When to Use**: Bucket policy is missing `s3:PutObject` permission

**Steps**:

1. **Backup Current Policy**
   ```bash
   # Save current policy for rollback
   aws s3api get-bucket-policy \
     --bucket acmecorp-uploads \
     --query Policy \
     --output text > bucket-policy-backup.json
   ```

2. **Create Updated Policy**
   ```bash
   cat > updated-bucket-policy.json << 'EOF'
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AllowFileUploadServiceReadWrite",
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::123456789012:role/FileUploadServiceRole"
         },
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::acmecorp-uploads",
           "arn:aws:s3:::acmecorp-uploads/*"
         ]
       }
     ]
   }
   EOF
   ```

3. **Apply Updated Policy**
   ```bash
   # Apply the new policy
   aws s3api put-bucket-policy \
     --bucket acmecorp-uploads \
     --policy file://updated-bucket-policy.json
   
   # Verify the policy was applied
   aws s3api get-bucket-policy \
     --bucket acmecorp-uploads \
     --query Policy \
     --output text | jq .
   ```

4. **Test Immediately**
   ```bash
   # Test upload with service role
   echo "test" > test-file.txt
   aws s3 cp test-file.txt s3://acmecorp-uploads/test/ \
     --profile service-role-profile
   
   # Should succeed with no errors
   ```

**Expected Result**: File uploads should work immediately (within seconds)

**Rollback Plan**: If issues occur, restore original policy:
```bash
aws s3api put-bucket-policy \
  --bucket acmecorp-uploads \
  --policy file://bucket-policy-backup.json
```

---

### Option 2: Update IAM Role Policy

**When to Use**: Bucket policy is correct, but IAM role policy is missing permissions

**Steps**:

1. **Backup Current Policy**
   ```bash
   aws iam get-role-policy \
     --role-name FileUploadServiceRole \
     --policy-name S3AccessPolicy > iam-policy-backup.json
   ```

2. **Create Updated IAM Policy**
   ```bash
   cat > updated-iam-policy.json << 'EOF'
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::acmecorp-uploads",
           "arn:aws:s3:::acmecorp-uploads/*"
         ]
       }
     ]
   }
   EOF
   ```

3. **Apply Updated Policy**
   ```bash
   aws iam put-role-policy \
     --role-name FileUploadServiceRole \
     --policy-name S3AccessPolicy \
     --policy-document file://updated-iam-policy.json
   ```

4. **Restart Service** (if needed for policy refresh)
   ```bash
   aws ecs update-service \
     --cluster production \
     --service file-upload-service \
     --force-new-deployment
   ```

**Expected Result**: Permissions take effect within 1-2 minutes

---

### Option 3: Fix Resource ARN Syntax

**When to Use**: Policy has correct actions but wrong resource ARN

**Common Mistakes**:
```json
// WRONG - Missing /* for object operations
"Resource": "arn:aws:s3:::acmecorp-uploads"

// CORRECT - Includes both bucket and objects
"Resource": [
  "arn:aws:s3:::acmecorp-uploads",
  "arn:aws:s3:::acmecorp-uploads/*"
]
```

**Fix**:
```bash
# Update policy with correct resource ARNs
# Use Option 1 or Option 2 steps above with corrected ARNs
```

---

### Option 4: Remove Conflicting Deny Statements

**When to Use**: Explicit Deny statement is blocking access

**Steps**:

1. **Identify Deny Statement**
   ```bash
   # Check all policies for Deny statements
   aws s3api get-bucket-policy --bucket acmecorp-uploads \
     --query Policy --output text | jq '.Statement[] | select(.Effect == "Deny")'
   ```

2. **Evaluate if Deny is Necessary**
   - Is it blocking malicious access?
   - Is it overly broad?
   - Can it be made more specific?

3. **Remove or Modify Deny**
   ```bash
   # Edit policy to remove or refine Deny statement
   # Then apply using put-bucket-policy
   ```

**Caution**: Deny statements often exist for security reasons. Consult security team before removing.

---

## Verification Steps

### 1. Test File Upload Functionality
```bash
# Create test file
echo "Test upload at $(date)" > test-upload-$(date +%s).txt

# Upload using service credentials
aws s3 cp test-upload-*.txt s3://acmecorp-uploads/test/ \
  --profile service-role-profile

# Verify upload succeeded
aws s3 ls s3://acmecorp-uploads/test/ | grep test-upload

# Clean up test file
aws s3 rm s3://acmecorp-uploads/test/test-upload-*.txt
```

**Expected Result**: Upload succeeds with no errors

---

### 2. Check Application Logs
```bash
# Monitor application logs for successful uploads
aws logs tail /aws/ecs/file-upload-service \
  --since 5m \
  --follow \
  --filter-pattern "upload"

# Should see successful upload log entries
# Should NOT see 403 or Access Denied errors
```

---

### 3. Verify CloudWatch Metrics
```bash
# Check S3 request metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 4xxErrors \
  --dimensions Name=BucketName,Value=acmecorp-uploads \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# Should show 0 or very low 4xx errors
```

**Expected**: 4xx error count drops to 0 within 2-3 minutes

---

### 4. Monitor User Reports
- Check support tickets for upload issues
- Monitor Slack channels for user complaints
- Review application error tracking (Sentry, Datadog, etc.)
- Confirm users can successfully upload files

**Expected**: No new upload failure reports

---

### 5. End-to-End User Test
```bash
# Have a team member test actual upload flow
# 1. Log into application
# 2. Navigate to file upload page
# 3. Select file and upload
# 4. Verify file appears in application
# 5. Verify file exists in S3 bucket
```

---

## Post-Resolution Actions

### 1. Update Incident Status
```
Incident: INC-2025-5001
Status: Resolved
Resolution: Added missing s3:PutObject permission to bucket policy
Root Cause: Bucket policy was updated during infrastructure migration but 
            s3:PutObject permission was inadvertently omitted
Resolution Time: 18 minutes
Impact: 500+ users unable to upload files for 35 minutes
```

### 2. Internal Communication
- Post resolution summary in war room channel
- Update status page: "File upload functionality restored"
- Send all-clear notification to stakeholders
- Thank team members for quick response

### 3. Documentation
- Update incident log with complete timeline
- Document root cause analysis
- Add lessons learned to this runbook
- Update infrastructure-as-code to prevent recurrence

### 4. Preventive Measures
- [ ] Add automated tests for S3 permissions in CI/CD pipeline
- [ ] Implement CloudWatch alarm for S3 4xx errors
- [ ] Add policy validation to infrastructure deployment process
- [ ] Create pre-deployment checklist for S3 policy changes
- [ ] Schedule review of all S3 bucket policies
- [ ] Add S3 permission checks to monitoring dashboard
- [ ] Document S3 policy change approval process
- [ ] Create automated policy backup before changes

---

### 5. Post-Mortem Meeting
**Schedule**: Within 48 hours of resolution

**Agenda**:
1. Timeline review
2. Root cause analysis
3. What went well?
4. What could be improved?
5. Action items to prevent recurrence

**Attendees**:
- SRE team
- Platform engineering
- DevOps lead
- Engineering manager

---

## Common Pitfalls and Tips

### Pitfall 1: Forgetting the `/*` in Resource ARN
```json
// WRONG - Only allows bucket-level operations
"Resource": "arn:aws:s3:::acmecorp-uploads"

// CORRECT - Allows both bucket and object operations
"Resource": [
  "arn:aws:s3:::acmecorp-uploads",
  "arn:aws:s3:::acmecorp-uploads/*"
]
```

### Pitfall 2: Testing with Wrong Credentials
- Always test with the actual service role credentials
- Don't test with admin credentials (will always work)
- Use `aws sts assume-role` to test with service role

### Pitfall 3: Not Waiting for Policy Propagation
- IAM policy changes can take 1-2 minutes to propagate
- S3 bucket policy changes are usually immediate
- Wait and retry before assuming fix didn't work

### Pitfall 4: Overlooking Explicit Deny
- Explicit Deny always overrides Allow
- Check all policies (bucket, IAM, SCP, permission boundaries)
- Use `aws iam simulate-principal-policy` to debug

### Pitfall 5: Incorrect Principal Format
```json
// WRONG - Missing AWS key
"Principal": "arn:aws:iam::123456789012:role/MyRole"

// CORRECT - Proper format
"Principal": {
  "AWS": "arn:aws:iam::123456789012:role/MyRole"
}
```

---

## Escalation Path

**Level 1**: On-call SRE (0-15 minutes)  
**Level 2**: Platform Engineering Lead (15-30 minutes)  
**Level 3**: VP Engineering (30-60 minutes)  
**Level 4**: AWS Support (if AWS service issue suspected)

---

## Related Documentation

- [AWS S3 Bucket Policy Examples](https://docs.aws.amazon.com/AmazonS3/latest/userguide/example-bucket-policies.html)
- [IAM Policy Evaluation Logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [S3 Access Denied Troubleshooting](https://aws.amazon.com/premiumsupport/knowledge-center/s3-troubleshoot-403/)
- [File Upload Service Architecture](link)
- [Production Incident Response Playbook](link)

---

## Quick Reference Commands

```bash
# Get bucket policy
aws s3api get-bucket-policy --bucket BUCKET_NAME --query Policy --output text | jq .

# Update bucket policy
aws s3api put-bucket-policy --bucket BUCKET_NAME --policy file://policy.json

# Check IAM role
aws iam get-role --role-name ROLE_NAME

# List IAM role policies
aws iam list-attached-role-policies --role-name ROLE_NAME

# Simulate permission
aws iam simulate-principal-policy \
  --policy-source-arn ROLE_ARN \
  --action-names s3:PutObject \
  --resource-arns BUCKET_ARN

# Test upload
aws s3 cp test.txt s3://BUCKET_NAME/test/

# Check CloudWatch logs
aws logs tail /aws/ecs/SERVICE_NAME --since 5m --filter-pattern "403"
```

---

**Document Owner**: Platform Engineering - SRE Team  
**Last Updated**: October 19, 2025  
**Review Frequency**: Quarterly  
**Emergency Contact**: platform-oncall@acmecorp.com  
**Slack Channel**: #platform-sre
