# Contributing to SAR SaaS

Thank you for your interest in contributing! This guide explains our commit message conventions.

## Commit Message Format

We follow **conventional commits** to keep our commit history clear and structured. Our automated versioning system uses commit messages to determine version bumps.

### Structure

```
<type>(<scope>): <subject>
```

### Type

Must be one of:

- **feat**: A new feature
- **fix**: A bug fix
- **BREAKING CHANGE**: A breaking change (add to commit body)

### Scope (Optional)

What part of the codebase is affected:

- `parser` - SAR file parsing
- `stats` - Statistics calculation
- `backend` - Backend API
- `frontend` - Frontend
- `docker` - Docker/containers

### Subject

- Use imperative mood ("add feature" not "added feature")
- No capital first letter
- No period at the end
- Max 50 characters

## Examples

### Feature

```
feat(parser): add cpu metrics parsing
```

### Bug Fix

```
fix(stats): handle empty values correctly
```

### Breaking Change

```
feat(api): change response format

BREAKING CHANGE: Response format changed from flat array to grouped structure
```

## Versioning Impact

| Commit Type | Version Bump |
|------------|-----------------|
| `fix:` | Patch (0.1.0 → 0.1.1) |
| `feat:` | Minor (0.1.0 → 0.2.0) |
| `BREAKING CHANGE` | Major (0.1.0 → 1.0.0) |
