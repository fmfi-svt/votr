
from .action import Action
from .actionlist import ActionList
from .button import Button
from .dialogbody import DialogBody
from .htmlarea import HtmlArea

from .component import Component as TODO


component_classes = {
    'action': Action,
    'actionList': ActionList,
    'body': DialogBody,
    'button': Button,
    'changeGuardInteractive': TODO,
    'checkBox': TODO,
    'checkList': TODO,
    'comboBox': TODO,
    'dateControl': TODO,
    'eventInteractive': TODO,
    'htmlArea': HtmlArea,
    'image': TODO,
    'label': TODO,
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
    'separator': TODO,
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
