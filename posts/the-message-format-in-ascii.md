# The message format that was already in ASCII

*2026-11-08. Thomas Sawyer.*

Open the [1963 ASCII chart](https://en.wikipedia.org/wiki/ASCII) and read the first column. Not the letters.
The [first thirty-two positions](https://en.wikipedia.org/wiki/C0_and_C1_control_codes), the ones your keyboard still reaches
with the Control key and that no editor will show you.

    0x01  SOM   Start of Message
    0x02  EOA   End of Address
    0x03  EOM   End of Message
    0x04  EOT   End of Transmission
    0x05  WRU   Who Are You
    0x06  RU    Are You
    0x07  BELL
    ...
    0x18  S0
    0x19  S1
    ...
    0x1F  S7

That is not a character set. That is a protocol. Before ASCII was an
alphabet for files and terminals it was an alphabet for machines talking
to each other over a wire, and the committee spent its first thirty-two
codes on the conversation: who are you, here comes a message, here is
the address, here is the text, done, goodbye. The eight unnamed
separators at the end were left for whatever structure the message
carried inside.

The 1967 revision gave everything its lasting names. SOM became SOH,
Start of Heading. EOA became STX, Start of Text. EOM became ETX. WRU
became ENQ, Enquiry. The last four separators got a hierarchy and names
to match: FS, GS, RS, US. File, Group, Record, Unit. The first four
became CAN, EM, SUB, ESC. Cancel, End of Medium, Substitute, Escape.

## What a message looked like

For about fifteen years this was how two computers exchanged a record.
The procedures were written down in ANSI X3.28, and IBM's [Binary
Synchronous Communications](https://en.wikipedia.org/wiki/Binary_Synchronous_Communications), announced in 1967 with the [2780 terminal](https://en.wikipedia.org/wiki/IBM_2780/3780),
was the version most people met.

    SYN SYN ENQ                           may I send?
    SYN SYN ACK                           go ahead
    SYN SYN SOH heading STX text ETB BCC  first block
    SYN SYN ACK
    SYN SYN SOH heading STX text ETX BCC  last block
    SYN SYN ACK
    SYN SYN EOT                           line released

Two SYNs so the receiver could find the character boundary in a stream
of bits. SOH, then a heading that said where the message was going and
what it was. STX, then the text. ETB closed a block that had more to
follow, ETX the last one, and a block check character followed each so
the receiver could say ACK or NAK (BISYNC spelled its acknowledgement as
a DLE pair, alternating ACK0 and ACK1, so a lost reply could be told
from a repeated one). EOT released the line.

If the text had to carry a byte that looked like a control code, DLE
in front of it said "this one is data", and DLE DLE was a literal DLE.
That transparency was a mode of its own, switched on for a block with
DLE STX and off again with DLE ETX, so a channel built for text could
carry binary; an ordinary text block never needed it.

Inside the text, the four separators did what their names said. A file
held groups, a group held records, a record held units. The standard
fixed the order and said nothing else: what a group was, what a unit
was, was the user's business. On a nine-track tape or a deck of punch
cards that was exactly the right amount of standard.

## Why it disappeared

Three things happened, and none of them was a decision.

ASCII became the alphabet of terminals. The control codes that a
terminal does something with survived in daily use: BEL, BS, HT, LF, CR,
FF, ESC, and DC1 and DC3 as flow control. The ones that framed a
conversation between machines had nothing to do on a screen.

Framing moved down the stack. [HDLC](https://en.wikipedia.org/wiki/High-Level_Data_Link_Control) put a flag byte and bit stuffing
around a frame; later protocols put a length in front of it; TCP made a
reliable byte stream and the question of where a message began became
somebody else's. Nobody needed STX to find the start of the text when the
packet header already said how long it was.

And data formats were written by people, in editors, so they used
delimiters people could type. Comma. Tab. Angle brackets. Braces and
quotes. CSV, then SGML and XML, then JSON. Every one of them is a format
whose delimiter can occur in the data, and every one of them pays for
that with a quoting rule: doubled quotes, entities, backslashes. The
separators never had that problem, because nobody types them, and nobody
types them because no editor shows them.

So they went quiet. Not away: quiet. For sixty years every operating
system, every language, every network has carried 0x1C through 0x1F
unharmed, because they are just bytes and nothing claims them. A few
formats kept using them. Library catalogues in [MARC](https://www.loc.gov/marc/) end a record with
0x1D, a field with 0x1E and a subfield with 0x1F, and have since the
1970s. [RFC 7464](https://www.rfc-editor.org/rfc/rfc7464), from 2015, separates a sequence of JSON texts with RS.
[GNU Info files](https://www.gnu.org/software/texinfo/manual/texinfo/html_node/Info-Format-Specification.html) mark each node with US. That is about it.

## What was lost

A delimiter that cannot be in the data.

That sentence is the whole argument. Pick any text format and ask what
happens when a value contains the thing that separates values. CSV has
two incompatible answers. JSON has a grammar of escapes that every parser
gets right and every hand-written producer gets wrong once. XML has five
entities and a CDATA section. All of this exists because the delimiter is
a printable character, and printable characters are what data is made of.

The ASCII committee had solved this in 1963 by putting the delimiters
outside the printable range. Data is bytes 0x20 and up. Structure is
bytes below 0x20. They cannot collide, so nothing needs quoting. A
reader finds a record boundary by scanning for one byte, and that scan
is the fastest thing a CPU does.

## Picking it up again

[C0DATA](https://c0data.github.io/) is that message format, resumed. Sixteen of the thirty-two codes,
each doing what its name says or the nearest thing the name allows, and
the other sixteen left alone.

    ␖  SYN  starts a document; the heading follows
    ␁  SOH  marks a key, in the heading or in a record
    ␜  FS   file
    ␝  GS   group
    ␞  RS   record
    ␟  US   unit
    ␂  STX  starts text, when a value needs it
    ␃  ETX  ends it
    ␐  DLE  inside text, escapes; outside, opens a nested level
    ␘  CAN  closes the level
    ␇  BEL  a note, or marks the next element dead
    ␅  ENQ  a reference to data defined elsewhere
    ␗  ETB  commits a block in a log
    ␙  EM   end of medium: a raw blob follows
    ␚  SUB  substitution
    ␄  EOT  ends the document

Two users, name and amount, as a table with a header row:

    ␖␁shape␟tabular␝users␁␞name␟amount␞Alice␟1502.30␞Bob␟340.00␄

Sixty bytes, against eighty as JSON and thirty-seven as CSV. The small
example flatters CSV, because the whole difference is the framing: the
heading, the group name, the mark that says the first row is a header,
and EOT. Per row, C0DATA spends what CSV spends, one byte between fields
and one between rows. So the gap to CSV is a constant, 23 bytes for this
table whether it has two rows or ten thousand, while JSON keeps paying
for its keys and punctuation on every row. On sample tables with the
same two columns:

    rows      C0DATA      CSV      JSON
    100        1,996    1,973     4,172
    1,000     19,781   19,758    41,757
    10,000   198,018  197,995   417,994

And only the C0DATA form can hold a comma, a quote, a newline or a brace
in a value without a rule for it. Those glyphs, by the way, are real:
Unicode put a [picture of every control code](https://en.wikipedia.org/wiki/Control_Pictures) at U+2400, so a document can
be shown exactly as it is without any of its bytes changing.

Some of the 1967 roles moved, and I should say which and why. SYN starts
a document rather than SOH, because the one thing a reader must be able
to do from any offset is find a beginning, and the frame used SYN for
exactly that. SOH, which once began the whole message, now begins a key:
the heading of a document is keys, and so is the heading of a record,
which is the nearest thing the name allows. DLE kept both of its
meanings. Inside text it is still the escape. Outside text it still says
that what follows is not plain data, and there it opens a nested level,
which CAN closes. The block check character is gone; the medium checks
bytes now. ACK and NAK are
gone for the same reason. ETB survived because an append-only log still
needs a mark that says "everything before this is final", and that is
what it always said.

Text, when a value needs it, is STX to ETX, and inside it only seven
codes are escaped: the two that fence text, DLE itself, and the four that
frame a document, ETB, EOT, SYN and EM, so that a torn log can never hide
a commit behind an unclosed quote. Everything else inside text is data as
it stands, separators included.

The rest is what you would expect once the delimiters are free: a
canonical form, so that equal data is equal bytes and can be hashed; a
header row so a table can name its columns once; keyed records whose
order is data; nesting; references; and a diff format that uses SUB for
what SUB was named for, the place where a wrong value is replaced by the
right one. Seven implementations read and write it against one
conformance suite. The spec is at [github.com/c0data](https://github.com/c0data).

## The point

ASCII's authors designed a message format and a text encoding in the same
table, and the world kept the half it could see. The other half has been
riding along in every byte stream since, untouched because unused, which
is the longest compatibility test any format has ever passed. It was
waiting for someone to need a delimiter that cannot be in the data. I
did, so I picked it up.
