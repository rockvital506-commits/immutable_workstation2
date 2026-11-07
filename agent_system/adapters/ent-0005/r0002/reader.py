#!/usr/bin/env python3
"""Linux x86-64 bounded artifact reader, not catalog admission or export."""
import ctypes
import copy
import hashlib
import os
from pathlib import Path
import platform
import re
import stat


class ReadBlocked(Exception):
    """Stable code only: never copy private paths, link targets or contents."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


class _OpenHow(ctypes.Structure):
    _fields_ = [('flags', ctypes.c_uint64), ('mode', ctypes.c_uint64),
                ('resolve', ctypes.c_uint64)]


def _fingerprint(fd):
    s = os.fstat(fd)
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns)


def _open_node(rootfd, parts):
    # Linux x86-64 syscall number; never guess on other architectures.
    how = _OpenHow(os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, 0, 0x01 | 0x04 | 0x08)
    # NO_XDEV | NO_SYMLINKS | BENEATH; final O_PATH|NOFOLLOW may return a link fd.
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(437, rootfd, os.fsencode('/'.join(parts) or '.'),
                          ctypes.byref(how), ctypes.sizeof(how))
    if result < 0:
        raise ReadBlocked('PATH_UNAVAILABLE_OR_UNSAFE')
    return result


def _read_data(fd, maximum):
    # Reopen the already-pinned, type-checked regular inode, not a source pathname.
    try:
        readfd = os.open('/proc/self/fd/' + str(fd), os.O_RDONLY | os.O_CLOEXEC)
    except OSError:
        raise ReadBlocked('READ_UNAVAILABLE') from None
    try:
        if _fingerprint(readfd) != _fingerprint(fd):
            raise ReadBlocked('INPUT_CHANGED')
        chunks = []
        count = 0
        while True:
            chunk = os.read(readfd, min(65536, maximum + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > maximum:
                raise ReadBlocked('BYTE_LIMIT')
        return b''.join(chunks)
    finally:
        os.close(readfd)


def _logical_parts(path):
    if (not isinstance(path, str) or not path or path.startswith('/')
            or '\\' in path or ':' in path
            or any(ord(c) < 32 or ord(c) == 127 for c in path)
            or any(p in ('', '.', '..') for p in path.split('/'))):
        raise ReadBlocked('INVALID_LOGICAL_PATH')
    return path.split('/')


def _resolve(rootfd, physical, pending, opened, maxlinks, maxsteps):
    prefix = []
    links = []
    seen = set()
    steps = 0
    while pending:
        steps += 1
        if steps > maxsteps:
            raise ReadBlocked('STEP_LIMIT')
        state = (tuple(prefix), tuple(pending))
        if state in seen:
            raise ReadBlocked('LINK_CYCLE')
        seen.add(state)
        part, pending = pending[0], pending[1:]
        if part in ('', '.'):
            continue
        if part == '..':
            if not prefix:
                raise ReadBlocked('OUTSIDE_ROOT')
            prefix.pop()
            continue
        parts = prefix + [part]
        fd = _open_node(rootfd, parts)
        opened.append((fd, _fingerprint(fd)))
        mode = os.fstat(fd).st_mode
        if stat.S_ISLNK(mode):
            if len(links) >= maxlinks:
                raise ReadBlocked('LINK_LIMIT')
            # Empty-path readlink reads the pinned symlink inode, not a racy name.
            target = os.readlink('', dir_fd=fd)
            links.append({'path': '/'.join(parts), 'link_type': 'symbolic_link',
                          'target': target})
            if target.startswith('/'):
                # Do not normalize '..' or resolve an external path and return inside.
                boundary = physical.rstrip('/') + '/'
                if target == physical:
                    remainder = ''
                elif target.startswith(boundary):
                    remainder = target[len(boundary):]
                else:
                    raise ReadBlocked('OUTSIDE_ROOT')
                prefix = []
                pending = remainder.split('/') + pending
            else:
                pending = target.split('/') + pending
            continue
        prefix.append(part)
        if pending and not stat.S_ISDIR(mode):
            raise ReadBlocked('NOT_A_DIRECTORY')
        if not pending:
            if not stat.S_ISREG(mode):
                raise ReadBlocked('NOT_A_REGULAR_FILE')
            return fd, links, '/'.join(prefix)
    raise ReadBlocked('NOT_A_REGULAR_FILE')


def _freeze_expected(expected, path):
    if not isinstance(expected, dict):
        raise ReadBlocked('EXPECTED_REQUIRED')
    expected = copy.deepcopy(expected)
    role = expected.pop('role', None)
    if role is not None and (not isinstance(role, str) or not role):
        raise ReadBlocked('INVALID_EXPECTED')
    mandatory = {'path', 'sha256', 'size_bytes'}
    if not mandatory.issubset(expected) or set(expected) - mandatory - {'links', 'resolved_path'}:
        raise ReadBlocked('INVALID_EXPECTED')
    if (expected['path'] != path or not isinstance(expected['sha256'], str)
            or re.fullmatch('[0-9a-f]{64}', expected['sha256']) is None
            or type(expected['size_bytes']) is not int or expected['size_bytes'] < 0):
        raise ReadBlocked('INVALID_EXPECTED')
    if ('links' in expected) != ('resolved_path' in expected):
        raise ReadBlocked('INVALID_EXPECTED')
    if 'links' in expected:
        _logical_parts(expected['resolved_path'])
        if not isinstance(expected['links'], list) or not expected['links']:
            raise ReadBlocked('INVALID_EXPECTED')
        for link in expected['links']:
            if (not isinstance(link, dict) or set(link) != {'path', 'link_type', 'target'}
                    or link['link_type'] != 'symbolic_link'
                    or not isinstance(link['target'], str) or not link['target']):
                raise ReadBlocked('INVALID_EXPECTED')
            _logical_parts(link['path'])
    return expected


def read_artifact(root, path, expected, *, max_bytes=16 * 1024 * 1024,
                  max_links=40, max_steps=1024):
    """Return (bytes, artifact metadata); no execution, traversal, export or writes.

    Requires a trusted local Linux namespace without privileged mount/proc/clock
    manipulation. Expected artifacts are mandatory and frozen before reading.
    Detected mutation aborts; unobserved changes or a tree-wide snapshot are NOT
    guaranteed. Returns only the verified bytes and artifact tuple, not admission.
    """
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise ReadBlocked('UNSUPPORTED_PLATFORM')
    if any(type(v) is not int or v < 1 for v in (max_bytes, max_links, max_steps)):
        raise ReadBlocked('INVALID_LIMIT')
    parts = _logical_parts(path)
    expected = _freeze_expected(expected, path)
    opened = []
    try:
        physical = os.path.realpath(root, strict=True)
        rootfd = os.open(physical, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        opened.append((rootfd, _fingerprint(rootfd)))
        if os.readlink('/proc/self/fd/' + str(rootfd)) != physical:
            raise ReadBlocked('ROOT_CHANGED')
        fd, links, resolved = _resolve(rootfd, physical, parts, opened, max_links, max_steps)
        if os.fstat(fd).st_size > max_bytes:
            raise ReadBlocked('BYTE_LIMIT')
        data = _read_data(fd, max_bytes)
        # Re-resolve from the pinned root and verify path-to-inode mapping as well
        # as every retained directory/link/file inode and metadata fingerprint.
        fd2, links2, resolved2 = _resolve(rootfd, physical, parts, opened, max_links, max_steps)
        if (links2 != links or resolved2 != resolved
                or _fingerprint(fd2) != _fingerprint(fd)):
            raise ReadBlocked('INPUT_CHANGED')
        if os.readlink('/proc/self/fd/' + str(rootfd)) != physical:
            raise ReadBlocked('ROOT_CHANGED')
        if any(_fingerprint(f) != before for f, before in opened):
            raise ReadBlocked('INPUT_CHANGED')
        record = {'path': path, 'sha256': hashlib.sha256(data).hexdigest(),
                  'size_bytes': len(data)}
        if links:
            record.update(links=links, resolved_path=resolved)
        if expected != record:
            raise ReadBlocked('ARTIFACT_MISMATCH')
        return data, record
    except ReadBlocked:
        raise
    except (OSError, ValueError, TypeError, RuntimeError):
        raise ReadBlocked('INPUT_UNAVAILABLE') from None
    finally:
        for fd, _ in reversed(opened):
            os.close(fd)
