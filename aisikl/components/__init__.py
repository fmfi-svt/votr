from aisikl.components.action import Action
from aisikl.components.actionlist import ActionList
from aisikl.components.button import Button
from aisikl.components.checkbox import CheckBox
from aisikl.components.checklist import CheckList
from aisikl.components.combobox import ComboBox
from aisikl.components.component import Component
from aisikl.components.datecontrol import DateControl
from aisikl.components.dialogbody import DialogBody
from aisikl.components.htmlarea import HtmlArea
from aisikl.components.image import Image
from aisikl.components.label import Label
from aisikl.components.list import List
from aisikl.components.menuitem import MenuItem
from aisikl.components.numbercontrol import NumberControl
from aisikl.components.panel import Panel
from aisikl.components.popupmenu import PopupMenu
from aisikl.components.progressbar import ProgressBar
from aisikl.components.radiobox import RadioBox
from aisikl.components.separator import Separator
from aisikl.components.splitpane import SplitPane
from aisikl.components.stackedpane import StackedPane
from aisikl.components.tabbedpane import TabbedPane
from aisikl.components.table import Table
from aisikl.components.textarea import TextArea
from aisikl.components.textfield import TextField
from aisikl.components.tree import Tree
from aisikl.components.updown import UpDown


component_classes = {
    'action': Action,
    'actionList': ActionList,
    'body': DialogBody,
    'button': Button,
    'changeGuardInteractive': Component,  # TODO: implement
    'checkBox': CheckBox,
    'checkList': CheckList,
    'comboBox': ComboBox,
    'dateControl': DateControl,
    'eventInteractive': Component,  # TODO: implement
    'fileInput': Component,  # TODO: implement
    'htmlArea': HtmlArea,
    'htmlList': Component,  # TODO: implement
    'image': Image,
    'label': Label,
    'list': List,
    'listBox': Component,  # TODO: implement
    'menuItem': MenuItem,
    'numberControl': NumberControl,
    'panel': Panel,
    'popupMenu': PopupMenu,
    'progressBar': ProgressBar,
    'radioBox': RadioBox,
    'radioButton': Component,  # TODO: implement
    'radioGroup': Component,  # TODO: implement
    'separator': Separator,
    'splitPane': SplitPane,
    'stackedPane': StackedPane,
    'tabbedPane': TabbedPane,
    'table': Table,
    'textArea': TextArea,
    'textField': TextField,
    'tree': Tree,
    'upDown': UpDown,
    'valueInteractive': Component,  # TODO: implement
    'view': Component,  # TODO: implement
}
