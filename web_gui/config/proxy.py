import os


def set_proxy():
    # using v2rayn
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
    os.environ["HTTP_PROXYS"] = "http://127.0.0.1:10809"
