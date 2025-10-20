# AWS Cost Optimization Guide

## Overview

This comprehensive guide provides strategies, best practices, and actionable recommendations for optimizing AWS infrastructure costs while maintaining performance, reliability, and security.

**Target Audience**: DevOps Engineers, Cloud Architects, Engineering Leadership  
**Last Updated**: October 2025

---

## 1. Cost Optimization Principles

### The Four Pillars
1. **Right-Sizing**: Match resources to actual usage
2. **Purchasing Options**: Leverage Reserved Instances and Savings Plans
3. **Waste Elimination**: Remove unused and idle resources
4. **Architecture Optimization**: Design for cost efficiency

### Cost Optimization Mindset
- **Measure Everything**: You can't optimize what you don't measure
- **Automate**: Manual cost management doesn't scale
- **Continuous Improvement**: Cost optimization is ongoing, not one-time
- **Balance**: Don't sacrifice reliability for cost savings

---

## 2. EC2 Cost Optimization

### Right-Sizing Instances

**Identify Underutilized Instances**:
```bash
# Check CPU utilization (target: 40-70% average)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average
```

**Right-Sizing Recommendations**:
| Current Instance | Avg CPU | Recommendation | Monthly Savings |
|------------------|---------|----------------|-----------------|
| m5.2xlarge | 15% | m5.large | $140 |
| c5.4xlarge | 25% | c5.xlarge | $280 |
| r5.xlarge | 10% | r5.large | $70 |

**Action Steps**:
1. Identify instances with <30% average CPU utilization
2. Test downsized instance in staging environment
3. Schedule maintenance window for production change
4. Monitor performance for 1 week post-change
5. Document savings and performance impact

---

### Reserved Instances & Savings Plans

**When to Use Reserved Instances**:
- Steady-state workloads running 24/7
- Predictable usage patterns
- 1-year or 3-year commitment acceptable

**Savings Comparison**:
| Instance Type | On-Demand | 1-Year RI | 3-Year RI | Savings |
|---------------|-----------|-----------|-----------|---------|
| m5.2xlarge | $280/month | $182/month | $140/month | 35-50% |
| c5.4xlarge | $520/month | $338/month | $260/month | 35-50% |
| r5.xlarge | $230/month | $150/month | $115/month | 35-50% |

**Recommendation**:
```
Current Spend: 3 production instances running 24/7
- m5.2xlarge (API servers): 2 instances
- r5.xlarge (database): 1 instance

Action: Purchase 1-year Reserved Instances
- 2x m5.2xlarge: Save $196/month
- 1x r5.xlarge: Save $80/month
Total Savings: $276/month = $3,312/year
```

---

### Spot Instances for Non-Critical Workloads

**Use Cases**:
- Batch processing jobs
- CI/CD build servers
- Development/testing environments
- Data analysis workloads
- Stateless web servers (with Auto Scaling)

**Savings**: Up to 90% compared to On-Demand

**Example**:
```yaml
# Auto Scaling Group with Spot Instances
LaunchTemplate:
  InstanceType: m5.large
  SpotOptions:
    MaxPrice: "0.05"  # 50% of On-Demand price
    SpotInstanceType: one-time

AutoScalingGroup:
  MinSize: 2
  MaxSize: 10
  DesiredCapacity: 4
  MixedInstancesPolicy:
    InstancesDistribution:
      OnDemandBaseCapacity: 2  # Always have 2 On-Demand
      OnDemandPercentageAboveBaseCapacity: 0  # Rest are Spot
      SpotAllocationStrategy: capacity-optimized
```

**Savings**: $280/month → $56/month (80% reduction)

---

### Auto Scaling for Variable Workloads

**Target Tracking Scaling**:
```yaml
ScalingPolicy:
  PolicyType: TargetTrackingScaling
  TargetTrackingConfiguration:
    PredefinedMetricType: ASGAverageCPUUtilization
    TargetValue: 60.0
    ScaleInCooldown: 300
    ScaleOutCooldown: 60
```

**Schedule-Based Scaling**:
```yaml
# Scale down during off-hours
ScheduledAction:
  - Name: ScaleDownEvening
    Recurrence: "0 18 * * *"  # 6 PM daily
    MinSize: 2
    MaxSize: 4
    DesiredCapacity: 2
  
  - Name: ScaleUpMorning
    Recurrence: "0 8 * * *"  # 8 AM daily
    MinSize: 4
    MaxSize: 10
    DesiredCapacity: 6
```

**Savings**: Running 6 instances 24/7 vs 6 during business hours (10h) + 2 off-hours (14h)
- Before: 6 instances × 24h = 144 instance-hours/day
- After: (6 × 10h) + (2 × 14h) = 88 instance-hours/day
- Savings: 39% reduction = ~$1,200/month

---

## 3. S3 Cost Optimization

### Storage Class Optimization

**Storage Class Comparison**:
| Storage Class | Use Case | Cost (per GB/month) | Retrieval Cost |
|---------------|----------|---------------------|----------------|
| S3 Standard | Frequently accessed | $0.023 | Free |
| S3 Intelligent-Tiering | Unknown access patterns | $0.023 + $0.0025 | Free |
| S3 Standard-IA | Infrequently accessed | $0.0125 | $0.01/GB |
| S3 One Zone-IA | Non-critical, infrequent | $0.01 | $0.01/GB |
| S3 Glacier Instant | Archive, instant retrieval | $0.004 | $0.03/GB |
| S3 Glacier Flexible | Archive, 1-5 min retrieval | $0.0036 | $0.02/GB |
| S3 Glacier Deep Archive | Long-term archive, 12h | $0.00099 | $0.02/GB |

**Lifecycle Policy Example**:
```json
{
  "Rules": [
    {
      "Id": "MoveToIA",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "GLACIER_IR"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}
```

**Savings Example**:
```
Current: 1 TB in S3 Standard
- Cost: 1000 GB × $0.023 = $23/month

Optimized with Lifecycle:
- 200 GB Standard (frequently accessed): $4.60
- 300 GB Standard-IA (30-90 days old): $3.75
- 500 GB Glacier Instant (90+ days old): $2.00
- Total: $10.35/month

Savings: $12.65/month = 55% reduction
```

---

### S3 Intelligent-Tiering

**When to Use**:
- Unknown or changing access patterns
- Don't want to manage lifecycle policies
- Objects >128 KB

**How It Works**:
- Monitors access patterns automatically
- Moves objects between tiers based on access
- No retrieval fees
- Small monitoring fee: $0.0025 per 1,000 objects

**Configuration**:
```bash
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket my-bucket \
  --id EntireBucket \
  --intelligent-tiering-configuration '{
    "Id": "EntireBucket",
    "Status": "Enabled",
    "Tierings": [
      {
        "Days": 90,
        "AccessTier": "ARCHIVE_ACCESS"
      },
      {
        "Days": 180,
        "AccessTier": "DEEP_ARCHIVE_ACCESS"
      }
    ]
  }'
```

**Savings**: 30-50% for mixed access patterns

---

### Delete Incomplete Multipart Uploads

**Problem**: Incomplete multipart uploads consume storage but aren't visible

**Solution**:
```json
{
  "Rules": [
    {
      "Id": "DeleteIncompleteMultipartUploads",
      "Status": "Enabled",
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
```

**Typical Savings**: 5-10% of S3 costs

---

## 4. RDS Cost Optimization

### Right-Sizing Database Instances

**Metrics to Monitor**:
- CPU Utilization (target: 40-70%)
- Memory (target: <80% used)
- IOPS (should not be consistently maxed)
- Connection count (should be <80% of max)

**Example Analysis**:
```
Current: db.r5.2xlarge (8 vCPU, 64 GB RAM)
- Avg CPU: 25%
- Avg Memory: 45%
- Max Connections: 150 (limit: 5000)

Recommendation: db.r5.xlarge (4 vCPU, 32 GB RAM)
- Sufficient for current load
- Savings: $280/month
```

---

### Reserved Instances for RDS

**Savings**:
| Instance | On-Demand | 1-Year RI | 3-Year RI | Savings |
|----------|-----------|-----------|-----------|---------|
| db.r5.xlarge | $496/month | $322/month | $248/month | 35-50% |
| db.r5.2xlarge | $992/month | $644/month | $496/month | 35-50% |

**Recommendation**:
```
Production database running 24/7:
- Current: db.r5.2xlarge On-Demand = $992/month
- Action: Purchase 1-year RI = $644/month
- Savings: $348/month = $4,176/year
```

---

### Aurora Serverless for Variable Workloads

**Use Cases**:
- Development/testing databases
- Infrequently used applications
- Variable traffic patterns
- New applications with unknown demand

**Cost Model**:
- Pay per second of database usage
- Automatically scales capacity
- Pauses during inactivity (no charges)

**Example**:
```
Traditional RDS:
- db.r5.large running 24/7 = $248/month

Aurora Serverless v2:
- Active 8 hours/day, 5 days/week
- 2 ACUs average during active periods
- Cost: ~$80/month

Savings: $168/month = 68% reduction
```

---

## 5. Lambda Cost Optimization

### Right-Size Memory Allocation

**Key Insight**: Lambda charges for GB-seconds. More memory = faster execution = potentially lower cost.

**Example**:
```
Function with 128 MB memory:
- Execution time: 3000ms
- Cost: 128 MB × 3000ms = 384,000 MB-ms

Same function with 512 MB memory:
- Execution time: 800ms (faster due to more CPU)
- Cost: 512 MB × 800ms = 409,600 MB-ms

Result: 512 MB is only 6% more expensive but 3.75x faster
```

**Recommendation**: Test with different memory sizes to find optimal cost/performance

---

### Reduce Cold Starts

**Strategies**:
1. **Provisioned Concurrency**: Keep functions warm
   - Cost: $0.015 per GB-hour
   - Use for latency-sensitive functions

2. **Increase Memory**: Faster cold starts
   - More memory = more CPU = faster initialization

3. **Minimize Dependencies**: Smaller package = faster cold start
   - Use Lambda Layers for shared dependencies
   - Remove unused libraries

**Example**:
```
Before: 50 MB package, 2-second cold start
After: 10 MB package, 500ms cold start

For 1000 cold starts/day:
- Time saved: 1500 seconds/day
- Cost saved: ~$5/month
```

---

## 6. Data Transfer Cost Optimization

### Minimize Cross-Region Transfer

**Costs**:
- Same AZ: Free
- Same Region, different AZ: $0.01/GB
- Cross-Region: $0.02/GB
- To Internet: $0.09/GB (first 10 TB)

**Strategies**:
1. **Use CloudFront**: Cache content at edge locations
2. **Regional Architecture**: Keep services in same region
3. **VPC Endpoints**: Avoid internet gateway for AWS services
4. **Direct Connect**: For large data transfers

**Example**:
```
Current: 10 TB/month cross-region transfer
- Cost: 10,000 GB × $0.02 = $200/month

Optimized: Use CloudFront + regional architecture
- CloudFront: 10,000 GB × $0.085 = $850/month
- But reduces origin requests by 80%
- Actual origin transfer: 2,000 GB × $0.02 = $40/month
- Total: $890/month

Wait, that's more expensive! 

Better optimization: Keep services in same region
- Same region transfer: 10,000 GB × $0.01 = $100/month
- Savings: $100/month
```

---

### Use VPC Endpoints

**Problem**: Traffic to S3/DynamoDB via internet gateway incurs NAT Gateway costs

**Solution**: VPC Endpoints (Gateway or Interface)

**Savings**:
```
NAT Gateway:
- $0.045/hour = $32.40/month
- $0.045/GB processed = $450/month for 10 TB

VPC Gateway Endpoint (S3, DynamoDB):
- Free!
- Savings: $482.40/month
```

**Configuration**:
```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345678 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345678
```

---

## 7. Monitoring and Alerting

### Cost Anomaly Detection

**AWS Cost Anomaly Detection**:
```bash
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "ProductionCostMonitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "CostAnomalyAlerts",
    "Threshold": 100,
    "Frequency": "DAILY",
    "MonitorArnList": ["arn:aws:ce::123456789012:anomalymonitor/abc123"],
    "Subscribers": [
      {
        "Type": "EMAIL",
        "Address": "devops@acmecorp.com"
      }
    ]
  }'
```

---

### Budget Alerts

**Example Budget**:
```bash
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "Monthly-Production-Budget",
    "BudgetLimit": {
      "Amount": "5000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {
          "SubscriptionType": "EMAIL",
          "Address": "devops@acmecorp.com"
        }
      ]
    }
  ]'
```

---

### Cost Allocation Tags

**Strategy**:
```
Tag all resources with:
- Environment: production, staging, development
- Project: project-phoenix, project-alpha
- Owner: team-backend, team-frontend
- CostCenter: engineering, sales, marketing
```

**Example**:
```bash
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags \
    Key=Environment,Value=production \
    Key=Project,Value=project-phoenix \
    Key=Owner,Value=team-backend \
    Key=CostCenter,Value=engineering
```

**Benefit**: Track costs by team, project, environment

---

## 8. Quick Wins Checklist

### Immediate Actions (This Week)
- [ ] Delete unused EBS volumes
- [ ] Delete old EBS snapshots (>90 days)
- [ ] Stop non-production instances outside business hours
- [ ] Enable S3 Intelligent-Tiering
- [ ] Delete incomplete multipart uploads
- [ ] Remove unused Elastic IPs
- [ ] Delete old AMIs
- [ ] Review and delete unused load balancers

### Short-Term Actions (This Month)
- [ ] Right-size overprovisioned EC2 instances
- [ ] Purchase Reserved Instances for steady-state workloads
- [ ] Implement Auto Scaling for variable workloads
- [ ] Set up VPC Endpoints for S3 and DynamoDB
- [ ] Enable Cost Anomaly Detection
- [ ] Create budget alerts
- [ ] Implement cost allocation tags

### Long-Term Actions (This Quarter)
- [ ] Migrate to Aurora Serverless for dev/test databases
- [ ] Implement Spot Instances for batch workloads
- [ ] Optimize Lambda memory allocation
- [ ] Review and optimize data transfer patterns
- [ ] Implement CloudFront for static content
- [ ] Evaluate Savings Plans
- [ ] Conduct quarterly cost review

---

## 9. Cost Optimization ROI Calculator

### Example Calculation
```
Current Monthly AWS Spend: $10,000

Optimization Actions:
1. Right-size 5 EC2 instances: Save $700/month
2. Purchase Reserved Instances: Save $640/month
3. Enable S3 Intelligent-Tiering: Save $200/month
4. Implement Auto Scaling: Save $1,200/month
5. Use VPC Endpoints: Save $480/month
6. Delete unused resources: Save $300/month

Total Monthly Savings: $3,520
Annual Savings: $42,240
Savings Percentage: 35.2%

Implementation Effort: 40 hours
Cost of Implementation: $4,000 (at $100/hour)
ROI: $42,240 / $4,000 = 10.56x
Payback Period: 1.1 months
```

---

## 10. Best Practices Summary

### Do's
✅ Monitor costs daily  
✅ Tag all resources  
✅ Right-size regularly  
✅ Use Reserved Instances for steady workloads  
✅ Implement Auto Scaling  
✅ Delete unused resources  
✅ Use appropriate storage classes  
✅ Set up budget alerts  
✅ Review costs monthly  
✅ Automate cost optimization

### Don'ts
❌ Over-provision "just in case"  
❌ Run non-production 24/7  
❌ Ignore cost anomalies  
❌ Use On-Demand for everything  
❌ Keep unused resources  
❌ Forget to delete old snapshots  
❌ Ignore data transfer costs  
❌ Skip tagging resources  
❌ Optimize once and forget  
❌ Sacrifice reliability for cost

---

**Document Owner**: Cloud FinOps Team  
**Last Updated**: October 2025  
**Review Frequency**: Quarterly  
**Questions?**: Contact finops@acmecorp.com
