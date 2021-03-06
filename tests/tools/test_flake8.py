from __future__ import absolute_import
from lintreview.review import Problems
from lintreview.tools.flake8 import Flake8
from unittest import TestCase
from nose.tools import eq_, assert_in
from tests import read_file, read_and_restore_file


class TestFlake8(TestCase):

    fixtures = [
        'tests/fixtures/pep8/no_errors.py',
        'tests/fixtures/pep8/has_errors.py',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = Flake8(self.problems, options={'config': ''})

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.php'))
        self.assertFalse(self.tool.match_file('test.js'))
        self.assertFalse(self.tool.match_file('dir/name/test.js'))
        self.assertTrue(self.tool.match_file('test.py'))
        self.assertTrue(self.tool.match_file('dir/name/test.py'))

    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    def test_process_files__one_file_fail(self):
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        eq_(2, problems[0].line)
        eq_(2, problems[0].position)
        assert_in('multiple imports on one line', problems[0].body)

    def test_process_files_two_files(self):
        self.tool.process_files(self.fixtures)

        eq_([], self.problems.all(self.fixtures[0]))

        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 6

        eq_(2, problems[0].line)
        eq_(2, problems[0].position)
        assert_in('multiple imports on one line', problems[0].body)

    def test_config_options_and_process_file(self):
        options = {
            'ignore': 'F4,W603',
        }
        self.tool = Flake8(self.problems, options)
        self.tool.process_files([self.fixtures[1]])
        problems = self.problems.all(self.fixtures[1])
        assert len(problems) >= 5
        for p in problems:
            self.assertFalse('F4' in p.body)
            self.assertFalse('W603' in p.body)

    def test_make_command__config(self):
        options = {
            'ignore': 'F4,W603',
            'max-line-length': 120,
            'max-complexity': 10
        }
        tool = Flake8(self.problems, options)
        out = tool.make_command([self.fixtures[1]])
        expected = [
            'flake8',
            '--isolated',
            '--ignore', 'F4,W603',
            '--max-complexity', 10,
            '--max-line-length', 120,
            self.fixtures[1]
        ]
        eq_(set(expected), set(out))

    def test_has_fixer__not_enabled(self):
        tool = Flake8(self.problems, {})
        eq_(False, tool.has_fixer())

    def test_has_fixer__enabled(self):
        tool = Flake8(self.problems, {'fixer': True})
        eq_(True, tool.has_fixer())

    def test_execute_fixer(self):
        tool = Flake8(self.problems, {'fixer': True})

        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)

        updated = read_and_restore_file(self.fixtures[1], original)
        assert original != updated, 'File content should change.'
        eq_(0, len(self.problems.all()), 'No errors should be recorded')

    def test_execute_fixer__fewer_problems_remain(self):
        tool = Flake8(self.problems, {'fixer': True})

        # The fixture file can have all problems fixed by autopep8
        original = read_file(self.fixtures[1])
        tool.execute_fixer(self.fixtures)
        tool.process_files(self.fixtures)

        read_and_restore_file(self.fixtures[1], original)
        assert 1 < len(self.problems.all()), 'Most errors should be fixed'

        text = [c.body for c in self.problems.all()]
        assert_in("'<>' is deprecated", ' '.join(text))
