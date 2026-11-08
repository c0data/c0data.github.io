# Reading the chart again

*Thomas Sawyer · 8 November 2026*

The first thirty-two positions of ASCII are control codes, and each one
has a name and a definition from 1967. Most of them were written for
machines talking over a wire: here comes a heading, here comes the text,
this block is done, goodbye. C0DATA is a data format built from sixteen of
them, and the short version of how is that nothing was invented. Every
code kept its name and its sense. What changed is the thing the code acts
on. In 1967 a control code acted on characters on a wire. In C0DATA it
acts on units of data in a document. Lift the operand one level, and the
chart reads as a data format.

Sixteen codes are used. Here they are, with the old meaning and the new.

    code  1967                        C0DATA
    SOH   start of heading            key: what follows heads what comes after
    STX   start of text               open an exact value
    ETX   end of text                 close it
    EOT   end of transmission         end of document
    ENQ   enquiry                     reference to data elsewhere in the document
    BEL   bell                        note, or: the next thing is dead
    DLE   data link escape            the next code opens a level
    SYN   synchronous idle            start of document, heading follows
    ETB   end of transmission block   commit
    CAN   cancel                      close the level
    EM    end of medium               raw bytes follow, to the end
    SUB   substitute                  the pair old/new (C0DIFF)
    FS    file separator              file
    GS    group separator             group
    RS    record separator            record
    US    unit separator              unit

Most of these need a sentence. Four need a section, and one pair, STX and
ETX, changed the most and deserves the reason.

## The floor

The four separators do what their names say. A document is files, a file
is groups, a group is records, a record is units. Each separator begins
the thing it names, and nothing ends it except the next code or the end of
input. Here is one record of a ledger, in the glyphs the pretty form uses
and then in the bytes the wire carries:

    ␞Alice␟1502.30␟DEPOSIT

    1e 41 6c 69 63 65 1f 31 35 30 32 2e 33 30 1f 44 45 50 4f 53 49 54

That is the whole encoding of a value: the bytes of the value. No quotes,
no escapes, no length prefix. The separators are never in the data,
because nobody types them and no editor shows them, so there is nothing to
quote, and a parser's hot loop is one comparison, `byte < 0x20`.

A document starts with SYN and ends with EOT. Between the SYN and the first
separator sits the heading, where a document says what a reader must know
before reading, and the heading is written with the code the committee
named for exactly that.

## SOH: the key

In 1967 a message was SOH, the heading, STX, the text, ETX. The heading was
the address block: who this is for, what it is. SOH said "a heading for
what comes after."

It still does. Put it in front of a value and the value gets a name:

    ␞␁name␟Alice␁amount␟1502.30␁type␟DEPOSIT

That is a map. Each SOH begins a key, the US divides the key from its
value, and the next SOH ends the unit by beginning another. Put SOH in
front of RS instead and the record it opens is a heading for the records
that follow it:

    ␝users
    ␁␞name␟amount␟type
    ␞Alice␟1502.30␟DEPOSIT
    ␞Bob␟340.00␟WITHDRAWAL

That is a table with a header row. And directly after SYN, SOH keys head
the whole document:

    ␖␁shape␟stream␁version␟1

Same byte, one meaning, three shapes: a map, a table, a document heading.
The spec puts it in one line, *SOH means one thing everywhere: what follows
is a heading for what comes after it.* A consequence worth stating is that
the order of keys in a map is data. The format does not sort them, and two
maps with the same keys in a different order are different bytes and
different documents. Anything that wants map equality can sort, but the
format carries what was written.

## DLE and CAN: recursion

The separators give four levels and no more: a file cannot hold a file. A
format needs more than that, because a field sometimes holds a table, and
the table's rows hold tables. Something has to say "the hierarchy starts
over here," and it has to be one of the sixteen.

In 1967 DLE meant "the next character is data, not control." It was the
escape hatch: in BISYNC's transparent mode, DLE in front of a control
character turned it back into a byte of the message. Lifted one level, it
means "the next code is not a boundary at this level; it opens a level
inside this one." An RS after DLE does not end the current record. It
starts a record inside the current field:

    ␝users
    ␁␞name␟amount␟address
    ␞Alice␟1502.30␟␐
      ␁␞street␟city
      ␞123 Main␟Springfield
    ␘

The DLE is on the opener only. Inside, the codes carry nothing extra: a
header row is a header row, a record is a record, a group is a group,
exactly as at the top, to any depth. The way out is CAN, "cancel," which
closes what the DLE opened. A level can hold a list of records, a table, a
map, or a whole document with its own files, and the reader does not care
which; the first code after the DLE tells it.

One byte in, one byte out, and nothing inside needs marking. That is the
recursion rule in full.

## STX and ETX: the flipped script

These two changed the most, and the reason explains the two above.

In 1967, STX and ETX wrapped the text of a message, and the text was the
payload, all of it. It was tempting to use them as the recursive container
in C0DATA. A nested value is a message inside a message, and the message's
body was what STX and ETX fenced. DLE would then keep its old job as the
escape for the odd control byte inside a value, the transparent-mode
pattern. It nearly went that way.

Two considerations turned it around. The first is the names. "Start of
text" was a good map in 1967 because everything was text; there was
nothing else a message could carry. Today the thing being fenced is a
unit of data, which may be a table, and calling a table "text" is a poor
map. "Data link escape" describes the move far better: escape from this
level of the data to another. So the script flipped. DLE became the marker
for substructure, and STX and ETX became the container for the other thing
a format needs, a value that is exact.

An exact value is one whose bytes are taken as they stand: leading and
trailing spaces kept, line breaks kept, tabs kept, and control codes
inside it taken as data. In a plain value, space around the edges is
layout and a separator is a separator. Inside STX and ETX only seven bytes
are special, and each takes a DLE in front to become data: STX and ETX
themselves, DLE, and the four framing codes ETB, EOT, SYN and EM. Everything
else, RS and US and CAN and the lot, is a byte of the value. Binary passes
through inflated by about three percent.

Seven escapes instead of 1967's one, and the extra six are there for a
reason that matters more than symmetry. The framing codes cut through
text. If a log is torn mid-value, so that an STX is open with no ETX, the
next ETB still commits, the next EOT still ends, and an open quote cannot
swallow everything after it. That is the opposite of transparent mode,
where a raw ETB inside text was data, and it is the right way round for
a file that may be appended to after a crash.

The second consideration is what the alternative would have looked like.
Had STX and ETX been the container and DLE the escape, the exact-value form
would have been DLE STX, the bytes, DLE ETX, sitting in documents alongside
plain STX and ETX doing the container's job. Two meanings for the same pair,
told apart by whether a DLE precedes them, in a format whose whole point is
that one byte means one thing. Nobody wants to read that, and no tokenizer
wants to be told to look back a byte.

## ETB: the commit

A record is start-delimited. RS begins it, and only the next code ends it.
That is what makes the encoding so small, and it has a cost: in a file
that is appended to, a process can die in the middle of writing a record,
and the half-record at the end looks exactly like a whole one.

In 1967 ETB ended a transmission block. BISYNC sent a message in blocks,
and each block was acknowledged before the next went out; ETB was the mark
that a block was complete. Lifted, it is a commit. In a document whose
heading says `shape` `stream`, ETB says that everything since the previous
ETB has landed:

    ␖␁shape␟stream␁␞op␟id␟at␗
    ␞create␟a1b2c3␟1718208000␗
    ␞name␟draft-2␟1718208042␗
    ␞tag␟alpha␟17182080

The last line has no ETB. A reader treats it as torn and skips it, whatever
it holds, without calling it an error, since a torn tail is the normal
state of a log after a crash. A writer checks that the file ends at a
commit before appending, and truncates or resumes from the last ETB if it
does not. A block is usually one record but can be several, so a batch
committed with one ETB is atomic. ETB may carry a payload, a plain value up
to the next code, reserved for a checkpoint hash of the block it closes.

That is an append-only log with crash safety for one byte per block, and
the byte means what it always meant: the block ended, and it is good.

## The rest, in a sentence each

**SYN** begins a document. On a synchronous line it was the idle pattern a
receiver locked onto before the message; here it is the byte a reader
locks onto before the heading.

**EOT** ends a document. Everything before it is final, which is what it
said in 1967.

**ENQ** is a reference. "Enquiry" asked the other end for something; here
a field asks for data defined elsewhere in the same document, a group by
name, or a path of group, record id and field.

**BEL** rang a bell to get attention. Followed by text it is a note a
reader skips; followed by a structural code it marks that element dead,
parsed and then discarded, which is how a record is retracted in a log
without rewriting the log.

**EM**, end of medium, marks the end of all C0DATA in the container.
Everything after it, to the end of the file, is one raw region: no
escapes, no framing, no scanning. A document can carry a blob after
itself without encoding it.

**SUB**, substitute, was the mark for a character received in error, to be
replaced. In C0DIFF it sits between an old value and its new one. That
format is still being settled and gets its own post.

## What the lifting bought

The codes were designed for a wire, where the units were characters and
the structure was one message. Raise the operand to the unit of data, and
the same sixteen codes give a document with files, groups, records and
fields; maps and tables from one key marker; recursion from one escape and
one cancel; exact values from one pair of fences; and crash-safe logs from
one commit mark. There is no quoting in the structure, because the
delimiters cannot be in the data. There is one spelling for every value,
so equal data is equal bytes and a document can be hashed. And the hot
loop of a parser is one comparison.

None of that is clever. It is the 1967 chart, read as if the committee had
been describing data instead of a conversation, which, in the end, is what
a conversation between machines is.

The spec is at [github.com/c0data/c0-spec](https://github.com/c0data/c0-spec), and the
pretty form shown here is what the editor extension and `c0fmt` display:
Unicode's Control Pictures for the codes, which no tool mistakes for
structure, with the bytes underneath for everything else.
