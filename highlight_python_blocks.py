"""
Highlight blocks in python, e.g. # %%
"""
import sublime_plugin


class HighlightPythonBlocks(sublime_plugin.ViewEventListener):
    def on_modified_async(self):
        self.update_regions()

    def on_activated_async(self):
        self.update_regions()

    def update_regions(self):
        view = self.view
        if not view.settings().get('syntax').find('python'):
            return
        blocks = view.find_all(r'^[[:blank:]]*#[[:blank:]]*%%')
        view.add_regions('py_blocks', blocks, 'comment')
