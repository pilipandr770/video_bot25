"""
Test the separation of image generation and animation in VideoService.
This test validates that the new methods work correctly without making real API calls.
"""
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.video_job import ScriptSegment, VideoSegment, SegmentStatus
from app.services.video_service import VideoService


def create_mock_script_segment(index: int) -> ScriptSegment:
    """Create a mock script segment for testing."""
    return ScriptSegment(
        index=index,
        text=f"Test segment {index} text",
        start_time=index * 5.0,
        end_time=(index + 1) * 5.0,
        image_prompt=f"Test image prompt {index}",
        animation_prompt=f"Test animation prompt {index}"
    )


def test_generate_images_only():
    """Test that generate_images_only creates images without animation."""
    print("\n🧪 Testing generate_images_only...")
    
    # Create mock services
    mock_runway = Mock()
    mock_runway.generate_image = Mock(side_effect=lambda prompt: f"image_task_{prompt[-1]}")
    mock_runway.download_result = Mock(return_value=None)
    
    mock_script_service = Mock()
    mock_file_manager = Mock()
    mock_file_manager.temp_dir = "/tmp/test"
    
    # Create video service
    video_service = VideoService(
        runway_service=mock_runway,
        script_service=mock_script_service,
        file_manager=mock_file_manager,
        max_workers=2
    )
    
    # Create test segments
    segments = [create_mock_script_segment(i) for i in range(3)]
    
    # Track progress
    progress_calls = []
    def progress_callback(current, total):
        progress_calls.append((current, total))
    
    # Call generate_images_only
    job_id = "test_job_123"
    video_segments = video_service.generate_images_only(
        job_id=job_id,
        segments=segments,
        progress_callback=progress_callback
    )
    
    # Verify results
    assert len(video_segments) == 3, f"Expected 3 segments, got {len(video_segments)}"
    
    for i, seg in enumerate(video_segments):
        assert seg.index == i, f"Segment {i} has wrong index: {seg.index}"
        assert seg.image_path is not None, f"Segment {i} has no image_path"
        assert seg.video_path is None, f"Segment {i} should not have video_path yet"
        assert seg.status == SegmentStatus.IMAGE_READY, f"Segment {i} has wrong status: {seg.status}"
    
    # Verify Runway API was called for images only
    assert mock_runway.generate_image.call_count == 3, \
        f"Expected 3 image generation calls, got {mock_runway.generate_image.call_count}"
    assert mock_runway.animate_image.call_count == 0, \
        "animate_image should not be called in generate_images_only"
    
    print("✅ generate_images_only test passed!")
    print(f"   - Created {len(video_segments)} video segments with images")
    print(f"   - No animations were created (as expected)")
    print(f"   - Progress callback called {len(progress_calls)} times")


def test_animate_images_only():
    """Test that animate_images_only animates existing images."""
    print("\n🧪 Testing animate_images_only...")
    
    # Create mock services
    mock_runway = Mock()
    mock_runway.animate_image = Mock(side_effect=lambda img, prompt: f"video_task_{img[-5]}")
    mock_runway.download_result = Mock(return_value=None)
    
    mock_script_service = Mock()
    mock_file_manager = Mock()
    mock_file_manager.temp_dir = "/tmp/test"
    
    # Create video service
    video_service = VideoService(
        runway_service=mock_runway,
        script_service=mock_script_service,
        file_manager=mock_file_manager,
        max_workers=2
    )
    
    # Create test segments with images already generated
    video_segments = []
    for i in range(3):
        script_seg = create_mock_script_segment(i)
        video_seg = VideoSegment(
            index=i,
            script_segment=script_seg,
            status=SegmentStatus.IMAGE_READY
        )
        video_seg.image_path = f"/tmp/test/test_job_123/images/segment_{i:03d}_image.png"
        video_segments.append(video_seg)
    
    # Track progress
    progress_calls = []
    def progress_callback(current, total):
        progress_calls.append((current, total))
    
    # Call animate_images_only
    job_id = "test_job_123"
    animated_segments = video_service.animate_images_only(
        job_id=job_id,
        video_segments=video_segments,
        progress_callback=progress_callback
    )
    
    # Verify results
    assert len(animated_segments) == 3, f"Expected 3 segments, got {len(animated_segments)}"
    
    for i, seg in enumerate(animated_segments):
        assert seg.index == i, f"Segment {i} has wrong index: {seg.index}"
        assert seg.image_path is not None, f"Segment {i} lost its image_path"
        assert seg.video_path is not None, f"Segment {i} has no video_path"
        assert seg.status == SegmentStatus.VIDEO_READY, f"Segment {i} has wrong status: {seg.status}"
    
    # Verify Runway API was called for animation only
    assert mock_runway.animate_image.call_count == 3, \
        f"Expected 3 animation calls, got {mock_runway.animate_image.call_count}"
    assert mock_runway.generate_image.call_count == 0, \
        "generate_image should not be called in animate_images_only"
    
    print("✅ animate_images_only test passed!")
    print(f"   - Animated {len(animated_segments)} video segments")
    print(f"   - All segments retained their image_path")
    print(f"   - Progress callback called {len(progress_calls)} times")


def test_full_pipeline_separation():
    """Test the full pipeline with separated stages."""
    print("\n🧪 Testing full pipeline with separation...")
    
    # Create mock services
    mock_runway = Mock()
    mock_runway.generate_image = Mock(side_effect=lambda prompt: f"image_task_{prompt[-1]}")
    mock_runway.animate_image = Mock(side_effect=lambda img, prompt: f"video_task_{img[-5]}")
    mock_runway.download_result = Mock(return_value=None)
    
    mock_script_service = Mock()
    mock_file_manager = Mock()
    mock_file_manager.temp_dir = "/tmp/test"
    
    # Create video service
    video_service = VideoService(
        runway_service=mock_runway,
        script_service=mock_script_service,
        file_manager=mock_file_manager,
        max_workers=2
    )
    
    # Create test segments
    segments = [create_mock_script_segment(i) for i in range(5)]
    job_id = "test_job_456"
    
    # Stage 1: Generate images only
    print("   Stage 1: Generating images...")
    video_segments = video_service.generate_images_only(
        job_id=job_id,
        segments=segments
    )
    
    assert len(video_segments) == 5
    assert all(seg.image_path is not None for seg in video_segments)
    assert all(seg.video_path is None for seg in video_segments)
    assert all(seg.status == SegmentStatus.IMAGE_READY for seg in video_segments)
    print("   ✓ Images generated successfully")
    
    # Stage 2: Animate images
    print("   Stage 2: Animating images...")
    animated_segments = video_service.animate_images_only(
        job_id=job_id,
        video_segments=video_segments
    )
    
    assert len(animated_segments) == 5
    assert all(seg.image_path is not None for seg in animated_segments)
    assert all(seg.video_path is not None for seg in animated_segments)
    assert all(seg.status == SegmentStatus.VIDEO_READY for seg in animated_segments)
    print("   ✓ Images animated successfully")
    
    # Verify API call order
    assert mock_runway.generate_image.call_count == 5
    assert mock_runway.animate_image.call_count == 5
    
    print("✅ Full pipeline separation test passed!")
    print(f"   - Generated {len(video_segments)} images in stage 1")
    print(f"   - Animated {len(animated_segments)} videos in stage 2")
    print(f"   - All intermediate results preserved")


if __name__ == '__main__':
    print("="*60)
    print("Testing VideoService Image/Animation Separation")
    print("="*60)
    
    try:
        test_generate_images_only()
        test_animate_images_only()
        test_full_pipeline_separation()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ Test failed: {e}")
        print("="*60)
        sys.exit(1)
        
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        sys.exit(1)
