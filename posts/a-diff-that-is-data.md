# A diff that is data

*Thomas Sawyer · 15 November 2026*

A unified diff tells you where a change goes by line number. The line
numbers are right for exactly one version of the file, the one the diff
was made from, and every tool that applies a diff to any other version
is guessing: it slides the hunk up and down looking for context that
matches, and it calls the guess "fuzz". The thing an edit actually knows
is not a position. It is the text around the change.

C0DIFF is a diff format that writes down only that. It is a profile of
C0DATA, the control-code data format from the two earlier posts: an
ordinary document whose heading says it is a diff, read by any C0DATA
parser as data and by a diff tool as an edit. Here is one that changes
one word in one file.

    ␖␁shape␟diff
    ␜greeting.txt
    ␞␂Hello ␃␟world␚␟universe␟!
    ␄

Read it with the chart from the last post. SYN starts the document, and
the heading says `shape` is `diff`. FS begins a file, and the name after
it is the path. RS begins a record, and the record's units, divided by
US, are the pattern: `Hello ` (in text fences, because it ends in a
space), then `world`, then `!`. The one new thing is in the middle unit.
`world` is followed by SUB and US and `universe`: a sub-unit, an element
that stands under the unit before it. In a diff the unit is what the file
holds and the sub-unit is what it will hold. Find `Hello world!`, once,
and replace `world` with `universe`.

## Nothing here is special

The last post said SUB, "substitute", sits between an old value and its
new one in C0DIFF. That was true and it was not the whole rule. The base
format gives SUB one meaning: in front of a separator, it makes the
element after subordinate to the element before, at that separator's
grain. In front of GS it makes a subsection, `␝Chapter 1␚␝Section 1.1`.
In front of US it hangs a sub-unit off a unit, `␞a␟b␚␟c`, two units with
`c` under `b`. The format says only that `c` is subordinate to `b`; what
that means belongs to the shape. In a data document it is an annotation
the model carries with its unit. In a diff it is the replacement.

So a diff is not a second grammar. A C0DATA parser that has never heard
of diffs reads the example above as a file holding a record of three
units, the second of which holds a sub-unit, which is exactly what it is.
Field counts, CSV and JSON exports see the three units; the sub-unit
rides along with the second. The diff adds only a reading: the record is
a pattern, its units are what the file holds, their sub-units what it
will hold. There is no `+` and `-`, no `@@`, no header pair of paths and
timestamps. There is a document, and a few sentences saying what a diff
tool does with it.

## Matching

A record's search text is its units concatenated: `Hello ` + `world` + `!`.
Its replacement is the same with each sub-unit in place of the unit that
holds it. The search text must occur exactly once in the file, counted
from the end of the previous record's match to the end of the file. Zero
matches is an error. Two or more is an error, and overlapping matches
count: `aa` occurs twice in `aaa`. A unit with no sub-unit is an anchor;
a unit with one is a substitution. Everything a text edit can be falls
out of those two.

    ␞␂class App
      def ␃␟run␚␟start                 anchored before only
    ␞␂Hello ␃␟world␚␟universe␟!         anchored on both sides
    ␞␂x = ␃␟10␚␟20␟␂ + ␃␟5␚␟15          two substitutions in one pattern
    ␞␂import os␃␟␚␟␂
    import sys␃                         insertion: an empty unit, then the new text
    ␞␂# TODO␃␚␟                         deletion: the sub-unit is empty
    ␞def tally(items)                   assertion: no sub-unit, nothing changes

An insertion is an empty unit holding a sub-unit, `␟␚␟new`: the first
unit of a record exists even when empty, so the pattern `␞␚␟new` would be
an insertion with no anchor, and that is an error, because an empty
search text matches everywhere. A deletion is a unit holding an empty
sub-unit. An assertion is a record with no sub-unit at all: its text must
be present once, nothing changes, and the cursor moves past it. Old and
new are values under the ordinary rules, so a value with a line break, a
tab, an edge space or a control byte goes in text fences and a plain word
does not, and there is no quoting to get wrong.

Measuring uniqueness to the end of the file, rather than to the next
record, has a consequence worth stating. Suppose the file has drifted and
an assertion no longer matches. The diff fails, as it should. But suppose
someone deletes the assertion to make it pass. The next record is now
searched in a wider window, and in that window it finds either the same
single match it would have found anyway, or a second one, and the diff
fails. Removing context can never move an edit somewhere else. The
anchors are a safety rail, not a hint.

## All or nothing

A diff is one transaction across its files. The tool matches every record
against every file first; if any record fails anywhere, nothing is
written. Only when every pattern has found its one place does it write,
and it writes each file by writing a temporary and renaming it, so an
interruption leaves no file half done. Matching is decided on the
original bytes, so a substitution early in a file cannot change what a
later record in the same file matches.

## What a diff refuses

The base grammar admits more than a text diff uses: keyed units, nested
levels, references, header rows, groups. Every slot the diff does not use
is an error in a diff, so each stays free for a later, additive meaning.
Two sub-units on one unit, `a␚␟b␚␟c`, is an error: one old has one new. A
sub-unit of a sub-unit is an error. SUB in front of RS is an error in the
base format for now, reserved, and it is the natural slot for a later
diff against a C0DATA document rather than a text file.

One refusal is a judgement rather than a reservation. C0DATA has a
comment mechanism: BEL before an element marks it dead, and a dead record
is skipped by every reader. A diff tool refuses a dead record. The reason
is the gap between reading and applying. A diff is an instruction, and a
hunk that reads as live on the screen but does not apply is a hazard: one
byte, rendered by most tools as nothing at all, would turn a hunk inert
while leaving it visible. In a diff, what is written applies. A hunk is
kept without applying by putting it inside a note as text, `␇␂␞…␃`, where
it is plainly a note.

## No replace-all

There is no "every `x` becomes `y`" in C0DIFF, and there will not be one.
A replace-all is an edit authored without looking at the target and
applied to text it has never seen, which is the one thing an anchored
diff refuses to be. What a tool does instead is expand it: find every
occurrence in the target, take enough context on each side to make each
match unique after the one before, and write one record per occurrence.
The expanded diff is its own preview, since every record shows its change
in context. What applies is explicit and atomic. And the inverse is free:
swap each unit with its sub-unit, `old␚␟new` to `new␚␟old`, and the same
records undo the change. A careful tool checks the inverse against the
result before it commits, so undo is not a hope but a verified property
of the diff it just applied.

## Data about data

Because a diff is a document, it does everything a document does. It can
be stored, hashed, transmitted and signed like any other. The SUB prefix
is structure, not layout, so the canonical form keeps it: canonicalising
a diff never applies it, and a diff hashes as written. A diff may end
with a committed block whose payload is a hash of the files it expects to
find, and an applier that understands the payload checks it before
touching anything. A diff may be a record in a log, or a value in a
field, or the body of a message, with no escaping, because the bytes that
structure it cannot appear in the text it carries.

Seven implementations apply C0DIFF, in Crystal, TypeScript, Rust, Go, C,
Python and Ruby, against one set of forty-two golden cases: the files
before, the diff, and the files after or the refusal. The specification
is one page, `DIFF.md`, at
[github.com/c0data/c0-spec](https://github.com/c0data/c0-spec). It is
short because almost everything a diff needs was already in the format.
