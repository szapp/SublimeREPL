"""
Highlight blocks in python, e.g. # %%
"""
import sublime
import sublime_plugin


stylesheet = '''
    <style>
        div.horz {
            height: 1px;
            margin-top: -1px;
            padding-top: 0px;
            margin-bottom: 0px;
            padding-bottom: -1px;
            line-height: 0px;
        }
        html.dark div.horz {
            border-top: 1px solid #606060FF;
        }
        html.light div.horz {
            border-left: 1px solid #ffffff18;
        }
    </style>
'''


class HighlightPythonBlocks(sublime_plugin.ViewEventListener):
    phantom_set = dict()

    def on_load(self):
        self.update_regions()

    def on_activated(self):
        self.update_regions()

    def on_modified(self):
        self.update_regions()

    def update_regions(self):
        view = self.view
        v_id = view.buffer_id()

        # Only for python syntax
        if view.settings().get('syntax').find('ython') == -1:
            return

        # Find block indicators
        blocks = view.find_all(r'^[[:blank:]]*#[[:blank:]]*%%')

        phantoms = []
        for block in blocks:

            # Get previous line
            block = view.line(block)
            block = sublime.Region(block.begin()-1, block.begin()-1)
            block = view.line(block)

            # Create phantom
            phantoms.append(sublime.Phantom(
                block,
                ('<body id="py_blocks">' + stylesheet +
                 '<div class="horz">' + '&nbsp;' * 79 + '</div></body>'),
                sublime.LAYOUT_BLOCK))

        self.phantom_set[v_id] = sublime.PhantomSet(view, 'py_blocks')
        self.phantom_set[v_id].update(phantoms)
