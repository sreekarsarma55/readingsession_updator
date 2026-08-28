# Archive audit report

- Sessions parsed: **216**
- Distinct works: **66**
- Reading time (normalised): **432.0 hours**
- Date range: **2022-12-12** to **2026-08-03**

## Assumptions baked into the numbers

- The chat export never records how long a session ran, so every session is normalised to **120 minutes** (`default_duration_minutes` in `config/settings.json`).
- `Stopped_At` is therefore `Created_Date + Duration_Minutes`, not an observed end time.
- `Created_Date` is the session's real start: the **date** comes from the message timestamp and the **time** from the announcement's `Time :` line, resolved in IST (Asia/Kolkata). The announcement's own `Date :` line is ignored because it contains copy-paste errors.
- A co-read session stays one row, so `Duration_Minutes` is never double-counted.
- `Hours` in `works.csv` credits each session to its primary work only.
- Per-session corrections can be added to `duration_overrides` in `config/settings.json`.
- `Stopped_At` is the site's live handover log, which narrators fill in each session, so it is exported **blank** for the history: a value inferred from a four-year-old announcement would read as something a human logged. What each session actually covered is already carried by `Segment`. Set `stopped_at_from_segment` to true to back-fill it anyway (it would reach only 14 of the 217 rows).
- The website's `duration_minutes` is nullable and the model says to leave it blank until recordings are measured. We fill it with the normalised value so the site's totals add up; set `emit_duration_minutes` to false to export it blank and keep that field strictly measured.

## Works whose session count exceeds their session rows

`sessions.csv` has one row per sitting, linked to that sitting's primary work. Where a single sitting covered two works, the second work's `Sessions` total in `works.csv` is higher than the number of rows naming it. Nothing is lost - the pairing is recorded in `Also_In_Session` in `sessions_detailed.csv`.

- 2024-04-08 - Dagon and The Other Gods + The Upper Berth
- 2024-12-09 - Salem's Lot + From The Pages of Childhood
- 2024-12-11 - Salem's Lot + From The Pages of Childhood
- 2024-12-13 - Salem's Lot + From The Pages of Childhood
- 2024-12-27 - Salem's Lot + From The Pages of Childhood
- 2024-12-30 - Salem's Lot + From The Pages of Childhood
- 2025-01-02 - Salem's Lot + From The Pages of Childhood
- 2025-01-03 - Salem's Lot + From The Pages of Childhood
- 2025-01-06 - Salem's Lot + From The Pages of Childhood
- 2025-01-08 - Salem's Lot + From The Pages of Childhood
- 2025-01-10 - Salem's Lot + From The Pages of Childhood
- 2025-01-13 - Salem's Lot + From The Pages of Childhood
- 2025-01-22 - Salem's Lot + From The Pages of Childhood
- 2025-01-24 - Salem's Lot + From The Pages of Childhood
- 2025-01-29 - Salem's Lot + From The Pages of Childhood
- 2025-02-03 - Salem's Lot + Ink What You Think
- 2025-02-05 - Salem's Lot + Ink What You Think
- 2025-02-07 - Salem's Lot + Ink What You Think
- 2025-02-12 - Salem's Lot + Ink What You Think
- 2025-02-14 - Salem's Lot + Ink What You Think
- 2025-02-28 - Salem's Lot + Ink What You Think
- 2025-03-07 - Salem's Lot + Ink What You Think

## Works still missing an author (1)

- **Didi** (1 session(s)) - Author not stated in chat. Possibly Subhadra Kumari Chauhan's 'Didi' - needs confirmation from whoever ran the session.

## Metadata needing a human check (1)

- **Didi** by ? [unverified] - Author not stated in chat. Possibly Subhadra Kumari Chauhan's 'Didi' - needs confirmation from whoever ran the session.

## Reader identities that are educated guesses

These merges are set in `config/reader_aliases.json`. Confirm or correct them there:

- `abhishek bhaiyya` -> **Abhishek Kumar Jha**
- `amit new member bib` -> **Amit Kumar Gupta**
- `chatrapal` -> **Chatrapal Singh Rathore**
- `gharsh` -> left as-is, real name unknown
- `himanshu` -> left as-is, real name unknown
- `sreevidya` -> **Sreevidya Yadavally**
- `thanvi` -> **Vedam Thanvi Sree Nithya**

## Sessions with no reader assigned (29)

The announcement said 'Open to all', 'Me', '???' or had no Reader line.

- 2023-03-20 - The Last Leaf (reader not assigned ('Open'))
- 2023-03-22 - The Champawat Man-Eater (reader not assigned ('Open'))
- 2023-03-24 - The Champawat Man-Eater (reader not assigned ('Open'))
- 2023-06-05 - Carmilla (reader not assigned ('???'))
- 2023-06-19 - The Monkey's Paw (reader not assigned ('To be decided in the session'))
- 2023-09-29 - Devolution (reader not assigned (''))
- 2023-10-02 - Devolution (reader not assigned ('Me'))
- 2023-10-04 - Devolution (reader not assigned ('Me'))
- 2023-10-06 - Devolution (reader not assigned ('Me'))
- 2023-10-11 - Evelina (reader not assigned ('Open to all'))
- 2023-10-13 - Evelina (reader not assigned ('Open to all'))
- 2023-10-16 - Evelina (reader not assigned ('Open to all'))
- 2023-10-18 - Evelina (reader not assigned ('Open to all'))
- 2023-11-15 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2023-11-20 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2023-11-24 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2023-12-06 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2023-12-11 - Pride and Prejudice (reader not assigned ('open to all'))
- 2023-12-13 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2023-12-15 - Pride and Prejudice (reader not assigned ('Open to all'))
- 2024-02-09 - Ramayan (reader not assigned ('Open to all'))
- 2024-03-04 - The Hitchhiker's Guide to the Galaxy (reader not assigned ('Open to all'))
- 2024-03-11 - The Hitchhiker's Guide to the Galaxy (reader not assigned ('Open to all'))
- 2024-03-13 - The Hitchhiker's Guide to the Galaxy (reader not assigned ('Open to all'))
- 2024-03-18 - The Hitchhiker's Guide to the Galaxy (reader not assigned ('Open To All'))
- 2024-04-03 - The Case of The Caretaker (reader not assigned ('Open to all'))
- 2024-04-05 - Miss Marple Stories (reader not assigned ('Open to all'))
- 2024-04-17 - Sherlock Holmes Stories (reader not assigned ('Open to all'))
- 2026-01-16 - दो बैलों की कथा (no Reader line in the announcement)

## Sessions where the reader was still undecided (1)

- 2024-09-20 - Waiting for the Mahatma: Ayesha Badgujar; Himanshu Sharma; Satyaki Goswami

## Messages that looked like announcements but were skipped (5)

- Tuesday, August 15, 2023 at 4:10:14 PM UTC - announcement-like message with no Book/Story label
  > Reading Sessions : A Chapter A Day Hey all!!🌻 Here are the details for today's session : Date : 15th August, 2023 Time : 10:15 PM Occasion : Independence Day Sp
- Sunday, September 3, 2023 at 4:42:01 PM UTC - announcement-like message with no Book/Story label
  > Reading Sessions : A Chapter A Day Hey all!!🌻 Here are the details for today's session : Date : September 3rd, 2023 Time : 10:20 PM No book today, but a discuss
- Monday, April 7, 2025 at 3:54:09 PM UTC - announcement-like message with no Book/Story label
  > Hello There, Lovely People ❤ Batman's gauntlet through Arkham has been mind boggling as of now. And although today's Monday, we would be resuming with the Readi
- Saturday, July 11, 2026 at 1:16:29 PM UTC - announcement-like message with no Book/Story label
  > Hello there, lovely people Weekly open mic Hey all🌻, come join us for an open mic. Whether you'd like to share your poems, stories, songs, or any other creative
- 2026-03-18T16:41:30+00:00 - re-post of the 2026-03-18 'The Kite Runner' session, already announced by Sreevidya Yadavally
  > The Kite Runner | reader: Sreevidya Yadavally | re-posted by 24F2001732 SHRUJAL N K

## Multi-work and combined sessions

- 2024-04-08 - Dagon and The Other Gods + The Upper Berth
- 2024-12-09 - Salem's Lot + From The Pages of Childhood
- 2024-12-11 - Salem's Lot + From The Pages of Childhood
- 2024-12-13 - Salem's Lot + From The Pages of Childhood
- 2024-12-27 - Salem's Lot + From The Pages of Childhood
- 2024-12-30 - Salem's Lot + From The Pages of Childhood
- 2025-01-02 - Salem's Lot + From The Pages of Childhood
- 2025-01-03 - Salem's Lot + From The Pages of Childhood
- 2025-01-06 - Salem's Lot + From The Pages of Childhood
- 2025-01-08 - Salem's Lot + From The Pages of Childhood
- 2025-01-10 - Salem's Lot + From The Pages of Childhood
- 2025-01-13 - Salem's Lot + From The Pages of Childhood
- 2025-01-22 - Salem's Lot + From The Pages of Childhood
- 2025-01-24 - Salem's Lot + From The Pages of Childhood
- 2025-01-29 - Salem's Lot + From The Pages of Childhood
- 2025-02-03 - Salem's Lot + Ink What You Think
- 2025-02-05 - Salem's Lot + Ink What You Think
- 2025-02-07 - Salem's Lot + Ink What You Think
- 2025-02-12 - Salem's Lot + Ink What You Think
- 2025-02-14 - Salem's Lot + Ink What You Think
- 2025-02-28 - Salem's Lot + Ink What You Think
- 2025-03-07 - Salem's Lot + Ink What You Think
