import pytest
import time

@pytest.fixture(scope="function")
def app(request):
    from pyble import backend
    print ""

    app = backend.load(shell=False)

    while not app.isReady():
        pass

    return app

@pytest.fixture(scope="function")
def app_noshell(request):
    from pyble import backend
    print ""

    app = backend.load(shell=False)

    while not app.isReady():
        pass

    def teardown():
        print ""
        app.inq.put("stop")

    request.addfinalizer(teardown)
    return app

def test_backend_load_halt(app):
    assert app.isReady()
    app.halt()
    time.sleep(1)
    assert app.stop.is_set()

def test_backend_tunnels(app_noshell):
    inq, outq = app_noshell.getTunnels()
    assert inq
    assert outq

