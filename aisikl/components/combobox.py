from typing import TYPE_CHECKING, NamedTuple, override

from aisikl.components.control import Control
from aisikl.events import selection_event
from aisikl.typeutils import ct, nn

if TYPE_CHECKING:
    from bs4.element import Tag

    from aisikl.dialog import Dialog
    from aisikl.operations import Operations


class Option(NamedTuple):
    title: str
    id: str
    tool_tip_text: str


class ComboBox(Control):
    """A WebUI drop-down list widget.

    webui.js calls it "ComboBox", but the text is never editable. So to be
    pedantic, the "ComboBox" name is wrong: this component is actually a
    [drop-down list](https://en.wikipedia.org/wiki/Drop-down_list), *not* a
    [combo box](https://en.wikipedia.org/wiki/Combo_box).
    """

    selected_index: int
    """Index of the selected option. -1 if none."""

    options: list[Option]

    def __init__(
        self,
        dialog: Dialog,
        id: str,
        type: str,
        parent_id: str | None,
        properties: dict[str, object],
        element: Tag | None,
    ) -> None:
        super().__init__(dialog, id, type, parent_id, properties, element)
        self.tool_tip_like_data = ct(bool, properties.get("ttld", False))
        """Whether the AIS UI shows the current [`Option.tool_tip_text`][] when
        the whole box is hovered. Uninteresting.
        """
        self._parse_options(nn(element))

    def _parse_options(self, element: Tag) -> None:
        self.selected_index = -1
        self.options = []
        for index, option in enumerate(element.find_all("option")):
            self.options.append(Option(
                title=option.get_text(),
                id=ct(str, option.get("sid", "")),
                tool_tip_text=ct(str, option.get("title", "")),
            ))
            if option.has_attr("selected"):
                self.selected_index = index

    @property
    def selected_option(self) -> Option | None:
        if self.selected_index == -1:
            return None
        return self.options[self.selected_index]

    async def select(
        self, index: int, *, return_ops: bool = False
    ) -> Operations:
        """Selects the option at ``index``."""
        await self.log(
            "action", f'Selecting "{self.options[index].title}" in {self.id}')
        self.selected_index = index
        return await self._fire_event(return_ops=return_ops)

    async def _fire_event(self, *, return_ops: bool) -> Operations:
        self.dialog.component_changes(self, False)
        ev = selection_event(self, self.selected_index)
        return await self.dialog.app.send_events(ev, return_ops=return_ops)

    @override
    def changed_properties(self) -> str:
        cdata = (
            "<root><selection>"
            f"<selectedIndexes>{self.selected_index}</selectedIndexes>"
            "</selection></root>"
        )
        return self._build_changed_properties(dataView=(True, True, cdata))

    def _ais_setDataView(self, id: str, body: Tag) -> None:
        data_view = nn(body.find(id=id))
        combo_box_list = nn(data_view.find(id="comboBoxList", recursive=False))
        if combo_box_list.has_attr("selectedIndex_"):
            self.selected_index = int(ct(str, combo_box_list["selectedIndex_"]))
        else:
            self._parse_options(combo_box_list)
        self.dialog.try_interactive(self, "SelectionEvent")

    _ais_setDataView.wants_body = True  # pyrefly: ignore [missing-attribute] # pyright: ignore [reportFunctionMemberAccess]
