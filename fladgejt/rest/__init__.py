from fladgejt.base import BaseClient
from fladgejt.rest.studium import RestStudiumMixin
#from fladgejt.rest.terminy import RestTerminyMixin
from typing import override


# Disable RestTerminyMixin until it gives us all columns.


class RestClient(RestStudiumMixin, BaseClient):
    @override
    async def check_connection(self) -> None:
        await self.context.request_json('')
        await super().check_connection()
