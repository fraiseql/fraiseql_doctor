# Claude Commands for FraiseQL Doctor Project
**Quick commands for project management and idea capture**

## 💡 **Idea Management Commands**

### **Save Idea to Roadmap**
```
@claude save idea: [YOUR_IDEA_DESCRIPTION]
```

**Examples:**
```bash
@claude save idea: GraphQL query caching with Redis integration for faster response times

@claude save idea: Slack bot for natural language monitoring queries like "show me endpoint health"

@claude save idea: Visual schema diff tool to compare GraphQL schema versions side-by-side

@claude save idea: Auto-generate test queries from GraphQL schema for endpoint validation
```

### **Add Feature Request**
```
@claude add feature: [FEATURE_NAME] - [DESCRIPTION] - [PRIORITY: high/medium/low]
```

**Examples:**
```bash
@claude add feature: Dark Mode - User preference for dark/light theme toggle - Priority: medium

@claude add feature: Export Dashboard Data - CSV/JSON export of health metrics - Priority: low

@claude add feature: Query Templates - Pre-built query templates for common use cases - Priority: high
```

### **Save User Feedback**
```
@claude save feedback: [USER_TYPE] said "[FEEDBACK]" - [CONTEXT]
```

**Examples:**
```bash
@claude save feedback: DevOps Engineer said "Need better alerting for weekends" - During user interview

@claude save feedback: Frontend Developer said "GraphQL playground needs autocomplete" - Beta testing session
```

### **Add Research Question**
```
@claude research question: [QUESTION] - [CONTEXT/WHY]
```

**Examples:**
```bash
@claude research question: Do users prefer email or Slack for alerts? - For notification strategy

@claude research question: What's the ideal refresh rate for real-time dashboards? - Performance vs utility
```

---

## 🐛 **Development Commands**

### **Log Technical Debt**
```
@claude tech debt: [COMPONENT] - [ISSUE] - [IMPACT]
```

**Examples:**
```bash
@claude tech debt: Authentication - Mock provider needs more realistic behavior - Testing accuracy

@claude tech debt: Dashboard - Large bundle size from chart library - Performance impact
```

### **Architecture Decision**
```
@claude architecture: [DECISION] - [RATIONALE] - [ALTERNATIVES_CONSIDERED]
```

**Examples:**
```bash
@claude architecture: Using Pinia over Vuex - Better TypeScript support and simpler API - Considered Vuex 4

@claude architecture: WebSockets for real-time updates - Low latency requirement - Considered polling
```

---

## 📊 **Project Tracking Commands**

### **Update Progress**
```
@claude progress: [FEATURE/PHASE] - [STATUS] - [BLOCKERS/NOTES]
```

**Examples:**
```bash
@claude progress: Dashboard Layout - 80% complete - Waiting on user menu design

@claude progress: Auth0 Integration - Completed - All tests passing, ready for review
```

### **Add Lesson Learned**
```
@claude lesson: [WHAT_LEARNED] - [CONTEXT] - [APPLY_TO_FUTURE]
```

**Examples:**
```bash
@claude lesson: Bundle size exploded with full Chart.js - Phase 2.5 development - Use tree-shaking aggressively

@claude lesson: Users confused by technical error messages - User testing - Add user-friendly error translations
```

---

## 🤝 **Integration Commands**

### **Save Integration Idea**
```
@claude integration: [SERVICE/TOOL] - [USE_CASE] - [PRIORITY]
```

**Examples:**
```bash
@claude integration: GitHub Actions - Automated GraphQL schema validation in PRs - High priority

@claude integration: DataDog - Correlation with existing APM metrics - Medium priority
```

### **Competitive Intelligence**
```
@claude competitor: [COMPETITOR] - [FEATURE] - [OUR_RESPONSE]
```

**Examples:**
```bash
@claude competitor: Apollo Studio - Added federation monitoring - We should prioritize federation features

@claude competitor: Postman - GraphQL collection sharing - Consider query marketplace feature
```

---

## 🎯 **How Claude Should Handle These Commands**

When you see a command like `@claude save idea:`, Claude should:

1. **Acknowledge** the command immediately
2. **Add the idea** to the appropriate section in ROADMAP.md
3. **Auto-categorize** based on keywords (auth, monitoring, UI, integration, etc.)
4. **Add timestamp** and context
5. **Suggest priority** based on similar existing items
6. **Confirm** the idea was saved with a brief summary

### **Command Processing Example**

**User Input:**
```
@claude save idea: Real-time collaborative query editing like Google Docs for teams working on complex GraphQL queries
```

**Claude Response:**
```
✅ Idea saved to roadmap!

📍 **Location**: ROADMAP.md > User Experience & Collaboration > Brainstorming Section
🏷️ **Auto-categorized**: User Experience, Collaboration Tools
⏰ **Added**: 2025-01-21 14:30
🎯 **Suggested Priority**: Medium (collaboration features score well for team adoption)
📝 **Summary**: Real-time collaborative GraphQL query editing

The idea has been added to the "Brainstorming Section" since it's innovative but needs user validation. Similar to existing collaborative incident response features.
```

---

## 📋 **Command Reference Quick List**

| Command | Purpose | Example |
|---------|---------|---------|
| `@claude save idea:` | Add feature idea to roadmap | General feature concepts |
| `@claude add feature:` | Structured feature request | Specific features with priority |
| `@claude save feedback:` | User/stakeholder feedback | User research insights |
| `@claude research question:` | Questions to investigate | User research topics |
| `@claude tech debt:` | Technical debt tracking | Code quality issues |
| `@claude architecture:` | Architecture decisions | Design choices and rationale |
| `@claude progress:` | Development progress | Phase/feature status updates |
| `@claude lesson:` | Lessons learned | Development insights |
| `@claude integration:` | Integration opportunities | Third-party service ideas |
| `@claude competitor:` | Competitive intelligence | Market research findings |

---

## 🚀 **Advanced Usage**

### **Batch Commands**
```bash
@claude save idea: Dark mode toggle for better user experience
@claude save idea: Export health metrics as PDF reports for stakeholders
@claude save idea: Mobile push notifications for critical alerts
@claude research question: What's the optimal alert threshold to avoid false positives?
```

### **Context-Aware Commands**
```bash
# During user testing session
@claude save feedback: User said "dashboard loads too slowly" - User testing session #3

# During code review
@claude tech debt: Chart.js bundle size - 150KB impact on initial load - Review findings

# During planning meeting
@claude add feature: Query performance budgets - Set SLA thresholds per query - Priority: high
```

### **Cross-Reference Commands**
```bash
@claude save idea: Integration with existing APM tools - relates to DataDog integration idea from Q1 planning
```

---

**💡 Pro Tip**: Use these commands during development, user interviews, code reviews, and planning sessions to never lose a valuable insight!

**🎯 Goal**: Make idea capture so frictionless that you naturally use it during any project work, building a comprehensive knowledge base for FraiseQL Doctor's evolution.
