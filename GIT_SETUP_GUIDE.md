# Git Setup and GitHub Push Guide

## Overview
This guide will walk you through initializing a git repository for the HR Recruiter AI Agent and pushing it to GitHub.

## Prerequisites Checklist
- ✅ All code improvements completed
- ✅ Code tested and working
- ✅ README.md created
- ✅ .gitignore created
- ✅ Documentation complete (CODE_REVIEW.md, IMPROVEMENTS.md)
- ✅ .env file exists (will be excluded from git)

## Step 1: Verify Your Files

Before initializing git, let's verify what will be included:

### Files to be Committed:
- ✅ hr_agent.py (main script)
- ✅ requirements.txt
- ✅ mcp.json (MCP configuration)
- ✅ README.md
- ✅ CODE_REVIEW.md
- ✅ IMPROVEMENTS.md
- ✅ MasterPrompt
- ✅ .gitignore
- ✅ job_descriptions/*.txt
- ✅ resumes/*.txt
- ✅ results/.gitkeep
- ✅ test_*.py files

### Files to be Excluded (via .gitignore):
- ❌ .env (API keys - NEVER commit this!)
- ❌ __pycache__/
- ❌ *.pyc
- ❌ results/*.md (generated reports)
- ❌ .vscode/

## Step 2: Initialize Git Repository

Open PowerShell in your project directory and run:

```powershell
# Navigate to project directory (if not already there)
cd C:\Maruthu\Projects\Recruiter_Agent

# Initialize git repository
git init

# Check git status
git status
```

**Expected Output:**
```
Initialized empty Git repository in C:/Maruthu/Projects/Recruiter_Agent/.git/
```

## Step 3: Configure Git (First Time Only)

If this is your first time using Git on this machine:

```powershell
# Set your name (replace with your name)
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list
```

## Step 4: Stage All Files

```powershell
# Add all files to staging area
git add .

# Check what's been staged
git status
```

**Expected Output:**
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   CODE_REVIEW.md
        new file:   IMPROVEMENTS.md
        new file:   MasterPrompt
        new file:   README.md
        new file:   hr_agent.py
        new file:   job_descriptions/software_engineer.txt
        new file:   mcp.json
        new file:   requirements.txt
        new file:   resumes/alice_johnson.txt
        new file:   resumes/bob_smith.txt
        new file:   results/.gitkeep
        new file:   test_gemini.py
        new file:   test_mcp_connection.py
        new file:   test_rank_resumes.py
```

**IMPORTANT:** Verify that `.env` is NOT in the list!

## Step 5: Create Initial Commit

```powershell
# Create your first commit
git commit -m "Initial commit: HR Recruiter AI Agent with MCP integration

- Implemented HR recruitment agent using LangChain and Google Gemini
- MCP server integration for resume ranking
- Dynamic job title extraction
- Comprehensive error handling and security features
- Complete documentation (README, CODE_REVIEW, IMPROVEMENTS)
- Production-ready with logging and type hints"

# View commit history
git log --oneline
```

## Step 6: Create GitHub Repository

### Option A: Via GitHub Website (Recommended)

1. Go to [GitHub](https://github.com)
2. Click the **"+"** icon in top-right corner
3. Select **"New repository"**
4. Fill in details:
   - **Repository name:** `recruiter-agent` (or your preferred name)
   - **Description:** "AI-powered HR recruitment agent using LangChain, Gemini API, and MCP server"
   - **Visibility:** Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

### Option B: Via GitHub CLI (if installed)

```powershell
# Create repository
gh repo create recruiter-agent --public --source=. --remote=origin

# Or for private repository
gh repo create recruiter-agent --private --source=. --remote=origin
```

## Step 7: Connect Local Repository to GitHub

After creating the GitHub repository, you'll see a URL like:
`https://github.com/yourusername/recruiter-agent.git`

```powershell
# Add remote origin (replace with YOUR repository URL)
git remote add origin https://github.com/yourusername/recruiter-agent.git

# Verify remote
git remote -v
```

**Expected Output:**
```
origin  https://github.com/yourusername/recruiter-agent.git (fetch)
origin  https://github.com/yourusername/recruiter-agent.git (push)
```

## Step 8: Push to GitHub

### Option A: Using HTTPS (Recommended for beginners)

```powershell
# Rename branch to main (if not already)
git branch -M main

# Push to GitHub
git push -u origin main
```

**First Time:** You'll be prompted to authenticate:
- A browser window may open for GitHub authentication
- Or you'll be asked for username/password
- **Note:** GitHub now requires Personal Access Token (PAT) instead of password

### Option B: Using SSH (if you have SSH keys configured)

```powershell
# Add SSH remote instead
git remote set-url origin git@github.com:yourusername/recruiter-agent.git

# Push to GitHub
git push -u origin main
```

## Step 9: Verify on GitHub

1. Go to your repository URL: `https://github.com/yourusername/recruiter-agent`
2. You should see all your files
3. Check that README.md is displayed at the bottom
4. Verify `.env` is NOT visible (it should be excluded)

## GitHub Personal Access Token Setup

If you need to create a Personal Access Token (PAT):

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "Recruiter Agent Project"
4. Set expiration (recommend 90 days)
5. Select scopes:
   - ✅ `repo` (full control of private repositories)
6. Click "Generate token"
7. **IMPORTANT:** Copy the token immediately (you won't see it again!)
8. When git asks for password, paste the token instead

## Common Issues and Solutions

### Issue 1: "fatal: not a git repository"
**Solution:**
```powershell
git init
```

### Issue 2: "fatal: remote origin already exists"
**Solution:**
```powershell
git remote remove origin
git remote add origin https://github.com/yourusername/recruiter-agent.git
```

### Issue 3: ".env file is being tracked"
**Solution:**
```powershell
# Remove from git (but keep local file)
git rm --cached .env

# Commit the removal
git commit -m "Remove .env from tracking"

# Verify .gitignore includes .env
cat .gitignore | Select-String ".env"
```

### Issue 4: "Authentication failed"
**Solution:**
- Use Personal Access Token instead of password
- Or set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Issue 5: "Updates were rejected"
**Solution:**
```powershell
# Pull first (if remote has changes)
git pull origin main --rebase

# Then push
git push origin main
```

## Future Workflow

After initial setup, your typical workflow will be:

```powershell
# 1. Make changes to your files
# ... edit code ...

# 2. Check what changed
git status
git diff

# 3. Stage changes
git add .
# Or stage specific files
git add hr_agent.py

# 4. Commit changes
git commit -m "Descriptive commit message"

# 5. Push to GitHub
git push
```

## Useful Git Commands

```powershell
# View status
git status

# View commit history
git log --oneline --graph

# View changes
git diff

# View remote URL
git remote -v

# Create a new branch
git checkout -b feature-name

# Switch branches
git checkout main

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo changes to a file
git checkout -- filename.py

# View file in specific commit
git show commit-hash:filename.py
```

## Best Practices

1. **Commit Often:** Make small, focused commits
2. **Descriptive Messages:** Write clear commit messages
3. **Never Commit Secrets:** Always check .gitignore includes .env
4. **Pull Before Push:** If collaborating, pull changes first
5. **Use Branches:** Create branches for new features
6. **Review Changes:** Use `git diff` before committing

## Next Steps

After pushing to GitHub:

1. ✅ Add repository description and topics on GitHub
2. ✅ Add a license file (if desired)
3. ✅ Enable GitHub Issues for bug tracking
4. ✅ Set up branch protection rules
5. ✅ Consider adding GitHub Actions for CI/CD
6. ✅ Share the repository URL

## Repository URL Template

After setup, your project will be available at:
```
https://github.com/yourusername/recruiter-agent
```

Share this URL to collaborate or showcase your work!

---

## Quick Reference Card

```powershell
# One-time setup
git init
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Initial commit
git add .
git commit -m "Initial commit: HR Recruiter AI Agent"

# Connect to GitHub
git remote add origin https://github.com/yourusername/recruiter-agent.git
git branch -M main
git push -u origin main

# Daily workflow
git status                          # Check changes
git add .                           # Stage all changes
git commit -m "Your message"        # Commit changes
git push                            # Push to GitHub
```

---

**Document Version:** 1.0  
**Last Updated:** October 13, 2025  
**Status:** Ready for execution ✅
