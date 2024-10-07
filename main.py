import os
import sys
import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction

logger = logging.getLogger(__name__)

class TextToolsExtension(Extension):
    def __init__(self):
        super(TextToolsExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        argument = event.get_argument() or ""
        if not argument.strip():
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Enter the text to transform',
                    description='Example: tt Hello world',
                    on_enter=None)
            ])
        
        transformations = self.get_transformations(argument)
        items = []
        for name, transformed_text in transformations.items():
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=name,
                description=transformed_text,
                on_enter=CopyToClipboardAction(transformed_text)
            ))
        
        return RenderResultListAction(items)

    def get_transformations(self, text):
        words = text.split()
        transformations = {}
        transformations['Uppercase'] = text.upper()
        transformations['Lowercase'] = text.lower()
        transformations['Title Case'] = text.title()
        transformations['Swap Case'] = text.swapcase()
        transformations['Capitalize Each Word'] = ' '.join(word.capitalize() for word in words)
        transformations['CamelCase'] = ''.join(word.capitalize() for word in words)
        transformations['Lower CamelCase'] = words[0].lower() + ''.join(word.capitalize() for word in words[1:]) if words else ''
        transformations['Snake Case'] = '_'.join(word.lower() for word in words)
        transformations['Kebab Case'] = '-'.join(word.lower() for word in words)
        transformations['Dot Case'] = '.'.join(word.lower() for word in words)
        transformations['Slash Case'] = '/'.join(word.lower() for word in words)
        transformations['Backslash Case'] = '\\'.join(word.lower() for word in words)
        transformations['Reverse'] = text[::-1]
        transformations['SpongeBob Case'] = ''.join(c.lower() if i % 2 else c.upper() for i, c in enumerate(text))
        return transformations

if __name__ == '__main__':
    TextToolsExtension().run()
