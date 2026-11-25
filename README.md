# THE COMEBACK — 24 November 2026 World News in One Image

[![make.fun](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/jiangzhang674-a11y/news-image-20261124-the-comeback/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/jiangzhang674-a11y/news-image-20261124-the-comeback/reward.svg)](https://make.fun/bounty/news-image-20261124)

> Owner **jiangzhang674-a11y** and repo **news-image-20261124-the-comeback**
> are filled in (username confirmed by the user's GitHub screenshot on
> 2026-11-25; repo name chosen for submission). The badges above are the
> live make.fun badges for this exact repository — no placeholder left.
> Use the existing 674 account (jiangzhang674@gmail.com); do not create
> a new GitHub account.

An entry for the make.fun bounty
[Sum up 24 November's world news in one image](https://make.fun/bounty/news-image-20261124):
one newspaper front page — **THE COMEBACK, Tuesday 24 November 2026** —
summing up the day's world news.

Headlines on the front page:

- **HUANG IS BACK AT NVIDIA** — Jensen Huang returns as Nvidia chief
  executive 11 days after resigning; shares surge 31%, market value back
  to $4.0T.
- **CLIMATE TALKS END IN FAILURE** — COP31 in Antalya ends without an
  agreement.
- **UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA** — Ukrainian sea drones sink
  the Russian corvette Merkury off Benghazi.
- Briefs: **AWACS TO POLAND** and **ASIA FACTORY FIRE KILLS 24**.

## How the entry works

The repository holds the pre-rendered front page as `entry.png`
(724 × 1024 px, inside the competition gate of at most 1024 × 1024 px
and 1 MiB). The competition entrypoint is `main.py` (Python 3.13,
standard library only), which just copies `entry.png` to the grader's
output directory — exactly like the kit's own starter `main.ts` does.
It runs twice and writes the same bytes both times.

`build_frontpage.py` is the local build tool only (Pillow + system
fonts). It rebuilds `entry.png` from `news/news-20261124.json` and is
never run in the sandbox.

Local check:

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
python3 -I main.py                        # isolated mode, no site-packages
```

## License

MIT — see [LICENSE](LICENSE).
