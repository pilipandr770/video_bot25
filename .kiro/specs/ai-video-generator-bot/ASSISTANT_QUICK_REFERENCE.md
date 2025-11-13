# OpenAI Assistants - Quick Reference Card

## 🎯 Three Assistants Overview

```
User Prompt → [Script Assistant] → 50s Script → [Segment Assistant] → 10 Segments + Images → [Animation Assistant] → Animation Prompts
```

---

## 1️⃣ Script Assistant

**ID Variable**: `OPENAI_SCRIPT_ASSISTANT_ID`

**Input**: Product/topic description (any length)

**Output**: 50-second script with 3 sections
```
[INTRODUCTION - 15 seconds]
[Hook and problem introduction]

[MAIN CONTENT - 25 seconds]
[Solution and key benefits]

[CONCLUSION - 10 seconds]
[Call to action]
```

**Settings**:
- Model: `gpt-4o`
- Temperature: `0.7`
- Response: Text

**Test Prompt**:
```
Create a 50-second ad for a smart fitness watch with heart rate monitoring and 7-day battery life.
```

---

## 2️⃣ Segment Assistant

**ID Variable**: `OPENAI_SEGMENT_ASSISTANT_ID`

**Input**: Complete 50-second script from Script Assistant

**Output**: JSON with 10 segments
```json
{
  "segments": [
    {
      "index": 1,
      "type": "intro",
      "start_time": 0.0,
      "end_time": 5.0,
      "text": "Script text for this segment",
      "image_prompt": "Detailed visual description..."
    },
    ...
  ]
}
```

**Segment Distribution**:
- Segments 1-3: `intro` (0-15s)
- Segments 4-7: `main` (15-40s)
- Segments 8-10: `outro` (40-50s)

**Settings**:
- Model: `gpt-4o`
- Temperature: `0.5`
- Response: JSON

**Test Prompt**:
```
Please segment this script:
[Paste complete script from Script Assistant]
```

---

## 3️⃣ Animation Assistant

**ID Variable**: `OPENAI_ANIMATION_ASSISTANT_ID`

**Input**: Single segment data (index, type, text, image_prompt)

**Output**: Animation prompt (25-40 words)
```
Slow 180-degree product rotation with gentle floating motion, 
blue light particles orbiting, smooth camera push in, 
premium pacing with elegant ease-in-out timing
```

**Settings**:
- Model: `gpt-4o`
- Temperature: `0.6`
- Response: Text

**Test Prompt**:
```
Create an animation prompt for this segment:

Segment: 4
Type: main
Text: "Introducing the FitPulse watch with advanced heart rate monitoring"
Image: "Hero shot of sleek fitness watch floating in space, dramatic lighting with blue accents, premium materials visible, professional product photography"
```

---

## 🔑 Environment Variables

Add to `.env`:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
OPENAI_SCRIPT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_SEGMENT_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_ANIMATION_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
```

---

## ✅ Validation Checklist

### Script Assistant Output
- [ ] Has 3 clear sections (intro/main/outro)
- [ ] Approximately 125-150 words total
- [ ] Engaging opening hook
- [ ] Clear call to action
- [ ] Visual and descriptive language

### Segment Assistant Output
- [ ] Valid JSON format
- [ ] Exactly 10 segments
- [ ] Segments 1-3 are type "intro"
- [ ] Segments 4-7 are type "main"
- [ ] Segments 8-10 are type "outro"
- [ ] Each segment is 5 seconds
- [ ] Image prompts are 30-50 words
- [ ] Text evenly distributed

### Animation Assistant Output
- [ ] 25-40 words per prompt
- [ ] Describes camera movement
- [ ] Specifies motion type
- [ ] Includes pacing/timing
- [ ] Feasible for AI animation

---

## 🚨 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Script too long/short | Adjust temperature or emphasize duration in prompt |
| Segment Assistant not returning JSON | Enable JSON mode in settings |
| Image prompts too vague | Request "highly detailed visual descriptions" |
| Animation prompts too complex | Lower temperature to 0.5 |
| Inconsistent style | Provide more context about overall video style |

---

## 💰 Cost Per Video (Approximate)

- Script Assistant: ~$0.02
- Segment Assistant: ~$0.04
- Animation Assistant (10 segments): ~$0.10
- **Total**: ~$0.16 per video (using gpt-4o)

---

## 🔗 Quick Links

- **Create Assistants**: https://platform.openai.com/playground
- **View Assistants**: https://platform.openai.com/assistants
- **API Keys**: https://platform.openai.com/api-keys
- **Usage Dashboard**: https://platform.openai.com/usage

---

## 📋 Setup Steps (Ultra-Quick)

1. Open OpenAI Playground
2. Create 3 assistants with instructions from:
   - `script-assistant-instructions.md`
   - `segment-assistant-instructions.md`
   - `animation-assistant-instructions.md`
3. Copy each Assistant ID
4. Add IDs to `.env` file
5. Test each assistant
6. Done! ✅

---

## 🎬 Example Workflow

```
1. User: "Create ad for eco-friendly water bottle"
   ↓
2. Script Assistant: Generates 50s script
   ↓
3. Segment Assistant: Creates 10 segments with image prompts
   ↓
4. Animation Assistant: Generates animation prompt for each segment
   ↓
5. Runway API: Generates images → animates them
   ↓
6. OpenAI TTS: Creates voiceover
   ↓
7. FFmpeg: Assembles final video
   ↓
8. User receives: Complete 50-second video! 🎉
```

---

**For detailed instructions, see**: `ASSISTANT_SETUP_GUIDE.md`
