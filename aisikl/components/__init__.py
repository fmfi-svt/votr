
from .action import Action
from .actionlist import ActionList
from .button import Button
from .checkbox import CheckBox
from .dialogbody import DialogBody
from .htmlarea import HtmlArea
from .image import Image
from .label import Label
from .separator import Separator

from .component import Component as TODO


component_classes = {
    'action': Action,
    'actionList': ActionList,
    'body': DialogBody,
    'button': Button,
    'changeGuardInteractive': TODO,
    'checkBox': CheckBox,
    'checkList': TODO,
    'comboBox': TODO,
    'dateControl': TODO,
    'eventInteractive': TODO,
    'htmlArea': HtmlArea,
    'image': Image,
    'label': Label,
    'list': TODO,
    'listBox': TODO,
    'menuItem': TODO,
    'numberControl': TODO,
    'panel': TODO,
    'popupMenu': TODO,
    'progressBar': TODO,
    'radioBox': TODO,
    'radioButton': TODO,
    'radioGroup': TODO,
    'separator': Separator,
    'splitPane': TODO,
    'tabbedPane': TODO,
    'table': TODO,
    'textArea': TODO,
    'textField': TODO,
    'tree': TODO,
    'upDown': TODO,
    'valueInteractive': TODO,
    'view': TODO,
}
