# -*- coding: utf-8 -*-

"""
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import tempfile

from tdda.referencetest.checkpandas import PandasComparison
from tdda.referencetest.checkfiles import FilesComparison


# DEFAULT_FAIL_DIR is the default location for writing failing output
# if assertStringCorrect or assertFileCorrect fail with 'preprocessing'
# in place. This can be overridden using the set_defaults() class method.
DEFAULT_FAIL_DIR = os.environ.get('TDDA_FAIL_DIR', tempfile.gettempdir())


class ReferenceTest(object):
    """
    The :py:class:`~tdda.referencetest.referencetest.ReferenceTest` class
    provides support for comparing results against a set of reference
    "known to be correct" results.

    The functionality provided by this class can be used with:

        - the standard Python :py:mod:`unittest` framework, using the
          :py:class:`~tdda.referencetest.referencetestcase.ReferenceTestCase`
          class. This is a subclass of, and therefore a drop-in replacement
          for, :py:class:`unittest.TestCase`. It extends that class with all
          of the methods from the
          :py:class:`~tdda.referencetest.referencetest.ReferenceTest` class.

        - the :py:mod:`pytest` framework, using the
          :py:mod:`~tdda.referencetest.referencepytest` module.
          This module provides all of the methods from the
          :py:class:`~tdda.referencetest.referencetest.ReferenceTest` class,
          exposed as functions that can be called directly from tests
          in a :py:mod:`pytest` suite.

    In addition to the various test-assertion methods, the module also
    provides some useful instance variables. All of these can be set
    explicitly in test setup code, using the :py:meth:`set_defaults`
    class method:

        *tmp_dir*
            The location where temporary files can be written to. It defaults
            to a system-specific temporary area.

        *print_fn*
            The function to use to display information while running tests,
            which should have the same signature as Python's *__future__*
            standard print function.

        *verbose*
            Boolean verbose flag, to control reporting of errors while running
            tests. Reference tests tend to take longer to run than traditional
            unit tests, so it is often useful to be able to see
            information from failing tests as they happen, rather
            than waiting for the full report at the end.
    """

    # Verbose flag
    verbose = True

    # Temporary directory
    tmp_dir = DEFAULT_FAIL_DIR

    # Dictionary describing which kinds of reference files should be
    # regenerated when the tests are run. This should be set using the
    # set_regeneration() class-method. Can be initialized via the -w option.
    regenerate = {}

    # Dictionary describing default location for reference data, for
    # each kind. Can be initialized by set_default_data_location().
    default_data_locations = {}

    @classmethod
    def set_defaults(cls, **kwargs):
        """
        Set default parameters, at the class level. These defaults will
        apply to all instances of the class.

        The following parameters can be set:

            *verbose*:
                Sets the boolean verbose flag globally, to control
                reporting of errors while running tests. Reference
                tests tend to take longer to run than traditional
                unit tests, so it is often useful to be able to see
                information from failing tests as they happen, rather
                than waiting for the full report at the end. Verbose
                is set to ``True`` by default.

            *print_fn*:
                Sets the print function globally, to specify the
                function to use to display information while running
                tests.  The function should have the same signature
                as Python's *__future__* print function. If not
                specified, a default print function is used which
                writes unbuffered to sys.stdout.

            *tmp_dir*:
                Sets the tmp_dir property globally, to specify the
                directory where temporary files are written.
                Temporary files are created whenever a text file
                check fails and a 'preprocess' function has been
                specified. It's useful to be able to see the contents
                of the files after preprocessing has taken place,
                so preprocessed versions of the files are written
                to this directory, and their pathnames are included
                in the failure messages. If not explicitly set by
                :py:meth:`set_defaults()`, the environment variable
                *TDDA_FAIL_DIR* is used, or, if that is not defined,
                it defaults to */tmp*, *c:\\temp* or whatever
                py:func:`tempfile.gettempdir()` returns, as
                appropriate.

        """
        for k in kwargs:
            if k == 'verbose':
                cls.verbose = kwargs[k]
            elif k == 'print_fn':
                cls.print_fn = kwargs[k]
            elif k == 'tmp_dir':
                cls.tmp_dir = kwargs[k]
            else:
                raise Exception('set_defaults: Unrecogized option %s' % k)

    @classmethod
    def set_regeneration(cls, kind=None, regenerate=True):
        """
        Set the regeneration flag for a particular kind of reference file,
        globally, for all instances of the class.

        If the regenerate flag is set to True, then the framework will
        regenerate reference data of that kind, rather than comparing.

        All of the regeneration flags are set to False by default.
        """
        cls.regenerate[kind] = regenerate

    @classmethod
    def set_default_data_location(cls, location, kind=None):
        """
        Declare the default filesystem location for reference files of a
        particular kind. This sets the location globally, and will apply
        to all instances of the class.

        The instance method :py:meth:`set_data_location()` can be used to set
        the per-kind data locations for an individual instance of the class.

        If calls to :py:meth:`assertFileCorrect()` (etc) are made for
        kinds of reference data that hasn't had their location defined
        explicitly, then the
        default location is used. This is the location declared for
        the ``None`` *kind* and this default **must** be specified.

        If you haven't even defined the ``None`` default, and you make calls
        to :py:meth:`assertFileCorrect()` (etc) using relative pathnames for
        the reference data files, then it can't check correctness, so it will
        raise an exception.

        """
        cls.default_data_locations[kind] = os.path.normpath(location)

    def __init__(self, assert_fn):
        """
        Initializer for a ReferenceTest instance.

            *assert_fn*:
                Function to be used to make assertions for
                unit-tests. It should take two parameters:

                    - a value (which should evaluate as ``True`` for
                      the test to pass)
                    - a string (to report details of how a test
                      failed, if the value does not evaluate as ``True``).
        """
        self.assert_fn = assert_fn
        self.reference_data_locations = dict(self.default_data_locations)
        self.pandas = PandasComparison(print_fn=self.print_fn,
                                       verbose=self.verbose)
        self.files = FilesComparison(print_fn=self.print_fn,
                                     verbose=self.verbose,
                                     tmp_dir=self.tmp_dir)

    def set_data_location(self, location, kind=None):
        """
        Declare the filesystem location for reference files of a particular
        kind. Typically you would subclass ReferenceTestCase and pass in these
        locations though its __init__ method when constructing an instance
        of ReferenceTestCase as a superclass.

        If calls to :py:meth:`assertFileCorrect()` (etc) are made for
        kinds of reference data that hasn't had their location defined
        explicitly, then the
        default location is used. This is the location declared for
        the ``None`` *kind* and this default **must** be specified.

        This method overrides any global defaults set from calls to the
        set_default_data_location class-method.

        If you haven't even defined the ``None`` default, and you make calls
        to :py:meth:`assertFileCorrect()` (etc) using relative pathnames for
        the reference data files, then it can't check correctness, so it will
        raise an exception.

        """
        self.reference_data_locations[kind] = normalize_path(location)

    def assertDataFramesEqual(self, df, ref_df,
                              actual_path=None, expected_path=None,
                              check_data=None, check_types=None,
                              check_order=None, condition=None, sortby=None,
                              precision=None):
        """
        Check that an in-memory Pandas DataFrame matches an in-memory
        reference one.

            *df*:
                Actual DataFrame.

            *ref_df*:
                Expected DataFrame.

            *actual_path*:
                Optional parameter, giving path for file where
                actual DataFrame originated, used for error messages.

            *expected_path*:
                Optional parameter, giving path for file where
                expected DataFrame originated, used for error messages.

            *check_data*:
                Option to specify fields to compare values.

            *check_types*:
                Option to specify fields to compare types.

            *check_order*:
                Option to specify fields to compare field order.

            *check_extra_cols*:
                Option to specify fields in the actual dataset
                to use to check that there are no unexpected extra columns.

            *sortby*:
                Option to specify fields to sort by before comparing.

            *condition*:
                Filter to be applied to datasets before comparing.
                It can be ``None``, or can be a function that
                takes a DataFrame as its single parameter and
                returns a vector of booleans (to specify which rows
                should be compared).

            *precision*:
                Number of decimal places to compare float values.

        The ``check`` comparison flags can be of any of the following:

            - ``None`` (to apply that kind of comparison to all fields)
            - ``False`` (to skip that kind of comparison completely)
            - a list of field names
            - a function taking a DataFrame as its single parameter, and
              returning a list of field names to use.

        Raises :py:class:`NotImplementedError` if Pandas is not available.

        """
        r = self.pandas.check_dataframe(df, ref_df,
                                        actual_path=actual_path,
                                        expected_path=expected_path,
                                        check_data=check_data,
                                        check_types=check_types,
                                        check_order=check_order,
                                        condition=condition,
                                        sortby=sortby,
                                        precision=precision)
        (failures, msgs) = r
        self._check_failures(failures, msgs)

    def assertDataFrameCorrect(self, df, ref_csv, actual_path=None,
                               kind='csv', csv_read_fn=None,
                               check_data=None, check_types=None,
                               check_order=None, condition=None, sortby=None,
                               precision=None, **kwargs):
        """
        Check that an in-memory Pandas DataFrame matches a reference one
        from a saved reference CSV file.

            *df*:
                Actual DataFrame.

            *ref_csv*:
                Name of reference CSV file. The location of the
                reference file is determined by the configuration
                via :py:meth:`set_data_location()`.

            *actual_path*:
                Optional parameter, giving path for file where
                actual DataFrame originated, used for error
                messages.

            *kind*:
                Reference kind, used to locate the reference CSV file.

            *check_data*:
                Option to specify fields to compare values.

            *check_types*:
                Option to specify fields to compare types.

            *check_order*:
                Option to specify fields to compare field order.

            *check_extra_cols*:
                Option to specify fields in the actual dataset
                to use to check that there are no unexpected extra columns.

            *sortby*:
                Option to specify fields to sort by before comparing.

            *condition*:
                Filter to be applied to datasets before comparing.
                It can be ``None``, or can be a function that
                takes a DataFrame as its single parameter and
                returns a vector of booleans (to specify which
                rows should be compared).

            *precision*:
                Number of decimal places to compare float values.

            *loader*:
                Function to read a CSV file to obtain
                a pandas DataFrame. If ``None``, then a default
                CSV loader is used.

        The ``check`` comparison flags can be of any of the following:

            - ``None`` (to apply that kind of comparison to all fields)
            - ``False`` (to skip that kind of comparison completely)
            - a list of field names
            - a function taking a DataFrame as its single parameter, and
              returning a list of field names to use.

        The default CSV loader function is a wrapper around Pandas
        :py:func:`pd.read_csv()`, with default options as follows:

            - index_col             is ``None``
            - infer_datetime_format is ``True``
            - quotechar             is ""
            - quoting               is :py:const:`csv.QUOTE_MINIMAL`
            - escapechar            is \\\\ (backslash)
            - na_values             are the empty string, "NaN", and "NULL"
            - keep_default_na       is ``False``

        Raises :py:class:`NotImplementedError` if Pandas is not available.

        """
        expected_path = self._resolve_reference_path(ref_csv, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_file(actual_path, expected_path)
        else:
            ref_df = self.pandas.load_csv(expected_path, loader=csv_read_fn)
            self.assertDatasetsEqual(df, ref_df,
                                     actual_path=actual_path,
                                     expected_path=expected_path,
                                     check_data=check_data,
                                     check_types=check_types,
                                     check_order=check_order,
                                     condition=condition,
                                     sortby=sortby,
                                     precision=precision)

    def assertCSVFileCorrect(self, actual_path, ref_csv,
                             kind='csv', csv_read_fn=None,
                             check_data=None, check_types=None,
                             check_order=None, condition=None, sortby=None,
                             precision=None, **kwargs):
        """
        Check that a CSV file matches a reference one.

            *actual_path*:
                Actual CSV file.

            *ref_csv*:
                Name of reference CSV file. The location of the
                reference file is determined by the configuration
                via :py:meth:`set_data_location()`.

            *kind*:
                Reference *kind*, used to locate the reference CSV file.

            *csv_read_fn*:
                A function to read a CSV file to obtain
                a pandas DataFrame. If ``None``, then a default
                CSV loader is used, which takes the same
                parameters as the standard Pandas :py:func:`pd.read_csv()`
                function.

            *check_data*:
                Option to specify fields to compare values.

            *check_types*:
                Option to specify fields to compare types.

            *check_order*:
                Option to specify fields to compare field order.

            *check_extra_cols*:
                Option to specify fields in the actual dataset
                to use to check that there are no unexpected extra columns.

            *sortby*:
                Option to specify fields to sort by before comparing.

            *condition*:
                Filter to be applied to datasets before comparing.
                It can be ``None``, or can be a function that
                takes a DataFrame as its single parameter and
                returns a vector of booleans (to specify which
                rows should be compared).

            *precision*:
                Number of decimal places to compare float values.

            *\*\*kwargs*:
                Any additional named parameters are passed
                straight through to the *csv_read_fn* function.

        The ``check`` comparison flags can be of any of the following:

            - ``None`` (to apply that kind of comparison to all fields)
            - ``False`` (to skip that kind of comparison completely)
            - a list of field names
            - a function taking a DataFrame as its single parameter, and
              returning a list of field names to use.

        The default CSV loader function is a wrapper around Pandas
        :py:func:`pd.read_csv()`, with default options as follows:

            - index_col             is ``None``
            - infer_datetime_format is ``True``
            - quotechar             is ""
            - quoting               is :py:const:`csv.QUOTE_MINIMAL`
            - escapechar            is \\\\ (backslash)
            - na_values             are the empty string, "NaN", and "NULL"
            - keep_default_na       is ``False``

        Raises :py:class:`NotImplementedError` if Pandas is not available.

        """
        expected_path = self._resolve_reference_path(ref_csv, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_file(actual_path, expected_path)
        else:
            r = self.pandas.check_csv_file(actual_path, expected_path,
                                           check_types=check_types,
                                           check_order=check_order,
                                           condition=condition,
                                           sortby=sortby,
                                           precision=precision)
            (failures, msgs) = r
            self._check_failures(failures, msgs)

    def assertCSVFilesCorrect(self, actual_paths, ref_csvs,
                              kind='csv', csv_read_fn=None,
                              check_data=None, check_types=None,
                              check_order=None, condition=None, sortby=None,
                              precision=None, **kwargs):
        """
        Check that a set of CSV files match corresponding reference ones.

            *actual_paths*:
                List of actual CSV files.

            *ref_csvs*:
                List of names of matching reference CSV files. The
                location of the reference files is determined by
                the configuration via :py:meth:`set_data_location()`.

            *kind*:
                Reference *kind*, used to locate the reference CSV files.

            *csv_read_fn*:
                A function to read a CSV file to obtain
                a pandas DataFrame. If ``None``, then a default
                CSV loader is used, which takes the same
                parameters as the standard Pandas :py:func:`pd.read_csv()`
                function.

            *check_data*:
                Option to specify fields to compare values.

            *check_types*:
                Option to specify fields to compare types.

            *check_order*:
                Option to specify fields to compare field order.

            *check_extra_cols*:
                Option to specify fields in the actual dataset
                to use to check that there are no unexpected extra columns.

            *sortby*:
                Option to specify fields to sort by before comparing.

            *condition*:
                Filter to be applied to datasets before comparing.
                It can be ``None``, or can be a function that
                takes a DataFrame as its single parameter and
                returns a vector of booleans (to specify which
                rows should be compared).

            *precision*
                Number of decimal places to compare float values.

            *\*\*kwargs*:
                Any additional named parameters are passed
                straight through to the *csv_read_fn* function.

        The ``check`` comparison flags can be of any of the following:

            - ``None`` (to apply that kind of comparison to all fields)
            - ``False`` (to skip that kind of comparison completely)
            - a list of field names
            - a function taking a DataFrame as its single parameter, and
              returning a list of field names to use.

        The default CSV loader function is a wrapper around Pandas
        :py:func:`pd.read_csv()`, with default options as follows:

            - index_col             is ``None``
            - infer_datetime_format is ``True``
            - quotechar             is ""
            - quoting               is :py:const:`csv.QUOTE_MINIMAL`
            - escapechar            is \\\\ (backslash)
            - na_values             are the empty string, "NaN", and "NULL"
            - keep_default_na       is ``False``

        Raises :py:class:`NotImplementedError` if Pandas is not available.

        """
        expected_paths = self._resolve_reference_paths(ref_csvs, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_files(actual_paths, expected_paths)
        else:
            r = self.pandas.check_csv_files(actual_paths, expected_paths,
                                            check_types=check_types,
                                            check_order=check_order,
                                            condition=condition,
                                            sortby=sortby,
                                            precision=precision)
            (failures, msgs) = r
            self._check_failures(failures, msgs)

    def assertStringCorrect(self, string, ref_path, kind=None,
                            lstrip=False, rstrip=False,
                            ignore_substrings=None,
                            ignore_patterns=None, preprocess=None,
                            max_permutation_cases=0):
        """
        Check that an in-memory string matches the contents from a reference
        text file.

            *string*:
                The actual string.

            *ref_path*:
                The name of the reference file. The
                location of the reference file is
                determined by the configuration via
                :py:meth:`set_data_location()`.

            *kind*:
                The reference *kind*, used to locate the reference file.

            *lstrip*:
                If set to ``True``, both strings are
                left-stripped before the comparison is carried out.
                Note: the stripping is on a per-line basis.

            *rstrip*:
                If set to ``True``, both strings are
                right-stripped before the comparison is carried out.
                Note: the stripping is on a per-line basis.

            *ignore_substrings*:
                An optional list of substrings; lines
                containing any of these substrings will be
                ignored in the comparison.

            *ignore_patterns*:
                An optional list of regular expressions;
                lines will be considered to be the same if
                they only differ in substrings that match
                one of these regular expressions.
                The expressions must not contain parenthesised groups, and
                should only include explicit anchors if they
                need to refer to the whole line.

            *preprocess*:
                An optional function that takes a list of
                strings and preprocesses it in some way; this
                function will be applied to both the actual and expected.

            *max_permutation_cases*:
                An optional number specifying the maximum
                number of permutations allowed; if the actual
                and expected lists differ only in that their
                lines are permutations of each other, and
                the number of such permutations does not
                exceed this limit, then the two are considered to be identical.

        """
        expected_path = self._resolve_reference_path(ref_path, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_result(string, expected_path)
        else:
            ilc = ignore_substrings
            ip = ignore_patterns
            mpc = max_permutation_cases
            r = self.files.check_string_against_file(string, expected_path,
                                                     actual_path=None,
                                                     lstrip=lstrip,
                                                     rstrip=rstrip,
                                                     ignore_substrings=ilc,
                                                     ignore_patterns=ip,
                                                     preprocess=preprocess,
                                                     max_permutation_cases=mpc)
            (failures, msgs) = r
            self._check_failures(failures, msgs)

    def assertFileCorrect(self, actual_path, ref_path, kind=None,
                          lstrip=False, rstrip=False,
                          ignore_substrings=None,
                          ignore_patterns=None, preprocess=None,
                          max_permutation_cases=0):
        """
        Check that a file matches the contents from a reference text file.

            *actual_path*:
                A path for a text file.

            *ref_path*:
                The name of the reference file. The
                location of the reference file is determined by
                the configuration via
                :py:meth:`set_data_location()`.

            *kind*:
                The reference *kind*, used to locate the reference file.

            *lstrip*:
                If set to ``True``, lines are left-stripped
                before the comparison is carried out.

            *rstrip*:
                If set to ``True``, lines are right-stripped before
                the comparison is carried out.

            *ignore_substrings*:
                An optional list of substrings; lines
                containing any of these substrings will be
                ignored in the comparison.

            *ignore_patterns*:
                An optional list of regular expressions;
                lines will be considered to be the same if
                they only differ in substrings that match one
                of these regular expressions. The expressions
                must not contain parenthesised groups, and
                should only include explicit anchors if they
                need to refer to the whole line.

            *preprocess*:
                An optional function that takes a list of
                strings and preprocesses it in some way; this
                function will be applied to both the actual and expected.

            *max_permutation_cases*:
                An optional number specifying the maximum
                number of permutations allowed; if the actual
                and expected lists differ only in that their
                lines are permutations of each other, and
                the number of such permutations does not
                exceed this limit, then the two are considered to be identical.

        This should be used for unstructured data such as logfiles, etc.
        For CSV files, use :py:meth:`assertCSVFileCorrect` instead.

        """
        expected_path = self._resolve_reference_path(ref_path, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_file(actual_path, expected_path)
        else:
            mpc = max_permutation_cases
            r = self.files.check_file(actual_path, expected_path,
                                      lstrip=lstrip, rstrip=rstrip,
                                      ignore_substrings=ignore_substrings,
                                      ignore_patterns=ignore_patterns,
                                      preprocess=preprocess,
                                      max_permutation_cases=mpc)
            (failures, msgs) = r
            self._check_failures(failures, msgs)

    def assertFilesCorrect(self, actual_paths, ref_paths, kind=None,
                           lstrip=False, rstrip=False,
                           ignore_substrings=None,
                           ignore_patterns=None, preprocess=None,
                           max_permutation_cases=0):
        """
        Check that a collection of files matche the contents from
        matching collection of reference text files.

            *actual_paths*:
                A list of paths for text files.

            *ref_paths*:
                A list of names of the matching reference
                files.  The location of the reference files
                is determined by the configuration via
                :py:meth:`set_data_location()`.

            *kind*:
                The reference *kind*, used to locate the reference files.
                All the files must be of the same kind.

            *lstrip*:
                If set to ``True``, lines are left-stripped before
                the comparison is carried out.

            *rstrip*:
                If set to ``True``, lines are right-stripped before the
                comparison is carried out.

            *ignore_substrings*:
                An optional list of substrings; lines
                containing any of these substrings will be
                ignored in the comparison.

            *ignore_patterns*:
                An optional list of regular expressions;
                lines will be considered to be the same if
                they only differ in substrings that match one
                of these regular expressions. The expressions
                must not contain parenthesised groups, and
                should only include explicit anchors if they
                need to refer to the whole line.

            *preprocess*:
                An optional function that takes a list of
                strings and preprocesses it in some way; this
                function will be applied to both the actual
                and expected.

            *max_permutation_cases*:
                An optional number specifying the maximum
                number of permutations allowed; if the actual
                and expected lists differ only in that their
                lines are permutations of each other, and
                the number of such permutations does not
                exceed this limit, then the two are considered
                to be identical.

        This should be used for unstructured data such as logfiles, etc.
        For CSV files, use :py:meth:`assertCSVFileCorrect` instead.

        """
        expected_paths = self._resolve_reference_paths(ref_paths, kind=kind)
        if self._should_regenerate(kind):
            self._write_reference_files(actual_paths, expected_paths)
        else:
            mpc = max_permutation_cases
            r = self.files.check_files(actual_paths, expected_paths,
                                       lstrip=lstrip, rstrip=rstrip,
                                       ignore_substrings=ignore_substrings,
                                       ignore_patterns=ignore_patterns,
                                       preprocess=preprocess,
                                       max_permutation_cases=mpc)
            (failures, msgs) = r
            self._check_failures(failures, msgs)

    def _resolve_reference_path(self, path, kind=None):
        """
        Internal method for deciding where a reference data file should
        be looked for, if it has been specified using a relative path.
        """
        if self.reference_data_locations and not os.path.isabs(path):
            if kind not in self.reference_data_locations:
                kind = None
            if kind in self.reference_data_locations:
                path = os.path.join(self.reference_data_locations[kind], path)
            else:
                raise Exception('No reference data location for "%s"' % kind)
        return path

    def _resolve_reference_paths(self, paths, kind=None):
        """
        Internal method for resolving a list of reference data files,
        all of the same kind.
        """
        return [self._resolve_reference_path(p, kind=kind) for p in paths]

    def _should_regenerate(self, kind):
        """
        Internal method to determine if a particular kind of file
        should be regenerated.
        """
        if kind not in self.regenerate:
            kind = None
        return kind in self.regenerate and self.regenerate[kind]

    def _write_reference_file(self, actual_path, reference_path):
        """
        Internal method for regenerating reference data.
        """
        with open(actual_path) as fin:
            actual = fin.read()
        self._write_reference_result(actual, reference_path)

    def _write_reference_files(self, actual_paths, reference_paths):
        """
        Internal method for regenerating reference data for a list of
        files.
        """
        for (actual_path, expected_path) in zip(actual_paths, reference_paths):
            self._write_reference_file(actual_path, reference_path)

    def _write_reference_result(self, result, reference_path):
        """
        Internal method for regenerating reference data from in-memory
        results.
        """
        with open(reference_path, 'w') as fout:
            fout.write(result)
        if self.verbose and self.print_fn:
            self.print_fn('Written %s' % reference_path)

    def _check_failures(self, failures, msgs):
        """
        Internal method for check for failures and reporting them.
        """
        self.assert_fn(failures == 0, '\n'.join(msgs))

    @staticmethod
    def _default_print_fn(*args, **kwargs):
        # Sometimes the framework needs to print messages. By default, it
        # will use this print function, but you can override it by passing
        # in a print_fn parameter to __init__.
        print(*args, **kwargs)
        outfile = kwargs.get('file', sys.stdout)
        outfile.flush()

    # Default print function
    print_fn = _default_print_fn


# Magic so that an instance of this class can masquerade as a module,
# so that all of its methods can be made available as top-level functions,
# to work will with frameworks like pytest.
ReferenceTest.__all__ = dir(ReferenceTest)

