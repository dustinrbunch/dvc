import os

from dvc.command.common.base import CmdBase
from dvc.logger import Logger
from dvc.state_file import StateFile
from dvc.path.data_item import DataItem


class CmdAdd(CmdBase):
    def __init__(self, settings):
        super(CmdAdd, self).__init__(settings)

    def collect_file(self, fname):
        return [self.settings.path_factory.data_item(fname)]

    def collect_dir(self, dname):
        targets = []
        for root, dirs, files in os.walk(dname):
            for fname in files:
                targets += self.collect_file(os.path.join(root, fname))
        return targets

    def collect_targets(self, inputs):
        targets = []
        for i in inputs:
            if not os.path.isdir(i):
                targets += self.collect_file(i)
            else:
                targets += self.collect_dir(i)
        return targets

    def add_files(self, targets):
        for data_item in targets:
            data_item.move_data_to_cache()

    def create_state_files(self, targets):
        """
        Create state files for all targets.
        """
        for data_item in targets:
            Logger.debug('Creating state file for {}'.format(data_item.data.relative))

            fname = os.path.basename(data_item.data.relative + StateFile.STATE_FILE_SUFFIX)
            out = StateFile.parse_deps_state(self.settings, [data_item.data.relative],
                                             currdir=os.path.curdir)
            state_file = StateFile(fname=fname,
                                   cmd=None,
                                   out=out,
                                   out_git=[],
                                   deps=[],
                                   locked=True)
            state_file.save()
            Logger.debug('State file "{}" was created'.format(data_item.state.relative))

    def run(self):
        targets = self.collect_targets(self.parsed_args.input)
        self.add_files(targets)
        self.create_state_files(targets)
        msg = 'DVC add: {}'.format(str(self.parsed_args.input))
        self.commit_if_needed(msg)
