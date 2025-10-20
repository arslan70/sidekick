# Visual Assets Guide - SideKick AI

This document outlines the visual assets needed for the hackathon submission and provides guidance on capturing high-quality screenshots.

---

## Required Screenshots

### 1. Daily Planning Multi-Agent Orchestration

**Scenario**: User asks "Help me plan my day"

**What to Capture**:
- Chainlit chat interface showing the user query
- Agent response showing:
  - Calendar events for the day
  - Urgent emails with action items
  - JIRA tasks (blocked, in-progress, ready)
  - Overnight incidents
  - AWS infrastructure alerts
- Visible indicators of multi-agent execution (if possible)

**Screenshot Requirements**:
- Resolution: 1920x1080 (1080p) minimum
- Format: PNG (lossless)
- Filename: `01-daily-planning-orchestration.png`
- Location: `docs/screenshots/`

**Key Elements to Highlight**:
- Clean, professional UI
- Comprehensive information aggregation
- Clear, actionable output
- Multiple data sources integrated

---

### 2. JIRA Integration with OAuth

**Scenario**: User asks "What are my JIRA tasks?" (with OAuth configured)

**What to Capture**:
- Chainlit interface showing JIRA query
- Agent response with real JIRA data:
  - Issue keys (PROJ-123, etc.)
  - Issue summaries
  - Status, priority, assignee
  - Links to JIRA issues
- OAuth authentication indicator (if visible)

**Screenshot Requirements**:
- Resolution: 1920x1080 minimum
- Format: PNG
- Filename: `02-jira-oauth-integration.png`
- Location: `docs/screenshots/`

**Key Elements to Highlight**:
- Real JIRA data (not static demo data)
- Professional formatting
- Actionable information
- OAuth security

**Alternative** (if OAuth not configured):
- Capture OAuth login flow
- Show authorization screen
- Demonstrate secure token handling

---

### 3. AWS Monitoring (Read-Only Safety Demo)

**Scenario**: User asks "What's our AWS infrastructure status?" followed by "Delete S3 bucket"

**What to Capture**:
- **Part A**: Successful read-only query
  - List of EC2 instances, S3 buckets, or Lambda functions
  - CloudWatch alarms or cost data
  - Professional formatting

- **Part B**: Blocked destructive operation
  - User attempts: "Delete S3 bucket production-data"
  - Agent response: "❌ Operation blocked by read-only safety enforcement"
  - Clear explanation of why operation was blocked

**Screenshot Requirements**:
- Resolution: 1920x1080 minimum
- Format: PNG
- Filenames: 
  - `03a-aws-monitoring-readonly.png`
  - `03b-aws-safety-enforcement.png`
- Location: `docs/screenshots/`

**Key Elements to Highlight**:
- Read-only operations work perfectly
- Destructive operations clearly blocked
- Safety enforcement is automatic
- User-friendly error messages

---

### 4. Report Generation Output

**Scenario**: User asks "Generate Q3 2025 sales report"

**What to Capture**:
- Chainlit interface showing report request
- Agent response with professional report:
  - Executive summary
  - Sales data with metrics
  - Product breakdowns
  - Insights and recommendations
  - Source citations (Knowledge Base + DynamoDB)

**Screenshot Requirements**:
- Resolution: 1920x1080 minimum
- Format: PNG
- Filename: `04-report-generation-output.png`
- Location: `docs/screenshots/`

**Key Elements to Highlight**:
- Professional report formatting
- Data-driven insights
- Multi-source aggregation (KB + DynamoDB)
- Actionable recommendations

---

## Screenshot Capture Instructions

### Setup

1. **Run Application Locally**:
   ```bash
   cd app
   chainlit run app.py
   ```

2. **Configure Display**:
   - Set browser window to 1920x1080 or larger
   - Use Chrome or Firefox for best rendering
   - Zoom level: 100% (no zoom in/out)

3. **Prepare Test Data**:
   - Ensure demo data is loaded (configs/*.json)
   - Configure OAuth if capturing JIRA screenshots
   - Verify Knowledge Base is synced

### Capture Process

1. **Clear Chat History**: Start with clean slate for each screenshot

2. **Execute Scenario**: Type the exact query from scenario description

3. **Wait for Complete Response**: Ensure agent finishes before capturing

4. **Capture Screenshot**:
   - **macOS**: Cmd+Shift+4, then Space, click window
   - **Windows**: Windows+Shift+S, select area
   - **Linux**: Use Flameshot or Spectacle

5. **Verify Quality**:
   - Check resolution (1920x1080 minimum)
   - Ensure text is readable
   - No personal information visible
   - Professional appearance

6. **Save with Correct Filename**: Use naming convention from this guide

### Post-Processing (Optional)

1. **Crop if Needed**: Remove unnecessary browser chrome

2. **Add Annotations** (if helpful):
   - Arrows pointing to key features
   - Text labels for important elements
   - Use red (#FF0000) for highlights

3. **Optimize File Size**:
   - Use PNG compression (pngquant, TinyPNG)
   - Target: <500KB per image
   - Maintain visual quality

---

## Architecture Diagrams

### Existing Diagrams (Already in README)

✅ **Agent Hierarchy Diagram** (PlantUML)
- Shows Orchestrator + 7 Workers
- Agents-as-Tools pattern
- Data flow and dependencies

✅ **AWS Services Architecture** (Mermaid in AWS_SERVICES.md)
- All 11 AWS services
- Service connections
- Data flow

### Additional Diagrams Needed

**1. Deployment Architecture**
- Already exists in AWS_SERVICES.md
- Shows ECS Fargate + AgentCore + AWS services

**2. OAuth Flow Diagram** (Optional)
- User → Chainlit → Atlassian → Token Storage
- Could be added to oauth documentation

---

## Screenshot Checklist

Before submitting, verify:

- [ ] All 4 required screenshots captured
- [ ] Resolution: 1920x1080 minimum
- [ ] Format: PNG (lossless)
- [ ] Filenames follow naming convention
- [ ] Saved in `docs/screenshots/` directory
- [ ] No personal information visible
- [ ] Professional appearance (clean UI, no errors)
- [ ] Text is readable at full size
- [ ] File sizes optimized (<500KB each)
- [ ] Screenshots referenced in documentation

---

## Using Screenshots in Documentation

### In README.md

```markdown
## Screenshots

### Daily Planning Multi-Agent Orchestration
![Daily Planning](docs/screenshots/01-daily-planning-orchestration.png)
*SideKick AI aggregates information from 5+ sources to create comprehensive daily briefing*

### JIRA Integration with OAuth
![JIRA Integration](docs/screenshots/02-jira-oauth-integration.png)
*Secure OAuth 2.0 integration with Atlassian JIRA for real-time task management*

### AWS Monitoring with Read-Only Safety
![AWS Monitoring](docs/screenshots/03a-aws-monitoring-readonly.png)
*Read-only AWS infrastructure monitoring for safe analysis*

![Safety Enforcement](docs/screenshots/03b-aws-safety-enforcement.png)
*Automatic blocking of destructive operations for production safety*

### Report Generation
![Report Generation](docs/screenshots/04-report-generation-output.png)
*Professional reports combining Knowledge Base templates with live DynamoDB data*
```

### In HACKATHON.md

Add screenshots to relevant sections:
- "What It Does" → Daily planning screenshot
- "How We Built It" → Architecture diagram
- "Accomplishments" → All feature screenshots

### In Devpost Submission

Upload all 4 screenshots to Devpost gallery with captions:
1. "Multi-agent orchestration for daily planning"
2. "Secure JIRA integration with OAuth 2.0"
3. "Read-only AWS monitoring with safety enforcement"
4. "Intelligent report generation from multiple sources"

---

## Demo Video Thumbnails

### Requirements

- **Resolution**: 1280x720 (720p) minimum
- **Format**: JPG or PNG
- **Aspect Ratio**: 16:9
- **File Size**: <2MB

### Design Elements

- SideKick AI logo (if created)
- Compelling text: "Hierarchical Multi-Agent AI Assistant"
- AWS Bedrock branding
- Professional color scheme (AWS orange #FF9900)
- High contrast for readability

### Tools

- **Canva**: Easy online design tool
- **Figma**: Professional design tool
- **Photoshop**: Advanced editing
- **GIMP**: Free alternative to Photoshop

---

## Social Media Assets (Optional)

### Twitter/X Card

- **Resolution**: 1200x675
- **Format**: PNG or JPG
- **Content**: Project overview + key features

### LinkedIn Post Image

- **Resolution**: 1200x627
- **Format**: PNG or JPG
- **Content**: Professional presentation of innovation

### GitHub Social Preview

- **Resolution**: 1280x640
- **Format**: PNG or JPG
- **Content**: Repository branding and tagline

---

## Next Steps

1. **Capture Screenshots**: Follow instructions above to capture all 4 required screenshots
2. **Create Directory**: `mkdir -p docs/screenshots`
3. **Save Screenshots**: Use correct filenames and location
4. **Update Documentation**: Add screenshot references to README and HACKATHON.md
5. **Verify Quality**: Review all screenshots for professionalism
6. **Optimize Files**: Compress if needed to reduce file sizes
7. **Commit to Git**: `git add docs/screenshots/ && git commit -m "Add hackathon screenshots"`

---

## Questions?

If you need help with:
- **Screenshot capture**: See "Capture Process" section above
- **Image editing**: Use tools listed in "Post-Processing" section
- **File optimization**: Use pngquant or TinyPNG online
- **Documentation updates**: See "Using Screenshots in Documentation" section
