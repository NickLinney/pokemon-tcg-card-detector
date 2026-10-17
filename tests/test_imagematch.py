from pathlib import Path

from PIL import Image, ImageDraw

from ptcg.imagematch import compare_images


def test_identical_images_have_strong_visual_similarity(tmp_path: Path):
    image = Image.new("RGB", (240, 330), "gold")
    draw = ImageDraw.Draw(image)
    draw.rectangle((30, 40, 210, 180), fill="blue")
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    image.save(first)
    image.save(second)
    result = compare_images(first, second)
    assert result["score"] > 0.8
    assert result["printing_identity_sufficient"] is False
