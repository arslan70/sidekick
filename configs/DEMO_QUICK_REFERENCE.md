# Demo Scenarios Quick Reference Card

## 🎯 Quick Access Prompts

### Scenario 1: Daily Briefing (30s)
```
Help me plan my day
```
**Shows**: 5 agents in parallel, multi-source aggregation, intelligent prioritization

---

### Scenario 2: Incident Resolution (30s)
```
We have a critical incident - database connection timeouts in production. Help me troubleshoot.
```
**Shows**: Multi-source info aggregation, Knowledge Base retrieval, AWS metrics (read-only)

---

### Scenario 3: Cost Optimization (45s)
```
Analyze our AWS costs and suggest optimizations
```
**Shows**: Business value analysis, $1,472/month savings, read-only safety

---

### Scenario 4: JIRA Refinement (15s)
```
Refine JIRA task ENG-123 with proper acceptance criteria
```
**Shows**: OAuth integration, AI-powered content generation, EARS format

---

### Safety Demo (10s)
```
Terminate the underutilized EC2 instances
```
**Shows**: Read-only enforcement, clear error message, safety explanation

---

## 📊 Expected Results Summary

| Scenario | Agents | Duration | Key Metric |
|----------|--------|----------|------------|
| Daily Briefing | 5 | <10s | 5 urgent items, 4 meetings |
| Incident | 4 | <15s | INC-2025-1847, 8 timeline events |
| Cost Optimization | 4 | <20s | $1,472.26 savings (34.8%) |
| JIRA Refinement | 3 | <15s | 12 acceptance criteria |
| Safety Demo | 1 | <5s | Operation blocked |

---

## ✅ Pre-Demo Checklist

- [ ] Run: `python scripts/test_demo_scenarios.py`
- [ ] All 5 tests passing
- [ ] Agents deployed and accessible
- [ ] Knowledge Base indexed
- [ ] Screen recording ready
- [ ] Audio tested

---

## 🎬 Recording Tips

1. **Start Clean**: Clear browser cache, fresh session
2. **Speak Clearly**: Explain what you're doing
3. **Show Orchestration**: Highlight parallel agent execution
4. **Emphasize Value**: "30 minutes → seconds"
5. **Demo Safety**: Show read-only enforcement

---

## 🚨 Troubleshooting

**Slow Response?**
- Check agent logs
- Verify AWS service quotas
- Test Knowledge Base retrieval

**Missing Data?**
- Verify JSON files in `configs/`
- Check Knowledge Base documents uploaded
- Validate DynamoDB table exists

**OAuth Fails?**
- Check Secrets Manager credentials
- Verify redirect URI
- Test token refresh

---

## 📈 Key Talking Points

### Innovation
- Hierarchical multi-agent architecture (Orchestrator + 7 Workers)
- Intelligent DynamoDB query construction
- Read-only AWS safety enforcement
- RAG-powered Knowledge Bases

### Business Value
- 30+ minutes saved daily
- Reports in seconds vs hours
- $1,472/month cost savings identified
- Zero risk of infrastructure changes

### AWS Services
- Amazon Bedrock (Nova Pro, Nova Lite, Guardrails)
- Bedrock Knowledge Bases (RAG)
- ECS Fargate (deployment)
- DynamoDB (structured data)
- S3 (document storage)

---

**Print this card and keep it handy during demo recording!**
