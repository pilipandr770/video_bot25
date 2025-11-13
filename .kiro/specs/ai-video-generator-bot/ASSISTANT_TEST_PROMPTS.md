# OpenAI Assistants - Test Prompts

Use these test prompts to validate that your assistants are working correctly.

---

## Test Case 1: Tech Product (Smartphone)

### Script Assistant Test

**Prompt**:
```
Create a 50-second advertising script for a new smartphone called "Phoenix X1" that features:
- 72-hour battery life
- Professional triple camera system with 8K video
- Night photography capabilities
- Targeted at content creators and busy professionals
```

**Expected Output Structure**:
- Introduction (15s): Hook about phone dying at wrong time, missing photo moments
- Main Content (25s): Introduce Phoenix X1, highlight battery and camera features
- Conclusion (10s): Call to action with pre-order offer

---

### Segment Assistant Test

**Prompt**:
```
Please segment this script:

[INTRODUCTION - 15 seconds]
Tired of your phone dying right when you need it most? Missing those perfect photo moments because your camera can't keep up? There's a better way.

[MAIN CONTENT - 25 seconds]
Introducing the new Phoenix X1 - with revolutionary 72-hour battery life and a professional-grade triple camera system. Capture stunning 8K videos, take crystal-clear night photos, and never worry about charging again. Whether you're a content creator, busy professional, or adventure seeker, the Phoenix X1 keeps up with your life.

[CONCLUSION - 10 seconds]
The Phoenix X1. Power that lasts. Moments that matter. Pre-order now and get 20% off. Visit phoenix-tech.com today.
```

**Expected Output**:
- Valid JSON with 10 segments
- Segments 1-3: type "intro"
- Segments 4-7: type "main"
- Segments 8-10: type "outro"
- Each segment has detailed image_prompt (30-50 words)

---

### Animation Assistant Test

**Prompt**:
```
Create an animation prompt for this segment:

Segment: 4
Type: main
Text: "Introducing the new Phoenix X1 - with revolutionary 72-hour battery life"
Image: "Hero shot of sleek Phoenix X1 smartphone floating in space, dramatic studio lighting with blue and purple accents, battery icon glowing prominently, premium metallic finish, high-end product photography, clean background, sharp focus, professional commercial style"
```

**Expected Output**:
- 25-40 word animation prompt
- Describes rotation or camera movement
- Mentions lighting effects or particles
- Specifies pacing (smooth, elegant, etc.)
- Appropriate for 5-second duration

---

## Test Case 2: Lifestyle Product (Fitness App)

### Script Assistant Test

**Prompt**:
```
Create a 50-second advertising script for a fitness app called "FitLife Pro" that offers:
- AI-powered personalized workout plans
- Smart nutrition tracking
- Live classes with professional trainers
- Supportive community features
- Targeted at people starting their fitness journey
```

**Expected Output Structure**:
- Introduction (15s): Question about having personal trainer in pocket
- Main Content (25s): Features of FitLife Pro, AI personalization, community
- Conclusion (10s): Call to action with free trial offer

---

### Segment Assistant Test

**Prompt**:
```
Please segment this script:

[INTRODUCTION - 15 seconds]
What if you could have a personal trainer, nutritionist, and wellness coach all in your pocket? Meet FitLife Pro - your complete health transformation starts here.

[MAIN CONTENT - 25 seconds]
FitLife Pro uses AI to create personalized workout plans that adapt to your progress. Track your meals with smart nutrition insights, join live classes with world-class trainers, and connect with a supportive community. Whether you're starting your fitness journey or pushing to the next level, FitLife Pro makes it simple, effective, and fun.

[CONCLUSION - 10 seconds]
Transform your life today. Download FitLife Pro and start your free 30-day trial. Your future self will thank you.
```

**Expected Output**:
- Valid JSON with 10 segments
- Proper segment type distribution
- Image prompts focused on fitness, health, and lifestyle
- Visual descriptions appropriate for app advertisement

---

### Animation Assistant Test

**Prompt**:
```
Create an animation prompt for this segment:

Segment: 5
Type: main
Text: "Track your meals with smart nutrition insights, join live classes with world-class trainers"
Image: "Split screen composition showing nutrition tracking interface on left and live fitness class on right, vibrant and energetic colors, modern app UI design, people exercising in background, professional lifestyle photography, bright and motivating atmosphere"
```

**Expected Output**:
- Animation describing screen transitions or UI interactions
- Energetic and motivating motion style
- Appropriate for app demonstration

---

## Test Case 3: Eco Product (Water Bottle)

### Script Assistant Test

**Prompt**:
```
Create a 50-second advertising script for an eco-friendly water bottle called "EcoFlow" that features:
- Keeps drinks cold for 48 hours
- Made from 100% recycled materials
- Leak-proof design
- Supports ocean cleanup initiatives
- Targeted at environmentally conscious consumers
```

**Expected Output Structure**:
- Introduction (15s): Problem with single-use plastics or warm drinks
- Main Content (25s): EcoFlow features, sustainability, performance
- Conclusion (10s): Call to action emphasizing environmental impact

---

## Validation Criteria

### ✅ Script Assistant Success Indicators
- [ ] Script is approximately 125-150 words
- [ ] Clear three-part structure
- [ ] Engaging opening hook
- [ ] Benefits-focused (not just features)
- [ ] Strong call to action
- [ ] Visual and descriptive language
- [ ] Appropriate tone for target audience
- [ ] No grammatical errors

### ✅ Segment Assistant Success Indicators
- [ ] Valid JSON format (can be parsed)
- [ ] Exactly 10 segments
- [ ] All required fields present (index, type, start_time, end_time, text, image_prompt)
- [ ] Correct segment type distribution (3 intro, 4 main, 3 outro)
- [ ] Sequential timing (0-5, 5-10, 10-15, etc.)
- [ ] Text evenly distributed (12-15 words per segment)
- [ ] Image prompts are detailed (30-50 words)
- [ ] Image prompts include visual elements (lighting, composition, mood)
- [ ] Consistent visual style across segments

### ✅ Animation Assistant Success Indicators
- [ ] Prompt is 25-40 words
- [ ] Describes primary movement clearly
- [ ] Includes camera behavior (if applicable)
- [ ] Mentions pacing or timing
- [ ] Appropriate for 5-second duration
- [ ] Technically feasible for AI animation
- [ ] Matches the mood of the segment
- [ ] No overly complex multi-directional movements

---

## Troubleshooting Test Failures

### Script Assistant Issues

**Problem**: Script is too short (< 100 words)
```
Solution: Add to prompt: "Ensure the script is approximately 125-150 words for a full 50-second narration."
```

**Problem**: Missing section labels
```
Solution: Add to prompt: "Format with clear section headers: [INTRODUCTION - 15 seconds], [MAIN CONTENT - 25 seconds], [CONCLUSION - 10 seconds]"
```

**Problem**: Too feature-focused, not benefit-focused
```
Solution: Add to prompt: "Focus on benefits and emotional connection, not just technical features."
```

---

### Segment Assistant Issues

**Problem**: Not returning JSON
```
Solution 1: Enable JSON mode in assistant settings
Solution 2: Add to prompt: "Respond ONLY with valid JSON, no additional text"
```

**Problem**: Wrong number of segments
```
Solution: Add to prompt: "Create EXACTLY 10 segments, no more, no less"
```

**Problem**: Image prompts too short or vague
```
Solution: Add to prompt: "Each image_prompt must be 30-50 words with specific visual details including lighting, composition, mood, and style"
```

**Problem**: Uneven text distribution
```
Solution: Add to prompt: "Distribute the script text evenly across all 10 segments, approximately 12-15 words per segment"
```

---

### Animation Assistant Issues

**Problem**: Prompts too long (> 50 words)
```
Solution: Lower temperature to 0.5 or add to prompt: "Keep animation prompt between 25-40 words"
```

**Problem**: Too complex animations
```
Solution: Add to prompt: "Focus on ONE primary movement. Keep it simple and achievable for AI animation tools"
```

**Problem**: Missing pacing information
```
Solution: Add to prompt: "Always include pacing description (smooth, elegant, dynamic, etc.)"
```

---

## Performance Benchmarks

### Response Times (Approximate)
- Script Assistant: 10-20 seconds
- Segment Assistant: 20-40 seconds (more complex output)
- Animation Assistant: 5-10 seconds per segment

### Token Usage (Approximate)
- Script Assistant: 500 input + 400 output = 900 tokens
- Segment Assistant: 1000 input + 1500 output = 2500 tokens
- Animation Assistant: 600 input + 100 output = 700 tokens per segment

---

## Advanced Testing

### Test Edge Cases

1. **Very Short Product Description**
   ```
   "Create a 50-second ad for a new pen"
   ```
   Expected: Assistant should still create full 50-second script with creative details

2. **Very Detailed Product Description**
   ```
   [Provide 200+ word detailed product description]
   ```
   Expected: Assistant should distill to key points for 50-second format

3. **Technical Product**
   ```
   "Create ad for enterprise cloud security platform with zero-trust architecture"
   ```
   Expected: Script should be accessible to non-technical audience

4. **Emotional Product**
   ```
   "Create ad for memorial jewelry that holds ashes of loved ones"
   ```
   Expected: Sensitive, respectful tone while still being compelling

---

## Integration Testing

### Full Pipeline Test

1. Generate script with Script Assistant
2. Copy output to Segment Assistant
3. Verify JSON output
4. Take segments 1, 5, and 10
5. Generate animation prompts for each
6. Verify all outputs are consistent in style and quality

**Success Criteria**:
- All three assistants complete without errors
- Outputs flow logically from one to the next
- Visual style is consistent across all segments
- Total workflow takes < 2 minutes

---

## Documentation

After testing, document:
- [ ] Which test cases passed/failed
- [ ] Any adjustments made to assistant instructions
- [ ] Actual Assistant IDs used
- [ ] Any custom prompting techniques discovered
- [ ] Performance observations (speed, quality)

---

**Next Steps After Successful Testing**:
1. Add Assistant IDs to `.env` file
2. Update `app/config.py` to load new environment variables
3. Integrate assistants into application code
4. Test with real Runway API integration
5. Proceed to next implementation task
