# [Project Name] - Project Portfolio

## Elevator Pitch
[2-3 sentences: What it does, who it's for, why it matters. This should be your "cocktail party" explanation.]

## Context & Problem
[Describe the situation that led to this project. What problem exists? Who experiences it? Why does it matter? What are the consequences of not solving it?]

## Solution & Approach
[Describe your solution at a high level. What's your approach? What makes it different? What are the key design principles?]

## Technical Implementation

### Architecture
[Describe the system architecture. What are the main components? How do they interact? What patterns did you use?]

### Technology Stack
- **Core**: [Languages, frameworks, libraries]
- **Data**: [Databases, storage, formats]
- **Infrastructure**: [Hosting, deployment, services]
- **Testing**: [Test frameworks, coverage tools]
- **Other**: [Notable tools, integrations]

### Key Design Decisions
1. **[Decision 1]**: [Why you made this choice, what alternatives you considered]
2. **[Decision 2]**: [Trade-offs, constraints, benefits]
3. **[Decision 3]**: [Impact on architecture, maintenance, or scalability]
[Add more as needed]

## Key Features
- **[Feature 1]**: [Brief description]
- **[Feature 2]**: [Brief description]
- **[Feature 3]**: [Brief description]
[List 5-10 most important features]

## Outcomes & Metrics
[Quantifiable results: time saved, performance improvements, user adoption, business impact, code quality improvements, team productivity gains, etc.]

## Technical Challenges & Solutions

### Challenge 1: [Challenge Name]
**Problem**: [What was the technical challenge?]
**Solution**: [How did you solve it? What was the approach?]

### Challenge 2: [Challenge Name]
**Problem**: [What was the technical challenge?]
**Solution**: [How did you solve it? What was the approach?]

[Add 3-5 significant challenges that show problem-solving skills]

## Learnings & Growth
[What did you learn from this project? What would you do differently? What skills did you develop? What surprised you?]

## Future Enhancements
[What would you add if you had more time? What are the next logical steps? What feedback have you received?]

## Project Links
- **Repository**: [GitHub/GitLab link]
- **Live Demo**: [Production URL if applicable]
- **Documentation**: [Link to docs]
- **Related Projects**: [Links to related work]

## Tags
`tag1` `tag2` `tag3` [Add relevant technology and domain tags for searchability]

## Portfolio Use Cases
- **Resume Project Description**: Use "Elevator Pitch" + "Outcomes & Metrics" + "Technology Stack"
- **Technical Interview**: Reference "Technical Challenges & Solutions" for system design discussions
- **Portfolio Website**: Use "Context & Problem" + "Solution & Approach" + "Key Features"
- **LinkedIn Project**: Use "Elevator Pitch" + subset of "Key Features" + "Tags"
- **GitHub Profile**: Link to this PROJECT.md with "Elevator Pitch" as preview text

---

## Template Notes (Delete this section after filling out)

**How to use this template:**
1. Copy this file to your project root as `PROJECT.md`
2. Fill out each section - aim for clarity over length
3. Update as the project evolves (quarterly reviews work well)
4. Use "Portfolio Use Cases" to extract content for specific contexts
5. Keep technical depth balanced - enough to show expertise, not overwhelming

**Section guidance:**
- **Elevator Pitch**: Test by reading aloud - should be conversational
- **Context & Problem**: Show you understand the domain and user needs
- **Technical Implementation**: Demonstrate architectural thinking and technology choices
- **Challenges & Solutions**: Pick challenges that show growth and problem-solving
- **Outcomes & Metrics**: Use numbers whenever possible - even rough estimates help
- **Tags**: Think about keywords recruiters search for

**Quick extraction commands:**
```bash
# Resume format (plain text)
grep -A 3 "## Elevator Pitch" PROJECT.md | tail -n 1

# Get all technical tags
grep -o '\`[^`]*\`' PROJECT.md | sort -u

# Extract outcomes only
sed -n '/## Outcomes & Metrics/,/## /p' PROJECT.md
```
