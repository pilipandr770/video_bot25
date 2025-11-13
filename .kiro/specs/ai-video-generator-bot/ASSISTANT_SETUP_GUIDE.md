# OpenAI Assistants Setup Guide

This guide walks you through creating three specialized OpenAI Assistants for the AI Video Generator Bot.

## Overview

You need to create three assistants in the OpenAI Playground:
1. **Script Assistant** - Generates 50-second advertising scripts
2. **Segment Assistant** - Breaks scripts into 10 segments with image prompts
3. **Animation Assistant** - Creates animation prompts for video segments

## Prerequisites

- OpenAI account with API access
- Access to OpenAI Playground (https://platform.openai.com/playground)
- API credits for testing

## Step-by-Step Setup

### 1. Script Assistant

#### Create the Assistant

1. Go to https://platform.openai.com/playground
2. Click on "Assistants" in the left sidebar
3. Click "Create Assistant" or "+ New Assistant"
4. Configure the assistant:

**Name**: `Video Script Generator`

**Model**: `gpt-4-turbo-preview` or `gpt-4o` (recommended for best results)

**Instructions**: Copy the entire content from `script-assistant-instructions.md`

**Tools**: None required (no code interpreter, retrieval, or functions needed)

**Temperature**: `0.7` (balanced creativity and consistency)

**Top P**: `1.0` (default)

5. Click "Save"
6. **Copy the Assistant ID** (format: `asst_xxxxxxxxxxxxxxxxxxxxx`)

#### Test the Script Assistant

In the Playground, send a test message:

```
Create a 50-second advertising script for a new eco-friendly water bottle that keeps drinks cold for 48 hours and is made from 100% recycled materials.
```

**Expected Output**: A well-structured script with three sections (Introduction, Main Content, Conclusion) totaling approximately 50 seconds of narration.

**Validation Checklist**:
- ✅ Script has three clear sections
- ✅ Introduction is ~15 seconds
- ✅ Main content is ~25 seconds
- ✅ Conclusion is ~10 seconds
- ✅ Language is visual and engaging
- ✅ Includes clear call to action

---

### 2. Segment Assistant

#### Create the Assistant

1. In OpenAI Playground, create a new assistant
2. Configure:

**Name**: `Script Segmentation & Image Prompts`

**Model**: `gpt-4-turbo-preview` or `gpt-4o`

**Instructions**: Copy the entire content from `segment-assistant-instructions.md`

**Tools**: None required

**Temperature**: `0.5` (more consistent for structured output)

**Top P**: `1.0`

**Response Format**: Set to `JSON` if available in the interface

3. Click "Save"
4. **Copy the Assistant ID**

#### Test the Segment Assistant

Use the output from your Script Assistant test as input:

```
Please segment this script:

[INTRODUCTION - 15 seconds]
[Paste the introduction from your test script]

[MAIN CONTENT - 25 seconds]
[Paste the main content from your test script]

[CONCLUSION - 10 seconds]
[Paste the conclusion from your test script]
```

**Expected Output**: A JSON object with exactly 10 segments, each containing:
- index (1-10)
- type (intro/main/outro)
- start_time and end_time
- text (script portion)
- image_prompt (detailed visual description)

**Validation Checklist**:
- ✅ Exactly 10 segments returned
- ✅ Valid JSON format
- ✅ Segments 1-3 are type "intro"
- ✅ Segments 4-7 are type "main"
- ✅ Segments 8-10 are type "outro"
- ✅ Each segment is 5 seconds (start_time to end_time)
- ✅ Image prompts are detailed (30-50 words)
- ✅ Text is evenly distributed

---

### 3. Animation Assistant

#### Create the Assistant

1. In OpenAI Playground, create a new assistant
2. Configure:

**Name**: `Video Animation Prompts`

**Model**: `gpt-4-turbo-preview` or `gpt-4o`

**Instructions**: Copy the entire content from `animation-assistant-instructions.md`

**Tools**: None required

**Temperature**: `0.6` (balanced for creative but consistent animations)

**Top P**: `1.0`

3. Click "Save"
4. **Copy the Assistant ID**

#### Test the Animation Assistant

Use one segment from your Segment Assistant test:

```
Create an animation prompt for this segment:

Segment: 4
Type: main
Text: "Introducing the EcoFlow bottle - keeps your drinks ice cold for 48 hours"
Image: "Hero shot of sleek eco-friendly water bottle floating in space, dramatic studio lighting with green and blue accents, condensation droplets on surface, premium sustainable materials visible, professional product photography style"
```

**Expected Output**: A single animation prompt (25-40 words) describing motion, camera work, and effects.

**Validation Checklist**:
- ✅ Prompt is 25-40 words
- ✅ Describes primary movement clearly
- ✅ Includes camera behavior
- ✅ Mentions pacing/timing
- ✅ Appropriate for 5-second duration
- ✅ Technically feasible for AI animation tools

---

## Update Environment Variables

After creating all three assistants, update your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_SCRIPT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_SEGMENT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_ANIMATION_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
```

### Finding Your Assistant IDs

1. Go to https://platform.openai.com/assistants
2. Click on each assistant you created
3. The Assistant ID is displayed at the top of the page
4. Format: `asst_` followed by 24 alphanumeric characters

---

## Complete End-to-End Test

Once all three assistants are created and configured, perform a complete workflow test:

### Test Workflow

1. **Script Generation**
   ```
   Input: "Create a 50-second ad for a smart home security camera with AI detection"
   Assistant: Script Assistant
   Output: 50-second script with 3 sections
   ```

2. **Segmentation**
   ```
   Input: [The complete script from step 1]
   Assistant: Segment Assistant
   Output: JSON with 10 segments and image prompts
   ```

3. **Animation Prompts**
   ```
   Input: [Each segment from step 2, one at a time]
   Assistant: Animation Assistant
   Output: Animation prompt for each segment (test 2-3 segments)
   ```

### Success Criteria

- ✅ Script Assistant generates coherent 50-second scripts
- ✅ Segment Assistant produces valid JSON with 10 segments
- ✅ Image prompts are detailed and visually descriptive
- ✅ Animation Assistant creates feasible motion descriptions
- ✅ All three assistants respond consistently across multiple tests
- ✅ Output format matches expected structure
- ✅ Content quality is suitable for professional advertising

---

## Troubleshooting

### Script Assistant Issues

**Problem**: Script is too short or too long
- **Solution**: Adjust temperature (try 0.6-0.8) or add emphasis in instructions about 50-second duration

**Problem**: Script lacks structure
- **Solution**: In your prompt, explicitly request the three-section format

### Segment Assistant Issues

**Problem**: Not returning valid JSON
- **Solution**: Enable JSON mode in assistant settings, or add "Respond only with valid JSON" to your prompt

**Problem**: Uneven segment distribution
- **Solution**: Emphasize in prompt: "Divide evenly into exactly 10 segments"

**Problem**: Image prompts too vague
- **Solution**: Request more detail: "Provide highly detailed image prompts with specific visual elements"

### Animation Assistant Issues

**Problem**: Animation prompts too complex
- **Solution**: Lower temperature to 0.5 for more conservative animations

**Problem**: Inconsistent style across segments
- **Solution**: Provide context about previous segments or overall video style in your prompt

---

## Best Practices

### For Production Use

1. **Consistent Prompting**: Use the same prompt structure for similar requests
2. **Context Preservation**: When using Segment and Animation assistants, provide full context
3. **Error Handling**: Implement retry logic for API failures
4. **Response Validation**: Always validate JSON structure from Segment Assistant
5. **Cost Management**: Monitor token usage, especially with gpt-4 models

### Optimization Tips

1. **Batch Processing**: Process multiple segments in parallel when possible
2. **Caching**: Cache common script patterns or segment structures
3. **Model Selection**: Use gpt-4o for best quality, gpt-3.5-turbo for faster/cheaper testing
4. **Temperature Tuning**: Adjust based on desired creativity vs. consistency

---

## Cost Estimation

### Per Video Generation (Approximate)

**Script Assistant**:
- Input: ~500 tokens (instructions + prompt)
- Output: ~400 tokens (script)
- Cost: ~$0.02 per script (gpt-4o)

**Segment Assistant**:
- Input: ~1,000 tokens (instructions + script)
- Output: ~1,500 tokens (JSON with 10 segments)
- Cost: ~$0.04 per segmentation (gpt-4o)

**Animation Assistant** (10 segments):
- Input per segment: ~600 tokens
- Output per segment: ~100 tokens
- Cost: ~$0.10 for all 10 segments (gpt-4o)

**Total OpenAI Assistant Cost per Video**: ~$0.16

*Note: Costs vary based on model choice and actual token usage*

---

## Next Steps

After completing this setup:

1. ✅ Verify all three Assistant IDs are in your `.env` file
2. ✅ Test each assistant individually in the Playground
3. ✅ Perform end-to-end workflow test
4. ✅ Document any custom adjustments you made
5. ✅ Proceed to integrate assistants into the application code

---

## Support Resources

- **OpenAI Assistants API Documentation**: https://platform.openai.com/docs/assistants/overview
- **OpenAI Playground**: https://platform.openai.com/playground
- **API Keys Management**: https://platform.openai.com/api-keys
- **Usage Dashboard**: https://platform.openai.com/usage

---

## Appendix: Quick Reference

### Assistant Configuration Summary

| Assistant | Model | Temperature | Response Format | Primary Function |
|-----------|-------|-------------|-----------------|------------------|
| Script | gpt-4o | 0.7 | Text | Generate 50s scripts |
| Segment | gpt-4o | 0.5 | JSON | Split into 10 segments |
| Animation | gpt-4o | 0.6 | Text | Create motion prompts |

### Environment Variables Template

```bash
# Copy this to your .env file and fill in your actual IDs
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_SCRIPT_ASSISTANT_ID=asst-your-script-assistant-id
OPENAI_SEGMENT_ASSISTANT_ID=asst-your-segment-assistant-id
OPENAI_ANIMATION_ASSISTANT_ID=asst-your-animation-assistant-id
```
