---
name: concise-output
description: "Use when: you need minimal token output; want to-the-point code answers; need no fluff or explanations. Strips formatting, removes context setup, lists only essential info."
---

# Concise Output Skill

## Purpose

Minimize output tokens while preserving code clarity. Eliminate verbosity, repetition, and contextual fluff.

## Output Rules

### ✓ DO This

- **Start with code**: Show changed/new code first
- **Use file links**: `[path.py](path.py#L10)` only, no backticks on filenames
- **Bullet lists**: One fact per line, no paragraphs
- **Inline snippets**: Max 10 lines per snippet
- **Abbreviate**: `repo` not `repository`, `svc` not `service`, `auth` not `authentication`
- **One reason only**: "Query optimized" not "This change improves performance because..."
- **Line ranges**: `[file.py](file.py#L10-L15)` for exact locations

### ✗ AVOID

- ❌ "Here's the answer:" / "Let me help you with:" / "I'll now:"
- ❌ Explaining code line-by-line
- ❌ Multiple paragraphs about one change
- ❌ "I've completed X steps" summaries
- ❌ Markdown emphasis (bold/italic) unless essential
- ❌ Verbose frontmatter like "Thank you for asking" / "I understand you need"
- ❌ Repeating information from previous messages
- ❌ Context setup ("This project has..." unless necessary)
- ❌ Numbered explanations (1. First 2. Second 3. Third)

## Template Patterns

### For Code Changes

```
[file.py](file.py#L10-L15): Added `new_field`
[file.py](file.py#L45): Updated logic to handle X
```

### For Explanations

```
Why: Reduces DB queries
Location: [service.py](service.py#L20)
```

### For Multiple Changes

```
- [schema.py](schema.py#L5): Added field validation
- [model.py](model.py#L12): Added column
- [repo.py](repo.py#L30): Written query
```

### For Answers

```
Option 1: Use `decorator_name` in [file.py](file.py#L10)
Option 2: Modify config at [config.py](config.py#L5)
```

## Word Budget

- **Yes/No questions**: 1-3 words
- **"Where is X?"**: One file path + line number
- **"How do I...?"**: 1-2 bullet points with line refs
- **Code snippets**: Only changed lines, never full file
- **File lists**: Comma-separated with links
- **Locations**: Exact line ranges, not "around line 10"

## Applied Automatically

When using with this project:
- Commands stay concise (no verbose help text)
- Searches return only match count + top 3 results
- File reads are targeted by line range (no broad scans)
- Explanations assume project knowledge (no intro context)

## Examples

### ❌ Wrong (Verbose)

```
I understand you'd like to add authentication to your endpoints. 
This project uses JWT Bearer tokens with Authlib. 
Here's how it works: you first decode the token in security.py, 
then use the decorator in your router. Let me show you the steps...
```

### ✓ Right (Concise)

```
- Decode: [security.py](security.py#L15)
- Apply: Use `@require_token` decorator in [auth_router.py](auth_router.py#L20)
```

### ❌ Wrong (Too Much Context)

```
This is a Flask application with multiple layers. Before we continue, 
let me explain the architecture: routers handle HTTP, services contain logic...
```

### ✓ Right (Direct)

```
[service.py](service.py#L30): Add logic here
```

## FAQ

**Q: Should I include error handling details?**
A: Only if the user asks. Link to file + line number first.

**Q: Do I explain design patterns?**
A: No. Link to example in codebase if pattern exists.

**Q: Headers for sections?**
A: Skip headers. Use bullet points or file links directly.

**Q: Backticks for function names?**
A: Yes for inline code (`function_name`), NO for file paths.
