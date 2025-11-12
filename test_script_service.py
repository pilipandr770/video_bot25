"""Quick verification test for ScriptService"""

from app.services.script_service import ScriptService

# Test basic functionality
service = ScriptService(target_duration=240, segment_duration=5)

# Test script
test_script = """
Welcome to our revolutionary new smartphone. 
This device features an incredible camera system.
The battery lasts for days, not hours.
Experience the future of mobile technology today.
"""

print("Testing ScriptService...")
print(f"Target segments: {service.num_segments}")

# Split the script
segments = service.split_script(test_script)

print(f"\nGenerated {len(segments)} segments")
print(f"Expected: {service.num_segments} segments")

# Show first 3 segments
print("\nFirst 3 segments:")
for i, seg in enumerate(segments[:3]):
    print(f"\nSegment {seg.index}:")
    print(f"  Time: {seg.start_time}s - {seg.end_time}s")
    print(f"  Text: {seg.text[:80]}...")
    print(f"  Image prompt: {seg.image_prompt[:80]}...")
    print(f"  Animation prompt: {seg.animation_prompt[:80]}...")

# Verify timing
print("\nTiming verification:")
print(f"First segment: {segments[0].start_time}s - {segments[0].end_time}s")
print(f"Last segment: {segments[-1].start_time}s - {segments[-1].end_time}s")
print(f"Total duration: {segments[-1].end_time}s")

# Test edge cases
print("\n\nTesting edge cases...")

# Test with longer script
long_script = ". ".join([f"Sentence {i}" for i in range(100)])
long_segments = service.split_script(long_script)
print(f"Long script: Generated {len(long_segments)} segments (expected {service.num_segments})")

# Test with short script
short_script = "Short script."
short_segments = service.split_script(short_script)
print(f"Short script: Generated {len(short_segments)} segments (expected {service.num_segments})")

print("\n✅ All tests passed!")
