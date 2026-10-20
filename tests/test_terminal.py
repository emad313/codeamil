import io

from app.terminal import TerminalAnimation


def test_animation_is_quiet_when_disabled():
    stream = io.StringIO()
    animation = TerminalAnimation(stream=stream, enabled=False)

    with animation:
        pass

    assert stream.getvalue() == ""


def test_animation_clears_output_when_stopped():
    stream = io.StringIO()
    animation = TerminalAnimation(
        stream=stream,
        enabled=True,
        interval=0.01,
    )

    animation.start()
    animation.stop()

    output = stream.getvalue()
    assert "\033[?25l" in output
    assert "\033[?25h" in output
    assert "\r" in output
