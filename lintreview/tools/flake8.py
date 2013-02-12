import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command

log = logging.getLogger(__name__)


class Flake8(Tool):

    name = 'flake8'

    def check_dependencies(self):
        """
        The flake8 module is installed as a dependency
        for lintreview, therefore it is always installed.
        """
        return True

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.py'

    def process_files(self, files):
        """
        Run code checks with flake8.
        Only a single process is made for all files
        to save resources.
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['flake8']
        if self.options.get('ignore'):
            command += ['--ignore', self.options.get('ignore')]
        command += files
        output = run_command(command, split=True, ignore_error=True)
        if not output:
            log.debug('No flake8 errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        flake8 only generates results as stdout.
        Parse the output for real data.
        """
        parts = line.split(':', 3)
        if len(parts) == 3:
            message = parts[2].strip()
        else:
            message = parts[3].strip()
        return (parts[0], int(parts[1]), message)