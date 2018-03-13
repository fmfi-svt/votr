
from .action import Action
from .actionlist import ActionList
from .button import Button
from .checkbox import CheckBox
from .checklist import CheckList
from .combobox import ComboBox
from .datecontrol import DateControl
from .dialogbody import DialogBody
from .htmlarea import HtmlArea
from .image import Image
from .label import Label
from .list import List
from .menuitem import MenuItem
from .numbercontrol import NumberControl
from .panel import Panel
from .popupmenu import PopupMenu
from .progressbar import ProgressBar
from .radiobox import RadioBox
from .separator import Separator
from .splitpane import SplitPane
from .stackedpane import StackedPane
from .tabbedpane import TabbedPane
from .table import Table
from .textarea import TextArea
from .textfield import TextField
from .tree import Tree
from .updown import UpDown

from .component import Component as TODO


component_classes = {
    'action': Action,
    'actionList': ActionList,
    'body': DialogBody,
    'button': Button,
    'changeGuardInteractive': TODO,
    'checkBox': CheckBox,
    'checkList': CheckList,
    'comboBox': ComboBox,
    'dateControl': DateControl,
    'eventInteractive': TODO,
    'fileInput': TODO,
    'htmlArea': HtmlArea,
    'htmlList': TODO,
    'image': Image,
    'label': Label,
    'list': List,
    'listBox': TODO,
    'menuItem': MenuItem,
    'numberControl': NumberControl,
    'panel': Panel,
    'popupMenu': PopupMenu,
    'progressBar': ProgressBar,
    'radioBox': RadioBox,
    'radioButton': TODO,
    'radioGroup': TODO,
    'separator': Separator,
    'splitPane': SplitPane,
    'stackedPane': StackedPane,
    'tabbedPane': TabbedPane,
    'table': Table,
    'textArea': TextArea,
    'textField': TextField,
    'tree': Tree,
    'upDown': UpDown,
    'valueInteractive': TODO,
    'view': TODO,
}
