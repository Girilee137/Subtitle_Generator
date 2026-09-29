import sys
from types import SimpleNamespace

from app.api.v1.health import gpu_available


def test_health_checks_cuda_availability_for_auto_mode(monkeypatch) -> None:
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    assert gpu_available("auto")
    assert gpu_available("cuda")
    assert not gpu_available("cpu")
