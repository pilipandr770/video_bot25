# OpenAI Assistants - Documentation Overview

This directory contains all the instruction documents and guides needed to set up the three specialized OpenAI Assistants for the AI Video Generator Bot.

## 📁 Files Created

### 1. **script-assistant-instructions.md**
Complete instructions for the Script Assistant that generates 50-second advertising scripts.

**Purpose**: Creates engaging, well-structured advertising scripts with three parts (intro, main, outro)

**Key Features**:
- 50-second duration target
- Three-part structure (15s intro, 25s main, 10s outro)
- Visual storytelling focus
- Professional advertising tone
- Clear call-to-action

**Use in OpenAI Playground**: Copy entire content into the "Instructions" field when creating the Script Assistant

---

### 2. **segment-assistant-instructions.md**
Complete instructions for the Segment Assistant that breaks scripts into segments and generates image prompts.

**Purpose**: Divides scripts into exactly 10 segments (5 seconds each) and creates detailed image generation prompts

**Key Features**:
- Precise 10-segment division
- Segment classification (intro/main/outro)
- Detailed image prompts (30-50 words each)
- JSON output format
- Cinematic visual descriptions

**Use in OpenAI Playground**: Copy entire content into the "Instructions" field when creating the Segment Assistant

---

### 3. **animation-assistant-instructions.md**
Complete instructions for the Animation Assistant that creates motion prompts for video animations.

**Purpose**: Generates detailed animation prompts to bring static images to life

**Key Features**:
- 5-second animation descriptions
- Camera movement specifications
- Motion effects and pacing
- Style consistency
- AI-animation-tool compatible

**Use in OpenAI Playground**: Copy entire content into the "Instructions" field when creating the Animation Assistant

---

### 4. **ASSISTANT_SETUP_GUIDE.md** ⭐
**START HERE** - Comprehensive step-by-step guide for setting up all three assistants.

**Contents**:
- Detailed setup instructions for each assistant
- Testing procedures and validation checklists
- Troubleshooting common issues
- Environment variable configuration
- Cost estimation
- Best practices

**This is your main reference document** - Follow this guide to create and test all three assistants.

---

### 5. **ASSISTANT_FILES_README.md** (this file)
Overview and quick reference for all assistant documentation.

---

## 🚀 Quick Start

### Step 1: Read the Setup Guide
Open `ASSISTANT_SETUP_GUIDE.md` and follow the instructions step by step.

### Step 2: Create Assistants in OpenAI Playground
For each assistant:
1. Go to https://platform.openai.com/playground
2. Create a new assistant
3. Copy the instructions from the corresponding `.md` file
4. Configure settings as specified in the setup guide
5. Save and copy the Assistant ID

### Step 3: Update Environment Variables
Add the three Assistant IDs to your `.env` file:
```bash
OPENAI_SCRIPT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_SEGMENT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_ANIMATION_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
```

### Step 4: Test Each Assistant
Follow the testing procedures in `ASSISTANT_SETUP_GUIDE.md` to verify each assistant works correctly.

---

## 📋 Checklist

Use this checklist to track your progress:

- [ ] Read `ASSISTANT_SETUP_GUIDE.md` completely
- [ ] Create Script Assistant in OpenAI Playground
  - [ ] Copy instructions from `script-assistant-instructions.md`
  - [ ] Configure with gpt-4o model, temperature 0.7
  - [ ] Save and copy Assistant ID
  - [ ] Test with sample prompt
  - [ ] Validate output format
- [ ] Create Segment Assistant in OpenAI Playground
  - [ ] Copy instructions from `segment-assistant-instructions.md`
  - [ ] Configure with gpt-4o model, temperature 0.5
  - [ ] Enable JSON response format
  - [ ] Save and copy Assistant ID
  - [ ] Test with sample script
  - [ ] Validate JSON output with 10 segments
- [ ] Create Animation Assistant in OpenAI Playground
  - [ ] Copy instructions from `animation-assistant-instructions.md`
  - [ ] Configure with gpt-4o model, temperature 0.6
  - [ ] Save and copy Assistant ID
  - [ ] Test with sample segment
  - [ ] Validate animation prompt quality
- [ ] Update `.env` file with all three Assistant IDs
- [ ] Perform end-to-end workflow test
- [ ] Document any custom adjustments made

---

## 🔧 Configuration Summary

| Assistant | File | Model | Temp | Response Format |
|-----------|------|-------|------|-----------------|
| Script | `script-assistant-instructions.md` | gpt-4o | 0.7 | Text |
| Segment | `segment-assistant-instructions.md` | gpt-4o | 0.5 | JSON |
| Animation | `animation-assistant-instructions.md` | gpt-4o | 0.6 | Text |

---

## 📖 Additional Resources

### OpenAI Documentation
- Assistants API: https://platform.openai.com/docs/assistants/overview
- Playground: https://platform.openai.com/playground
- API Keys: https://platform.openai.com/api-keys

### Project Documentation
- Main Requirements: `requirements.md`
- System Design: `design.md`
- Implementation Tasks: `tasks.md`

---

## 💡 Tips

1. **Save Your Work**: Keep a backup of your Assistant IDs in a secure location
2. **Test Thoroughly**: Test each assistant individually before integration
3. **Monitor Costs**: Keep an eye on token usage in the OpenAI dashboard
4. **Iterate**: You can update assistant instructions at any time if needed
5. **Version Control**: Document any changes you make to the instructions

---

## ❓ Need Help?

If you encounter issues:

1. Check the **Troubleshooting** section in `ASSISTANT_SETUP_GUIDE.md`
2. Verify your API key has sufficient credits
3. Ensure you're using gpt-4o or gpt-4-turbo-preview models
4. Review the validation checklists for expected outputs
5. Test with the provided example prompts first

---

## ✅ Next Steps After Setup

Once all three assistants are created and tested:

1. Verify all Assistant IDs are in your `.env` file
2. Update `app/config.py` if needed to load the new environment variables
3. Test the integration in your application code
4. Proceed with the remaining implementation tasks
5. Mark task 23 as complete in `tasks.md`

---

## 📝 Notes

- These instructions are optimized for the 10-segment, 50-second video format (test version)
- The instructions can be scaled to 48 segments for the full 4-minute version later
- All three assistants are designed to work together as a pipeline
- The output from one assistant feeds into the next in the workflow

---

**Last Updated**: Task 23 Implementation
**Status**: Ready for assistant creation and testing
