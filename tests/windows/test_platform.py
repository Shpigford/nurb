from nurb.platform import current_platform, executable_name


def test_platform_is_string():
    assert current_platform()


def test_executable_name():
    result = executable_name("uv")
    assert result in {"uv", "uv.exe"}
