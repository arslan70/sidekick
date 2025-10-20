# Meeting Notes Best Practices

## Purpose

This document outlines best practices for capturing, organizing, and distributing effective meeting notes. Well-structured meeting notes improve team alignment, accountability, and decision-making.

---

## Before the Meeting

### 1. Preparation
- **Create a Meeting Agenda**: Share 24 hours in advance
- **Identify Note-Taker**: Rotate responsibility among team members
- **Review Previous Notes**: Check action items from last meeting
- **Set Up Template**: Use standardized format for consistency

### 2. Pre-Meeting Checklist
- [ ] Meeting title and date confirmed
- [ ] Attendee list prepared
- [ ] Agenda items documented
- [ ] Previous action items reviewed
- [ ] Note-taking tool ready (Confluence, Notion, Google Docs)

---

## During the Meeting

### 3. Note-Taking Structure

```markdown
# [Meeting Title]
**Date**: YYYY-MM-DD HH:MM
**Attendees**: [List all participants]
**Facilitator**: [Name]
**Note-Taker**: [Name]

## Agenda
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]

## Discussion Points
### [Topic 1]
- [Key point discussed]
- [Question raised]
- [Answer/clarification]

## Decisions Made
- ✅ [Decision 1]
- ✅ [Decision 2]

## Action Items
- [ ] [Task] - Assigned to [Name] - Due: [Date]
- [ ] [Task] - Assigned to [Name] - Due: [Date]

## Next Steps
- [What happens next]

## Parking Lot
- [Topics to discuss later]
```

### 4. Active Listening Techniques
- **Focus on Key Points**: Don't transcribe verbatim
- **Capture Decisions**: Mark clearly with ✅ or **DECISION:**
- **Note Action Items**: Include owner and due date
- **Record Blockers**: Document impediments immediately
- **Use Abbreviations**: Save time (AI = Action Item, FYI = For Your Information)

### 5. What to Capture
✅ **Include:**
- Key decisions and rationale
- Action items with owners
- Important questions and answers
- Deadlines and milestones
- Disagreements and resolutions
- Next meeting date/time

❌ **Exclude:**
- Off-topic discussions
- Personal conversations
- Redundant information
- Overly detailed technical specs (link to docs instead)

---

## After the Meeting

### 6. Note Finalization (within 2 hours)
1. **Clean up and format**: Make notes readable
2. **Highlight action items**: Use bold or color coding
3. **Tag participants**: Notify assignees of their tasks
4. **Add links**: Reference related documents/tickets
5. **Spell check**: Ensure professionalism

### 7. Distribution
- **Primary Channel**: Post in team Slack/Teams channel
- **Email Summary**: Send to all attendees + stakeholders
- **Knowledge Base**: Archive in Confluence/SharePoint
- **Calendar Update**: Add to meeting series description

### 8. Follow-Up Actions
- Create Jira tickets for action items
- Set reminders for upcoming deadlines
- Schedule follow-up meetings if needed
- Update project status dashboard

---

## Meeting Types & Specific Practices

### Daily Standups (15 minutes)
**Format**:
- What I did yesterday
- What I'm doing today
- Blockers

**Best Practice**: Keep notes minimal, focus on blockers and action items only.

### Sprint Planning (2 hours)
**Format**:
- Sprint goal
- Stories committed
- Capacity planning
- Risk identification

**Best Practice**: Link all Jira tickets, capture team velocity, record assumptions.

### Retrospectives (1 hour)
**Format**:
- What went well
- What needs improvement
- Action items for next sprint

**Best Practice**: Be honest but constructive, focus on process not people.

### Executive Reviews (1-2 hours)
**Format**:
- Executive summary (3 bullet points)
- Detailed findings
- Recommendations
- Next steps

**Best Practice**: Use data visualization, keep language business-focused.

---

## Common Pitfalls to Avoid

1. **Too Much Detail**: Don't transcribe every word
2. **Missing Action Items**: Always assign owner and due date
3. **Late Distribution**: Send within 2 hours of meeting
4. **No Follow-Up**: Track action item completion
5. **Unclear Decisions**: Mark decisions explicitly
6. **Poor Formatting**: Use headings, bullets, and whitespace
7. **No Links**: Connect to related Jira tickets and documents

---

## Templates for Different Meetings

### Template 1: Technical Design Review
```markdown
# Technical Design Review - [Feature Name]

**Participants**: [List]
**Date**: [YYYY-MM-DD]

## Design Overview
- [Summary of proposed design]

## Technical Discussion
- [Key points raised]
- [Alternative approaches considered]

## Security Considerations
- [Security review findings]

## Performance Impact
- [Expected performance characteristics]

## Decisions
- ✅ [Architecture decision 1]
- ✅ [Technology choice]

## Action Items
- [ ] [Update design doc] - @engineer - Due: [date]
- [ ] [Create POC] - @engineer - Due: [date]
```

### Template 2: Client Meeting
```markdown
# Client Meeting - [Client Name]

**Participants**: [Internal team], [Client team]
**Date**: [YYYY-MM-DD]

## Meeting Objectives
- [Objective 1]
- [Objective 2]

## Discussion Summary
- [Key topics discussed]

## Client Feedback
- [Feedback point 1]
- [Feedback point 2]

## Next Steps
- [ ] [Follow-up action] - @sales - Due: [date]
- [ ] [Send proposal] - @presales - Due: [date]

## Follow-up Meeting
- Scheduled for: [date/time]
```

---

## Tools & Automation

### Recommended Tools
- **Confluence**: Enterprise knowledge base
- **Notion**: Flexible documentation
- **Google Docs**: Real-time collaboration
- **Microsoft OneNote**: Integrated with Teams
- **Roam Research**: Networked note-taking

### AI-Powered Assistants
- **Otter.ai**: Auto-transcription
- **Fireflies.ai**: Meeting recording and summary
- **Grain**: Video highlights and clips
- **Fathom**: AI meeting notes

### Integration Tips
- Link notes to Jira for action items
- Connect to Slack for distribution
- Sync with Google Calendar for scheduling
- Use Zapier for automation workflows

---

## Metrics for Success

Track these KPIs to improve meeting effectiveness:
- **Action Item Completion Rate**: Target >90%
- **Note Distribution Time**: Target <2 hours
- **Meeting Duration vs Scheduled**: Target ±10%
- **Participant Satisfaction**: Quarterly survey >4/5 stars

---

**Document Owner**: Product Team  
**Last Updated**: October 2025  
**Review Frequency**: Quarterly
