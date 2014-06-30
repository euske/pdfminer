#
# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 science+computing ag
#  Author: Anselm Kruis <a.kruis@science-computing.de>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from __future__ import absolute_import, print_function, division

import icu_bidi

IDM_CHARACTERS = u"\u200E\u200F\u061C"  # LRM, RLM, ALM


def reorder_text_line(objs, bidi_level, add_directional_marks,
                      annotation_factory, set_text_function):
    """Use the inverse Unicode birirectional algorithm

    to reorder a line from visual order to logical order.
    """
    if not objs:
        return objs[:]

    bidi_level &= 0xff
    if bidi_level not in (icu_bidi.UBiDiLevel.UBIDI_DEFAULT_LTR,
                          icu_bidi.UBiDiLevel.UBIDI_DEFAULT_RTL):
        if (bidi_level < 0 or
            bidi_level > icu_bidi.UBiDiLevel.UBIDI_MAX_EXPLICIT_LEVEL):
            return objs[:]

    objs_in_logical_order = []

    bidi = icu_bidi.Bidi()
    bidi.reordering_mode = icu_bidi.UBiDiReorderingMode.UBIDI_REORDER_INVERSE_LIKE_DIRECT
    if add_directional_marks:
        bidi.reordering_options = icu_bidi.UBiDiReorderingOption.UBIDI_OPTION_INSERT_MARKS

    visual_text2obj = []
    visual_text = []
    for i, obj in enumerate(objs):
        text = obj.get_text()
        visual_text.append(text)
        visual_text2obj.extend((i,) * len(text))
    visual_text = u"".join(visual_text)

    bidi.set_para(visual_text, bidi_level)
    logical_text = bidi.get_reordered(icu_bidi.UBidiWriteReorderedOpt.UBIDI_DO_MIRRORING |
                                      icu_bidi.UBidiWriteReorderedOpt.UBIDI_KEEP_BASE_COMBINING)
    logical_text_length = len(logical_text)
    index_logical = 0
    index_obj = None
    obj_text = []
    n_runs = bidi.count_runs()
    oids = set(xrange(len(objs)))

    def advance(old_iobj, new_iobj, char):
        if old_iobj != new_iobj or char is None:
            t = u"".join(obj_text)
            del obj_text[:]
            if old_iobj is None:
                if t:
                    objs_in_logical_order.append(annotation_factory(t))
            else:
                obj = objs[old_iobj]
                set_text_function(obj, t)
                objs_in_logical_order.append(obj)
            if new_iobj is not None:
                oids.remove(new_iobj)  # raises KeyError in case of an error
        if char is not None:
            obj_text.append(char)
        return new_iobj

    for index_run in range(n_runs):
        direction, start, length = bidi.get_visual_run(index_run)
        if direction:
            run_visual_indices = range(start + length - 1, start - 1, -1)
        else:
            run_visual_indices = range(start, start + length)

        for index_visual in run_visual_indices:
            # skip implicit directory marks added by the bidi algorithm
            while index_logical < logical_text_length:
                c = logical_text[index_logical]
                if c not in IDM_CHARACTERS:
                    break
                index_obj = advance(index_obj, None, c)
                index_logical += 1

            # get the index of the visual object
            index_obj = advance(index_obj, visual_text2obj[index_visual], c)
            index_logical += 1
    # skip implicit directory marks added by the bidi algorithm
    while index_logical < logical_text_length:
        c = logical_text[index_logical]
        assert c in IDM_CHARACTERS
        index_obj = advance(index_obj, None, c)
        index_logical += 1
    advance(index_obj, None, None)
    assert len(oids) == 0

    return objs_in_logical_order
