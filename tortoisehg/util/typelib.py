# typelib.py - A collection of type hint helpers
#
# Copyright 2020 Matt Harbison <mharbison72@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.


from __future__ import absolute_import

from mercurial import (
    pycompat,
)

if pycompat.TYPE_CHECKING:
    from typing import (
        TypeVar,
    )

    from mercurial import (
        config as config_mod,
    )

    from . import (
        wconfig,
    )

    IniConfig = TypeVar('IniConfig', wconfig._wconfig, config_mod.config)
