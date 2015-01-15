
from .actionablecontrol import ActionableControl


class HtmlArea(ActionableControl):
    def __init__(self, dialog_soup, element, dialog):
        super().__init__(dialog_soup, element, dialog)
        self.tool_tip_like_data = element.get('tooltiplikedata')
        self._parse_content(element)
        # Note: This is where we should call component_changes() if we actually
        # supported canClose.

    def _parse_content(self, element):
        self.content = element.find(id='htmlContent').get_text()[4:-3]

    def _ais_setHtml(self, id, body):
        self._parse_content(body.find(id=id))
    _ais_setHtml.wants_body = True

    def changed_properties(self):
        return self._build_changed_properties(canClose=self.can_close)

    @property
    def can_close(self):
        # canClose is actually determined by a script running in the iframe.
        # Since we don't run anything, we don't support canClose.
        raise Exception('canClose is unsupported')
