"""Special TOC directive to filter out specific enries based on configured options.

See https://stackoverflow.com/questions/15001888/conditional-toctree-in-sphinx
for more information.

"""

import re

from docutils.parsers.rst import directives
from sphinx.directives.other import TocTree

FILTER_OPTION_SPEC = {
    "excludebuilder": directives.unchanged,
}
FILTER_OPTION_SPEC.update(TocTree.option_spec)


def setup(app):
    app.add_config_value("toc_filter_exclude", [], "html")
    app.add_directive("toctree-filt", TocTreeFilt)
    return {"version": "1.0.0"}


class TocTreeFilt(TocTree):
    """Directive to allow filtering of TOC entries based on configured options.

    Directive to notify Sphinx about the hierarchical structure of the docs,
    and to include a table-of-contents like tree in the current document. This
    version filters the entries based on a list of prefixes. We simply filter
    the content of the directive and call the super's version of run. The
    list of exclusions is stored in the **toc_filter_exclusion** list. Any
    table of content entry prefixed by one of these strings will be excluded.
    If `toc_filter_exclusion=['secret','draft']` then all toc entries of the
    form `:secret:ultra-api` or `:draft:new-features` will be excluded from
    the final table of contents. Entries without a prefix are always included.
    """

    option_spec = FILTER_OPTION_SPEC
    hasPat = re.compile(r"^\s*:(.+):(.+)$")

    # Remove any entries in the content that we dont want and strip
    # out any filter prefixes that we want but obviously don't want the
    # prefix to mess up the file name.
    def filter_entries(self, entries):
        if self.env.app.builder.name in self.options.get("excludebuilder", ""):
            return []
        excl = self.state.document.settings.env.config.toc_filter_exclude
        filtered = []
        for e in entries:
            m = self.hasPat.match(e)
            if m is not None:
                if m.groups()[0] not in excl:
                    filtered.append(m.groups()[1])
            else:
                filtered.append(e)
        return filtered

    def run(self):
        # Remove all TOC entries that should not be on display
        self.content = self.filter_entries(self.content)
        return super().run()
