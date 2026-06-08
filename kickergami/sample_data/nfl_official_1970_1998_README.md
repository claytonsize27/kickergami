# NFL Official 1970-1998 Kicker CSVs

Generated from official NFL.com player field-goal stats and player game logs, with NFL-hosted/official-club-hosted game summary PDFs and corroborated Pro Football Reference scoring summaries used to complete known multi-field-goal rows.

Files:

- `nfl_official_1970_1998_upload.csv`: upload-ready normalized rows. These validate against the app schema because every row has exact made field-goal distances.
- `nfl_official_1970_1998_gsis_enhanced_partial.csv`: upload-ready normalized rows after adding every GSIS-resolved multi-FG row accumulated so far. The filename is historical; the current unresolved multi-FG audit is empty.
- `nfl_official_1970_1998_playoffs.csv`: separate upload-ready normalized playoff rows for the 1970-1998 seasons. Keep this separate from the regular-season CSV when doing a postseason-only backfill.
- `nfl_official_1970_1998_playoffs_unresolved.csv`: playoff audit rows that could not be safely resolved. The current audit is empty.
- `nfl_official_1970_1998_exact_from_logs.csv`: rows that can be completed from NFL.com game logs alone. This includes games with zero made field goals and games with exactly one made field goal, where NFL.com's `Lng` field is the made distance.
- `nfl_official_1970_1998_needs_gamebook_distances.csv`: official NFL.com kicker-game count rows where `fg_made > 1`. NFL.com logs provide the count and longest made FG, but not every made FG distance, so these rows are not safe to upload until an official gamebook/source supplies the full distance list.
- `nfl_official_partial_1970_1998.csv`: NFL-hosted PDF-verified rows used to complete a few multi-FG games.
- `scripts/complete_nfl_gsis_distances.py`: resolver for official NFLGSIS gamebook PDFs. It discovers gamebook IDs, extracts born-digital PDF text with PyMuPDF, and falls back to OCR for scanned gamebooks.
- `scripts/complete_nfl_gamecenter_distances.py`: resolver for official NFL.com Game Center pages that expose static NFL-hosted gamebook PDFs.
- `scripts/complete_nfl_annual_summary_distances.py`: resolver for NFL-branded annual scoring-summary PDFs hosted by the Eagles media CDN. These list per-game scoring plays, including made field-goal distances.
- `scripts/complete_nfl_club_media_guide_distances.py`: conservative resolver for official club media-guide PDFs hosted on `static.clubs.nfl.com` when the guide contains explicit historical game scoring summaries.
- `nfl_gsis_resolved_multi_fg_rows.csv`: GSIS-resolved multi-FG rows accumulated by the resolver.
- `nfl_gsis_unresolved_multi_fg_rows.csv`: rows not yet safe to merge because of parser misses, gamebook discovery misses, or official-source attribution conflicts.

Coverage as generated:

- `nfl_official_1970_1998_upload.csv`: 7,532 validated upload rows, seasons 1970-1998.
- `nfl_official_1970_1998_gsis_enhanced_partial.csv`: 11,935 validated upload rows after accumulated GSIS, NFL.com Game Center, annual scoring-summary, official club media-guide, and corroborated Pro Football Reference scoring-summary resolution.
- `nfl_official_1970_1998_playoffs.csv`: 510 validated upload rows covering 269 playoff games for the 1970-1998 seasons.
- `nfl_official_1970_1998_playoffs_unresolved.csv`: 0 current unresolved playoff audit rows.
- `nfl_gsis_resolved_multi_fg_rows.csv`: 4,410 accumulated resolved multi-FG rows. Seven of these overlap rows that were already present in the original upload seed, so the final normalized CSV has 11,935 unique `(game_id, player_id)` rows rather than `7,532 + 4,410`.
- `nfl_gsis_unresolved_multi_fg_rows.csv`: 0 current unresolved audit rows from the full best-effort 1970-1998 retry set.
- `nfl_official_1970_1998_needs_gamebook_distances.csv`: 4,410 rows with official counts but missing full made-FG distance lists.

Important limitation:

This is the current upload-ready 1970-1998 kicker-stat CSV produced from public official NFL.com logs, NFL-hosted PDFs, official/club-hosted summaries, and Pro Football Reference scoring summaries corroborated against official sources where NFL.com's longest-made-FG value conflicts. The last pass resolved the remaining 15 audit rows by majority-source review; source-conflict rows retain provenance in `nfl_gsis_resolved_multi_fg_rows.csv`.

Trusted distance source found:

- Official NFLGSIS gamebook PDFs, for example `https://nflgsis.com/1998/reg/11/465/Gamebook.pdf`.
- Older official NFLGSIS gamebooks use a case-sensitive `Reg` path, for example `https://nflgsis.com/1984/Reg/05/14496/Gamebook.pdf`. The resolver now probes both `Reg` and `reg`.
- Official NFL.com Game Center pages can expose static NFL-hosted gamebook PDFs, for example `https://www.nfl.com/games/cardinals-at-redskins-1997-reg-3` links to `https://static.www.nfl.com/image/upload/v1737683243/gamecenter/10011997-0914-0086-2a21-8b7c15b03b86.pdf`.
- NFL-branded annual scoring-summary PDFs hosted by the official Eagles media CDN, for example `https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28150347/1981.pdf` and `https://media.eagles.1rmg.com/wp-content/uploads/2022/02/28151436/1997.pdf`. These annual summaries list per-game scoring plays such as `Dal - FG Septien 29`, which provides team, kicker, and made-FG distance attribution.
- Official club media-guide and fact-book PDFs hosted by `static.clubs.nfl.com`, for example the 1971 New Orleans Saints media guide at `https://static.clubs.nfl.com/image/upload/saints/tecwancwttvcxqnxkoqm.pdf` and Saints record/fact book at `https://static.clubs.nfl.com/image/upload/saints/zupknbzryc6xiedwrojn.pdf`. The scanned guides include historical game scoring summaries with explicit field-goal scoring lines; the resolver only applies rows manually verified from OCR/search snippets.
- Official Chargers/Raiders game-release record-book entries hosted by `static.clubs.nfl.com` corroborate Greg Davis' six field goals at Oakland on October 5, 1997 as `(30, 22, 38, 43, 33, 33)`, matching the 1997 annual scoring summary. The club resolver also applies corrected team/game attribution for rows where NFL.com's player log counts were tied to the wrong season-level team after an in-season move.
- Pro Football Reference box-score scoring summaries were used as a trusted corroborating source for remaining rows where official annual summaries and NFL.com game-log counts needed confirmation, or where NFL.com's `Lng` field conflicted with scoring-play distance lists. Remaining source conflicts were resolved only when multiple sources supported the same value; for example, the 1978 Neil O'Donoghue Tampa Bay at Detroit row uses `27,49,28` because NFL.com's longest-made-FG value, the 1978 annual prose, and the gamebook-style recap agree on the 49-yard make despite a conflicting 45-yard scoring-summary line.
- The playoff CSV uses official NFL.com postseason player game logs for XP/FG counts and the NFL-branded annual scoring-summary PDFs for made-FG distances in multi-FG games. Old-format rows where NFL.com exposed a player as another position, such as George Blanda and Jim O'Brien in the 1970 playoffs, were supplemented from explicit annual scoring lines. Majority-source review resolved the 1998 Gary Anderson ARI-MIN conflict as `34,20`, where the NFL annual and Pro Football Reference agreed against NFL.com's `Lng` value.
- GSIS gamebooks include scoring plays and `Field Goals (Made & Missed)` summaries with made FG distances.
- 1998 regular-season multi-FG rows were test-resolved from GSIS with zero unresolved parser rows.
- 1998 regular-season multi-FG rows were resolved from GSIS with zero unresolved parser rows and merged into the enhanced partial CSV.
- 1997 was mostly resolved, but 6 multi-FG rows remain unresolved because of either parser misses or NFL.com-vs-GSIS attribution conflicts.
- 1995-1996 GSIS PDFs are much noisier. Many gamebooks have embedded text that is garbled, and OCR output varies by scan quality. Current long-pass completion rates are 33.2% for 1995 and 79.1% for 1996, so those seasons are not yet complete enough for a final upload CSV.
- The 1981-1994 long pass did not meet the accuracy bar. The corrected `Reg` source path proves more official PDFs are available, but many older scans still fail game matching or field-goal extraction.
- Public NFLGSIS regular-season gamebooks were confirmed through URL probing for 1981 week 1 and not found for 1979-1980 week 1 in the same public URL pattern. The 1970-1980 rows have been added to the unresolved audit with no merged distances, because no trusted official gamebook path was found by the current resolver.
- The full 1970-1998 best-effort pass currently resolves 4,410 multi-FG rows and leaves 0 unresolved audit rows. Rows were not merged until the official source block, kicker/team attribution, made-field-goal count, and source-conflict review were specific enough to avoid a false distance list.
- The NFL.com Game Center PDF source was tested against the remaining 1995-1998 unresolved rows. It did not safely add rows: 1995 pages mostly lacked Game Book PDF links, and available 1996-1997 PDFs either still failed distance extraction or showed kicker attribution conflicts with the NFL.com game-log rows. Those rows remain in the unresolved audit.
