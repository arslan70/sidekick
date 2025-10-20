# Database Connection Timeout Troubleshooting Runbook

## Overview

This runbook provides step-by-step procedures for diagnosing and resolving database connection timeout issues in production environments.

**Severity**: Critical  
**Expected Resolution Time**: 30-60 minutes  
**On-Call Team**: Database SRE Team

---

## Symptoms

- Users receiving 504 Gateway Timeout errors
- API responses timing out after 30 seconds
- CloudWatch alarms: High database connection count
- Application logs showing "Connection pool exhausted" errors
- Elevated response times across all services

---

## Immediate Actions (First 5 Minutes)

### 1. Verify the Issue
```bash
# Check current connection count
aws rds describe-db-instances --db-instance-identifier prod-db-primary \
  --query 'DBInstances[0].DBInstanceStatus'

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db-primary \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum
```

### 2. Establish War Room
- Create Slack channel: `#incident-YYYY-MM-DD`
- Page on-call engineer via PagerDuty
- Update status page: "Investigating database connectivity issues"
- Notify stakeholders: Engineering leadership, Customer Success

### 3. Gather Initial Data
- Current connection pool utilization
- Recent deployments (last 24 hours)
- Database CPU and memory metrics
- Application error logs

---

## Diagnostic Steps

### Step 1: Check Connection Pool Status

**Objective**: Determine if connection pool is exhausted

```sql
-- Check current connections
SELECT 
    COUNT(*) as total_connections,
    state,
    application_name
FROM pg_stat_activity
WHERE datname = 'production'
GROUP BY state, application_name
ORDER BY total_connections DESC;

-- Identify long-running queries
SELECT 
    pid,
    now() - query_start as duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 minutes'
ORDER BY duration DESC;
```

**Expected Results**:
- Normal: 50-150 connections
- Warning: 150-250 connections
- Critical: >250 connections (pool exhaustion)

**Action if Critical**:
- Proceed to Step 2 (Connection Leak Investigation)
- Consider temporary connection pool increase

---

### Step 2: Investigate Connection Leaks

**Objective**: Identify services not releasing connections

```bash
# Check application logs for connection errors
aws logs tail /aws/ecs/api-gateway --since 30m --filter-pattern "connection"

# Review recent deployments
aws ecs list-task-definitions --family-prefix api-gateway \
  --sort DESC --max-items 5
```

**Common Causes**:
1. **Code Issue**: Missing `connection.close()` in error handling
2. **Transaction Timeout**: Long-running transactions holding connections
3. **Connection Pool Misconfiguration**: Max connections too low
4. **Database Performance**: Slow queries causing connection buildup

**Action**:
- Review code changes from last deployment
- Check for missing connection cleanup in error paths
- Verify transaction timeout settings

---

### Step 3: Check Database Performance

**Objective**: Rule out database-level performance issues

```sql
-- Check for blocking queries
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check database CPU and memory
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched
FROM pg_stat_database
WHERE datname = 'production';
```

**Metrics to Check**:
- CPU utilization: Should be <70%
- Memory: Should have >20% free
- Disk I/O: Check for high wait times
- Cache hit ratio: Should be >95%

---

### Step 4: Review Recent Changes

**Objective**: Identify deployment or configuration changes

**Check**:
1. **Recent Deployments** (last 24 hours)
   - API Gateway service
   - Authentication service
   - Any database-dependent services

2. **Configuration Changes**
   - Connection pool settings
   - Database parameter groups
   - Security group rules

3. **Traffic Patterns**
   - Unusual spike in requests?
   - New feature launched?
   - Marketing campaign?

**Command**:
```bash
# Check recent ECS deployments
aws ecs describe-services --cluster production --services api-gateway \
  --query 'services[0].deployments'

# Check CloudWatch for traffic patterns
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## Resolution Strategies

### Option 1: Rollback Recent Deployment (Fastest)

**When to Use**: If connection issue started immediately after deployment

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster production \
  --service api-gateway \
  --task-definition api-gateway:previous-version \
  --force-new-deployment

# Monitor for improvement
watch -n 5 'aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db-primary \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Maximum \
  --query "Datapoints[0].Maximum"'
```

**Expected Result**: Connection count should decrease within 5-10 minutes

---

### Option 2: Increase Connection Pool (Temporary)

**When to Use**: If traffic spike is legitimate and temporary

```bash
# Update RDS parameter group
aws rds modify-db-parameter-group \
  --db-parameter-group-name production-params \
  --parameters "ParameterName=max_connections,ParameterValue=500,ApplyMethod=immediate"

# Update application connection pool
# Edit environment variable in ECS task definition
MAX_DB_CONNECTIONS=300
```

**Warning**: This is a temporary fix. Investigate root cause.

---

### Option 3: Kill Long-Running Queries

**When to Use**: If specific queries are blocking connections

```sql
-- Identify problematic queries
SELECT 
    pid,
    now() - query_start as duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '10 minutes'
ORDER BY duration DESC
LIMIT 10;

-- Terminate specific query (use with caution)
SELECT pg_terminate_backend(pid);
```

**Caution**: Only terminate queries after confirming they're safe to kill

---

### Option 4: Restart Application Services

**When to Use**: If connection leak is confirmed but rollback not possible

```bash
# Force new deployment to restart all tasks
aws ecs update-service \
  --cluster production \
  --service api-gateway \
  --force-new-deployment

# Monitor task health
aws ecs describe-services --cluster production --services api-gateway \
  --query 'services[0].deployments'
```

---

## Verification Steps

### 1. Confirm Connection Count Normalized
```bash
# Should return to normal range (50-150)
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=prod-db-primary \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

### 2. Verify API Response Times
```bash
# Check ALB target response time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average
```

**Expected**: <500ms average response time

### 3. Check Error Rates
```bash
# Should be <1% error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/prod-alb/abc123 \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum
```

### 4. User Impact Assessment
- Check customer support tickets
- Review social media mentions
- Confirm no ongoing user complaints

---

## Post-Incident Actions

### 1. Update Status Page
```
Status: Resolved
Message: "Database connectivity issue has been resolved. All services operating normally. 
We apologize for any inconvenience."
```

### 2. Internal Communication
- Post resolution summary in war room channel
- Thank team members for quick response
- Schedule post-mortem meeting (within 48 hours)

### 3. Documentation
- Update incident log with timeline
- Document root cause and resolution
- Add lessons learned to runbook

### 4. Preventive Measures
- [ ] Add connection pool monitoring alerts
- [ ] Implement connection leak detection
- [ ] Review code for proper connection cleanup
- [ ] Add automated connection pool scaling
- [ ] Improve deployment testing procedures

---

## Escalation Path

**Level 1**: On-call Database SRE (0-15 minutes)  
**Level 2**: Database Team Lead (15-30 minutes)  
**Level 3**: VP Engineering (30-60 minutes)  
**Level 4**: CTO (>60 minutes or customer-facing impact)

---

## Related Documentation

- [Database Performance Optimization Guide](link)
- [Connection Pool Configuration Best Practices](link)
- [RDS Monitoring and Alerting](link)
- [Production Incident Response Playbook](link)

---

**Document Owner**: Database SRE Team  
**Last Updated**: October 2025  
**Review Frequency**: Quarterly  
**Emergency Contact**: database-oncall@acmecorp.com
