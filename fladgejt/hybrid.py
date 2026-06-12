
from fladgejt.rest import RestClient
from fladgejt.webui import WebuiClient


class HybridClient(RestClient, WebuiClient):  # pyright: ignore [reportUnsafeMultipleInheritance] # verified that all __init__ methods call super()
    pass
