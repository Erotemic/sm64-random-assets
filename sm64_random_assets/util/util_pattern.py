#  type: ignore
"""
An encapsulation of regex and glob (and maybe other) patterns.

TODO:
    rectify with xdev / whatever package this goes in
"""
import os
import re
import fnmatch
import ubelt as ub
import pathlib

if hasattr(re, 'Pattern'):
    RE_Pattern = re.Pattern
else:
    # sys.version_info[0:2] <= 3.6
    RE_Pattern = type(re.compile('.*'))


class PatternBase:

    def match(self, text):
        raise NotImplementedError

    def search(self, text):
        raise NotImplementedError

    def sub(self, repl, text):
        raise NotImplementedError


# # TODO: wrapper for results of re and fnmatch
# class Match(ub.NiceRepr):
#     def __init__(self, string, pos, endpos):
#         self.string = string
#         self.pos = pos
#         self.endpos = endpos
#         self.lastgroup
#         self.lastindex
#     def span(self):
#         return (self.pos, self.endpos)
#     def __nice__(self):
#         return self.string
#     def __bool__(self):
#         return True


def _maybe_expandable_glob(pat):
    """
    Determine if a string might be a expandable glob pattern by looking for
    special glob characters: *, ? and [].

    Note:
        ! is also special, but always inside of a [] braket, so we dont need to
        check it.

    Returns:
        bool: if False then the input is 100% not an expandable glob pattern
            (although it could still be a glob pattern, but it is equivalant to
            strict matching). if True, then there are special glob characters
            in the string, but it is not guarenteed to be a valid glob pattern.
    """
    return ('*' in pat or '?' in pat or ('[' in pat and ']' in pat))


class Pattern(PatternBase, ub.NiceRepr):
    """
    Provides a common API to several common pattern matching syntaxes.

    A general patterns class, which can be strict, regex, or glob.

    Args:
        pattern (str | object):
            The pattern text or a precompiled backend pattern object

        backend (str):
            Code indicating what backend the pattern text should be
            interpereted with. Current modes are: strict, regex, and glob.

    Notes:
        The glob backend uses the :module:`fnmatch` module [fnmatch_docs]_.
        The regex backend uses the Python :module:`re` module.
        The strict backend uses the "==" string equality testing.

    References:
        ..[fnmatch_docs] https://docs.python.org/3/library/fnmatch.html

    Example:
        >>> repat = Pattern.coerce('foo.*', 'regex')
        >>> assert repat.match('foobar')
        >>> assert not repat.match('barfoo')
        >>> globpat = Pattern.coerce('foo*', 'glob')
        >>> assert globpat.match('foobar')
        >>> assert not globpat.match('barfoo')
        >>> globpat = Pattern.coerce('[foo|bar]', 'glob')
        >>> globpat.match('foo')
        >>> repat = Pattern.coerce('foo.*', 'regex')
        >>> match = repat.search('baz-biz-foobar')
        >>> match = repat.match('baz-biz-foobar')
    """

    def __init__(self, pattern, backend):
        if isinstance(pattern, pathlib.Path):
            pattern = os.fspath(pattern)
        if backend == 'regex':
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
        self.pattern = pattern
        self.backend = backend

    def __nice__(self) -> str:
        return '{}, {}'.format(self.pattern, self.backend)

    def to_regex(self):
        """
        Returns an equivalent pattern with the regular expression backend

        Example:
            >>> globpat = Pattern.coerce('foo*', 'glob')
            >>> strictpat = Pattern.coerce('foo*', 'strict')
            >>> repat1 = strictpat.to_regex()
            >>> repat2 = globpat.to_regex()
            >>> print(f'repat1={repat1}')
            >>> print(f'repat2={repat2}')
        """
        if self.backend == 'regex':
            regex_pattern = self.pattern
        elif self.backend == 'glob':
            regex_pattern = fnmatch.translate(self.pattern)
        elif self.backend == 'strict':
            regex_pattern = re.escape(self.pattern)
        else:
            raise AssertionError
        new = self.__class__(regex_pattern, 'regex')
        return new

    @classmethod
    def from_regex(cls, data, flags=0, multiline=False, dotall=False,
                   ignorecase=False):
        if multiline:
            flags |= re.MULTILINE
        if dotall:
            flags |= re.DOTALL
        if multiline:
            flags |= re.DOTALL
        if ignorecase:
            flags |= re.IGNORECASE
        pat = re.compile(data, flags=flags)
        self = cls(pat, 'regex')
        return self

    @classmethod
    def from_glob(cls, data):
        self = cls(data, 'glob')
        return self

    @classmethod
    def coerce_backend(cls, data, hint='auto'):
        """
        Example:
            >>> assert Pattern.coerce_backend('foo', hint='auto') == 'strict'
            >>> assert Pattern.coerce_backend('foo*', hint='auto') == 'glob'
            >>> assert Pattern.coerce_backend(re.compile('foo*'), hint='auto') == 'regex'
        """
        if isinstance(data, RE_Pattern):
            backend = 'regex'
        elif isinstance(data, cls) or type(data).__name__ == cls.__name__:
            backend = data.backend
        else:
            if hint == 'auto':
                hint = 'glob'
                if isinstance(data, str):
                    if not _maybe_expandable_glob(data):
                        hint = 'strict'
            backend = hint
        return backend

    def match(self, text):
        if self.backend == 'regex':
            return self.pattern.match(text)
        elif self.backend == 'glob':
            return fnmatch.fnmatch(text, self.pattern)
        elif self.backend == 'strict':
            return self.pattern == text
        else:
            raise KeyError(self.backend)

    def search(self, text):
        if self.backend == 'regex':
            return self.pattern.search(text)
        elif self.backend == 'glob':
            return fnmatch.fnmatch(text, '*{}*'.format(self.pattern))
        elif self.backend == 'strict':
            return self.pattern in text
        else:
            raise KeyError(self.backend)

    def sub(self, repl, text):
        if self.backend == 'regex':
            return self.pattern.sub(repl, text)
        elif self.backend == 'glob':
            raise NotImplementedError
        elif self.backend == 'strict':
            return text.replace(self.pattern, repl)
        else:
            raise KeyError(self.backend)

    @classmethod
    def coerce(cls, data, hint='auto'):
        """
        Example:
            >>> pat = Pattern.coerce('foo*', 'glob')
            >>> pat2 = Pattern.coerce(pat, 'regex')
            >>> print('pat = {}'.format(ub.urepr(pat, nl=1)))
            >>> print('pat2 = {}'.format(ub.urepr(pat2, nl=1)))

            Pattern.coerce(['a', 'b', 'c'])
        """
        if isinstance(data, cls) or type(data).__name__ == cls.__name__:
            self = data
        else:
            # string
            backend = cls.coerce_backend(data, hint=hint)
            self = cls(data, backend)
        return self

    def paths(self, cwd=None, recursive=False):
        """
        Find paths in the filesystem that match this pattern

        Yields:
            ub.Path
        """
        from ubelt.util_path import ChDir
        if self.backend == 'glob':
            import glob
            with ChDir(cwd):
                yield from map(ub.Path, glob.glob(
                    self.pattern, recursive=recursive))
        elif self.backend == 'strict':
            with ChDir(cwd):
                p  = ub.Path(self.pattern)
                if p.exists():
                    yield p
        else:
            raise NotImplementedError


class MultiPattern(PatternBase, ub.NiceRepr):
    """
    Example:
        >>> dpath = ub.Path.appdir('xdev/tests/multipattern_paths').ensuredir().delete().ensuredir()
        >>> (dpath / 'file0.txt').touch()
        >>> (dpath / 'data0.dat').touch()
        >>> (dpath / 'other0.txt').touch()
        >>> ((dpath / 'dir1').ensuredir() / 'file1.txt').touch()
        >>> ((dpath / 'dir2').ensuredir() / 'file2.txt').touch()
        >>> ((dpath / 'dir2').ensuredir() / 'file3.txt').touch()
        >>> ((dpath / 'dir1').ensuredir() / 'data.dat').touch()
        >>> ((dpath / 'dir2').ensuredir() / 'data.dat').touch()
        >>> ((dpath / 'dir2').ensuredir() / 'data.dat').touch()
        >>> pat = MultiPattern.coerce(['*.txt'], 'glob')
        >>> print(list(pat.paths(cwd=dpath)))
        >>> pat = MultiPattern.coerce(['*0*', '**/*.txt'], 'glob')
        >>> print(list(pat.paths(cwd=dpath, recursive=1)))
        >>> pat = MultiPattern.coerce(['*.txt', '**/*.txt', '**/*.dat'], 'glob')
        >>> print(list(pat.paths(cwd=dpath)))
    """

    def __init__(self, patterns, predicate):
        self.predicate = predicate
        self.patterns = patterns

    def __nice__(self):
        return f'{self.predicate.__name__}({[str(p) for p in self.patterns]})'

    def match(self, text):
        return self.predicate(p.match(text) for p in self.patterns)

    def paths(self, cwd=None, recursive=False):
        groups = (p.paths(cwd=cwd, recursive=recursive) for p in self.patterns)
        if self.predicate in {any}:  # all}:
            yield from ub.unique(ub.flatten(groups))
        elif self.predicate in {all}:  # all}:
            yield from set.intersection(*map(set, groups))
        else:
            raise NotImplementedError

    # def search(self, text):
    #     return self.predicate(p.search(text) for p in self.patterns)

    def _squeeze(self):
        if self.predicate in {any, all}:
            if len(self.patterns) == 1:
                new = self.patterns[0]
            else:
                new = self
        else:
            raise NotImplementedError
        return new

    @classmethod
    def coerce(cls, data, hint='auto', predicate='any'):
        """
        Args:
            data (str | List | Pattern | PathLike | MultiPattern)

            hint (str):
                can be 'glob', 'regex', 'strict' or 'auto'. In 'auto' we will
                use 'glob' if the input is a string and '*' is in the pattern,
                otherwise we will use strict. Pattern inputs keep their
                existing interpretation.

        Example:
            >>> pat = MultiPattern.coerce('foo*', 'glob')
            >>> pat2 = MultiPattern.coerce(pat, 'regex')
            >>> pat3 = MultiPattern.coerce([pat, pat], 'regex')
            >>> pat4 = MultiPattern.coerce([ub.Path('bar*'), pat], 'regex')
            >>> print('pat = {}'.format(ub.urepr(pat, nl=1)))
            >>> print('pat2 = {}'.format(ub.urepr(pat2, nl=1)))
            >>> print('pat3 = {!r}'.format(pat3))
            >>> print('pat4 = {!r}'.format(pat4))

            >>> pat00 = MultiPattern.coerce('foo', 'glob')
            >>> pat01 = MultiPattern.coerce('foo*', 'glob')
            >>> pat02 = MultiPattern.coerce('foo*', 'regex')
            >>> pat5 = MultiPattern.coerce(['foo', 'foo*', pat, pat00, pat01, pat02])
            >>> print(f'pat5={pat5}')

        Example:
            >>> # Test all acceptable input types
            >>> import itertools as it
            >>> str_pat = 'pattern*'
            >>> scalar_inputs = {
            >>>     'str': str_pat,
            >>>     'path': ub.Path(str_pat),
            >>>     'pat': Pattern.coerce(str_pat),
            >>>     'mpat': MultiPattern.coerce(str_pat)
            >>> }
            >>> # Test scalar input types
            >>> scalar_outputs = {}
            >>> for k, v in scalar_inputs.items():
            >>>     scalar_outputs[k] = MultiPattern.coerce(v)
            >>> print('scalar_outputs = {}'.format(ub.urepr(scalar_outputs, nl=1)))
            >>> #
            >>> # Test iterable input types
            >>> multi_outputs = []
            >>> for v in it.combinations(scalar_inputs.values(), 2):
            >>>     multi_outputs.append(MultiPattern.coerce(v))
            >>> for v in it.combinations(scalar_inputs.values(), 3):
            >>>     multi_outputs.append(MultiPattern.coerce(v))
            >>> # Higher order nesting test
            >>> higher_order_output = MultiPattern.coerce(multi_outputs)
            >>> print('higher_order_output = {}'.format(ub.urepr(higher_order_output, nl=1)))
        """
        if isinstance(data, cls) or type(data).__name__ == cls.__name__:
            self = data
        else:
            # coerce predicate
            if predicate == 'any':
                predicate = any
            else:
                raise NotImplementedError
            if isinstance(data, (str, os.PathLike, Pattern)):
                backend = Pattern.coerce_backend(data, hint=hint)
                pat = Pattern.coerce(data, backend)
                patterns = [pat]
                self = MultiPattern(patterns, predicate)
            else:
                self = MultiPattern([
                    MultiPattern.coerce(d, hint)._squeeze()
                    for d in data], predicate)
        return self
