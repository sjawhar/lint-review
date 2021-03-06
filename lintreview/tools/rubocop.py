from __future__ import absolute_import
import os
import logging
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import bundle_exists

log = logging.getLogger(__name__)


class Rubocop(Tool):

    name = 'rubocop'

    def check_dependencies(self):
        """
        See if rubocop is on the PATH
        """
        return in_path('rubocop') or bundle_exists('rubocop')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.rb'

    def process_files(self, files):
        """
        Run code checks with rubocop
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = self._create_command()
        command += files
        output = run_command(
            command,
            split=True,
            ignore_error=True,
            include_errors=False
        )

        if not output:
            log.debug('No rubocop errors found.')
            return False

        for line in output:
            filename, line, error = self._parse_line(line)
            self.problems.add(filename, line, error)

    def _create_command(self):
        command = ['rubocop']
        if bundle_exists('rubocop'):
            command = ['bundle', 'exec', 'rubocop']
        command += ['--format', 'emacs']
        if self.options.get('display_cop_names', '').lower() == 'true':
            command.append('--display-cop-names')
        return command

    def _parse_line(self, line):
        """
        `rubocop --format emacs` lines look like this:
        filename:lineno:charno: error-type: error
        """
        parts = line.split(':', 3)
        message = parts[3].strip()
        return (parts[0], int(parts[1]), message)

    def has_fixer(self):
        """
        Rubocop has a fixer that can be enabled through configuration.
        """
        return bool(self.options.get('fixer', False))

    def process_fixer(self, files):
        """Run Rubocop in the fixer mode.
        """
        command = self.create_fixer_command(files)
        run_command(
            command,
            ignore_error=True,
            include_errors=False)

    def create_fixer_command(self, files):
        command = self._create_command()
        command.append('--auto-correct')
        command += files
        return command
