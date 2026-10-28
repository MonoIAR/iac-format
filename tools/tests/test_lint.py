"""Unit tests for the reference IAC implementation.

    python -m unittest discover -s tools/tests -v

These test the behaviour the specification promises; testdata/conformance.json
tests the error taxonomy. Both must pass before a release.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iac_lint import (  # noqa: E402
    fmt_time,
    from_srt,
    migrate_text,
    parse_text,
    render_canonical,
    split_top_level,
)

GOOD = 'VO_1 : {"Hello"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'


class TestSeparator(unittest.TestCase):
    def test_colon_inside_text_does_not_split(self):
        line = 'VO_1 : {"Chapter : The Fall"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.errors, [])
        self.assertEqual(len(doc.records), 1)
        self.assertEqual(doc.records[0].entries[0].text, "Chapter : The Fall")

    def test_braces_inside_text_do_not_break_depth(self):
        line = 'VO_1 : {"a { b } c"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.errors, [])
        self.assertEqual(doc.records[0].entries[0].text, "a { b } c")

    def test_commas_inside_text_do_not_split_entries(self):
        line = 'VO_1 : {"one, two, three"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual(len(doc.records[0].entries), 1)
        self.assertEqual(doc.records[0].entries[0].text, "one, two, three")

    def test_scanner_distinguishes_quote_from_brace_damage(self):
        _parts, state = split_top_level('a : {b : c', ":")
        self.assertEqual(state, "unbalanced")
        _parts, state = split_top_level('a : {"b : c', ":")
        self.assertEqual(state, "quote")
        _parts, state = split_top_level('a : {"b"} : c', ":")
        self.assertEqual(state, "ok")

    def test_unterminated_quote_is_e010(self):
        line = 'VO_1 : {"unclosed|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E010"})


class TestEscapes(unittest.TestCase):
    def test_escaped_quote_round_trips(self):
        line = r'VO_1 : {"say \"hi\""|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.errors, [])
        entry = doc.records[0].entries[0]
        self.assertEqual(entry.text, 'say "hi"')
        self.assertIn(r'\"hi\"', render_canonical(doc))

    def test_backslash_round_trips(self):
        line = r'VO_1 : {"C:\\Games"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.records[0].entries[0].text, r"C:\Games")

    def test_unknown_escape_is_rejected(self):
        line = r'VO_1 : {"a\nb"|00:00:01:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E011"})


class TestTime(unittest.TestCase):
    def test_half_open_adjacency_is_not_overlap(self):
        line = (
            'VO_1 : {"a"|00:00:01:00-00:00:02:00|, "b"|00:00:02:00-00:00:03:00|}'
            " : [#FFFFFF]"
        )
        doc = parse_text(line + "\n")
        self.assertEqual(doc.diagnostics, [])

    def test_true_overlap_warns(self):
        line = (
            'VO_1 : {"a"|00:00:01:00-00:00:03:00|, "b"|00:00:02:00-00:00:04:00|}'
            " : [#FFFFFF]"
        )
        doc = parse_text(line + "\n")
        self.assertEqual([d.code for d in doc.warnings], ["W002"])

    def test_stop_must_exceed_start(self):
        line = 'VO_1 : {"a"|00:00:02:00-00:00:02:00|} : [#FFFFFF]'
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E018"})

    def test_time_format_round_trip(self):
        self.assertEqual(fmt_time(12345), "00:02:03:45")
        self.assertEqual(fmt_time(0), "00:00:00:00")


class TestStructure(unittest.TestCase):
    def test_duplicate_name_is_error(self):
        doc = parse_text(GOOD + "\n" + GOOD + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E015"})

    def test_unsorted_entries_is_error(self):
        line = (
            'VO_1 : {"b"|00:00:05:00-00:00:06:00|, "a"|00:00:01:00-00:00:02:00|}'
            " : [#FFFFFF]"
        )
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E019"})

    def test_version_major_is_enforced(self):
        doc = parse_text("#!iac 2.0\n" + GOOD + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E024"})

    def test_unknown_type_is_warning_not_error(self):
        line = 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : Battle'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.errors, [])
        self.assertEqual([d.code for d in doc.warnings], ["W005"])

    def test_default_type_is_voice(self):
        doc = parse_text(GOOD + "\n")
        self.assertEqual(doc.records[0].type, "Voice")

    def test_type_is_the_fourth_field(self):
        line = 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : Music'
        doc = parse_text(line + "\n")
        self.assertEqual(doc.errors, [])
        self.assertEqual(doc.records[0].type, "Music")

    def test_three_fields_is_the_whole_record(self):
        doc = parse_text(GOOD + "\n")
        self.assertEqual(len(doc.records[0].render().split(" : ")), 3)


class TestFieldCount(unittest.TestCase):
    def test_two_fields_is_e012(self):
        doc = parse_text('VO_1 : {"a"|00:00:01:00-00:00:02:00|}\n')
        self.assertEqual({d.code for d in doc.errors}, {"E012"})

    def test_five_fields_is_e012(self):
        line = 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : Music : Extra'
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E012"})

    def test_trailing_content_after_type_is_e027(self):
        line = 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : Music extra'
        doc = parse_text(line + "\n")
        self.assertEqual({d.code for d in doc.errors}, {"E027"})


class TestRetiredRecords(unittest.TestCase):
    RETIRED = '#!cut VO_2 : {"Deleted."|00:00:01:00-00:00:02:00|} : [#FFFFFF]'

    def test_cut_line_is_not_a_record(self):
        doc = parse_text(GOOD + "\n" + self.RETIRED + "\n")
        self.assertEqual(doc.diagnostics, [])
        self.assertEqual(len(doc.records), 1)
        self.assertEqual(doc.records[0].name, "VO_1")

    def test_cut_line_does_not_raise_duplicate_name(self):
        doc = parse_text(GOOD + "\n" + '#!cut VO_1 : {"Old."|00:00:01:00-00:00:02:00|} : [#FFFFFF]\n')
        self.assertEqual(doc.errors, [])

    def test_broken_cut_line_is_w008(self):
        doc = parse_text('#!cut VO_1 : {"Hi"|00:00:00-00:00:01:00|} : [#FFFFFF]\n')
        self.assertEqual(doc.errors, [])
        self.assertEqual([d.code for d in doc.warnings], ["W008"])

    def test_bare_marker_is_an_ordinary_comment(self):
        # §5.4: `#!cut` without the SPACE is an ordinary comment.
        doc = parse_text("#!cut\n" + GOOD + "\n")
        self.assertEqual(doc.diagnostics, [])
        self.assertEqual(len(doc.records), 1)

    def test_non_canonical_but_valid_payload_warns_w004_not_w008(self):
        text = '#!cut VO_2 : {"a"|00:00:01:00-00:00:02:00|,"b"|00:00:03:00-00:00:04:00|} : [#FFFFFF]\n'
        doc = parse_text(text)
        self.assertEqual(doc.errors, [])
        self.assertEqual([d.code for d in doc.warnings], ["W004"])

    def test_formatter_preserves_and_canonicalises_cut_lines(self):
        # A retired record must itself be valid; non-canonical spacing is a
        # warning, so the formatter still rewrites it in canonical form.
        text = '#!cut VO_2 : {"a"|00:00:01:00-00:00:02:00|,"b"|00:00:05:00-00:00:06:00|} : [#FFFFFF] : Voice\n'
        out = render_canonical(parse_text(text))
        self.assertTrue(out.startswith("#!cut VO_2 : "))
        self.assertIn('"a"|00:00:01:00-00:00:02:00|, "b"|00:00:05:00-00:00:06:00|', out)
        self.assertNotIn(" : Voice", out)


class TestCanonicalForm(unittest.TestCase):
    def test_formatter_is_idempotent(self):
        messy = (
            "# a comment\n"
            "\n"
            'VO_1 : {"b"|00:00:05:00-00:00:06:00|,"a"|00:00:01:00-00:00:02:00|}'
            " : [#ffffff] : Voice\n"
        )
        once = render_canonical(parse_text(messy))
        twice = render_canonical(parse_text(once))
        self.assertEqual(once, twice)
        self.assertIn('"a"|00:00:01:00-00:00:02:00|, "b"|00:00:05:00-00:00:06:00|', once)
        self.assertNotIn(" : Voice", once)

    def test_comments_are_preserved(self):
        text = "# header\n" + GOOD + "\n# trailer\n"
        out = render_canonical(parse_text(text))
        self.assertIn("# header", out)
        self.assertIn("# trailer", out)


class TestMigration(unittest.TestCase):
    def test_true_is_dropped(self):
        new, changed = migrate_text('VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : true\n')
        self.assertEqual(changed, 1)
        self.assertEqual(new, 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF]\n')

    def test_false_becomes_cut(self):
        new, changed = migrate_text('VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : false\n')
        self.assertEqual(changed, 1)
        self.assertTrue(new.startswith("#!cut VO_1 : "))

    def test_five_field_becomes_four(self):
        new, _changed = migrate_text(
            'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : true : Music\n'
        )
        self.assertEqual(new, 'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : Music\n')

    def test_false_with_type_becomes_cut_with_type(self):
        new, _changed = migrate_text(
            'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : false : Music\n'
        )
        self.assertTrue(new.startswith("#!cut VO_1 : "))
        self.assertTrue(new.rstrip().endswith(": Music"))

    def test_migration_is_idempotent(self):
        once, _ = migrate_text('VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : true\n')
        twice, changed = migrate_text(once)
        self.assertEqual(changed, 0)
        self.assertEqual(once, twice)

    def test_migrated_output_parses(self):
        legacy = (
            'VO_1 : {"a"|00:00:01:00-00:00:02:00|} : [#FFFFFF] : true\n'
            'VO_2 : {"b"|00:00:03:00-00:00:04:00|} : [#FFFFFF] : false : Music\n'
        )
        new, changed = migrate_text(legacy)
        self.assertEqual(changed, 2)
        doc = parse_text(new)
        self.assertEqual(doc.errors, [])
        self.assertEqual(len(doc.records), 1)
        self.assertEqual(doc.records[0].type, "Voice")


class TestSrtImport(unittest.TestCase):
    SRT = (
        "1\n"
        "00:00:01,000 --> 00:00:02,500\n"
        "First line\n"
        "\n"
        "2\n"
        "00:00:03,000 --> 00:00:04,000\n"
        "Second line\n"
    )

    def test_cue_count_and_timing(self):
        record = from_srt(self.SRT, "test")
        self.assertEqual(len(record.entries), 2)
        self.assertEqual(record.entries[0].start, 100)
        self.assertEqual(record.entries[0].stop, 250)
        self.assertEqual(record.entries[1].start, 300)

    def test_multiline_cue_is_joined(self):
        srt = "1\n00:00:01,000 --> 00:00:02,000\nline one\nline two\n"
        record = from_srt(srt, "test")
        self.assertEqual(record.entries[0].text, "line one line two")

    def test_exported_record_parses_clean(self):
        record = from_srt(self.SRT, "test")
        doc = parse_text("#!iac 1.0\n" + record.render() + "\n")
        self.assertEqual(doc.errors, [])
        self.assertEqual(len(doc.records[0].entries), 2)


if __name__ == "__main__":
    unittest.main()
