# The Emotional Landscape of Aviation Pilots: Scraper & Emotion Classification Pipeline

Data collection and NLP code for the paper:

> Renwick, A. S., Gonzalez, L., Silber, C. L., Mullen, A., Dykeman, C., Stewart, A., Ross, J. C., & Geisler, J. (2025). **The Emotional Landscape of Aviation Pilots: Analysis of Online Professional Forums Using Natural Language Processing.** *Journal of Aviation/Aerospace Education & Research, 34*(3). https://doi.org/10.58940/2329-258X.2132

- Journal page: https://commons.erau.edu/jaaer/vol34/iss3/1/
- Full text (PDF): https://commons.erau.edu/cgi/viewcontent.cgi?article=2132&context=jaaer
- Project page (pre-registration, raw data, ANOVA results, figures): https://osf.io/hgaz6/

This repository contains **only the software side of the study**: the forum scraper and the emotion classification step. The statistical analysis (descriptive statistics, ANOVAs, burnout composite score, figures) was done separately and is **not** included here. Those results are on the OSF project page.

## Highlights

- **1,130,530 forum posts** spanning 19 years (2005–2024), collected by a custom scraper in a single run (April 7–8, 2024).
- **Recursive crawler** that discovers sub-forums, skips sticky threads, walks pagination, and cleans quotes and HTML out of each post.
- **GPU-accelerated transformer inference** (RoBERTa via PyTorch + CUDA) producing 28 emotion scores for every post.
- **Analysis-ready output:** a single 34-column CSV feeding the study's statistical analysis, published in a peer-reviewed journal.

---

## Overview

The study looked at burnout-related emotions in three groups of pilots (commercial passenger, commercial cargo, and military) by analyzing anonymous posts from [Airline Pilot Central Forums](https://www.airlinepilotforums.com).

The pipeline has two stages:

```
airlinepilotforums.com
        │
        ▼
  scrape.py           ──►  JSON/<Category>/<thread>.json          (one file per thread)
        │
        ▼
  emotion_analysis.py ──►  JSON_results/<Category>/<thread>.json  (same data + per-post emotion scores)
                      └─►  results.csv                             (one row per post, used for statistics)
```

## Dataset

| Paper group | Directory/CSV Forum Category | Posts |
|---|---|---:|
| Commercial passenger | Major | 712,464 |
| Commercial cargo | Cargo | 361,519 |
| Military | Military | 56,547 |
| **Total** | | **1,130,530** |

- Posts span **February 18, 2005 to April 8, 2024**.
- The scraper ran **April 7–8, 2024**.
- All posts are in English.
- Usernames were never collected, to protect anonymity.
- The paper calls the `Major` forum group "Passenger". They are the same data.

The raw data is **not** stored in this repo. It is available on the [OSF project page](https://osf.io/hgaz6/).

## Headline Results

These results come from the paper. The analysis itself was done outside this repo.

- **"Neutral" was the dominant category** for all three pilot groups (mean score: Passenger 0.4667, Cargo 0.4473, Military 0.4424). Curiosity and approval were the most common emotions.
- **Differences between groups were statistically significant for 27 of the 28 categories** (the exception was surprise, *p* = 0.20). However, every effect size was trivial or at most small (Cohen's *f* ≤ 0.11).
- **Exploratory burnout composite:** the mean of seven emotion scores (anger, annoyance, disappointment, disapproval, disgust, fear, sadness).
  - Mean scores: Military 0.018, Cargo 0.020, Passenger 0.021.
  - ANOVA: *F*(2, 1,130,527) = 437.66, *p* < .001, Cohen's *f* = 0.028.
  - The difference is statistically significant but practically meaningless; the three groups are effectively equivalent.

See the paper for full tables, figures, and discussion.

---

## Components

### `scrape.py`: Forum Scraper

A recursive scraper built with `requests` and Beautiful Soup 4, using custom CSS selectors.

1. **Forum pages.** It walks each top-level forum (`/major/`, `/cargo/`, `/military/`) page by page (`index2.html`, `index3.html`, ...). It stops when the server redirects, which means the requested page doesn't exist.
2. **Sub-forums.** It discovers each forum's sub-forums (for example `/delta/`, `/fedex/`) and scrapes them the same way.
3. **Threads.** For every non-sticky thread, it walks the thread's pages (`<thread>-2.html`, `<thread>-3.html`, ...) until a redirect signals the last page.
4. **Posts.** For each post, it pulls the timestamp and message text:
   - Quoted blocks and HTML tags are stripped.
   - Posts with an empty timestamp are skipped.
5. **Output.** It writes one JSON file per thread into the directory for its category:
   - `Major` or `Cargo` is chosen from the thread URL and the hard-coded sub-forum lists.
   - A thread that fails writes `__ERROR-LOG__<thread>.json` containing the exception message instead.

Output format (`JSON/<Category>/<thread>.json`):

```json
{
    "thread_url": "https://www.airlinepilotforums.com/...html",
    "1": [
        { "timestamp": "...", "message_text": "..." }
    ],
    "2": [ ... ]
}
```

Top-level keys other than `thread_url` are page numbers stored as strings.

The CSS selectors and URL patterns target the site as it was in April 2024.

### `emotion_analysis.py`: Emotion Classification

Classifies every scraped post with [`SamLowe/roberta-base-go_emotions`](https://huggingface.co/SamLowe/roberta-base-go_emotions). This is RoBERTa-base trained on Google's GoEmotions dataset. It was used as-is, without fine-tuning.

- **Output.** Each post gets a score from 0 to 1 for each of **28 labels**: 27 emotions plus `neutral`. This is multi-label output, so the scores do not sum to 1.
- **Truncation.** Posts are truncated to the model's **512-token** maximum. Only the first 512 tokens of a long post are scored.
- **Hardware.** Inference runs through a Hugging Face `pipeline` on a CUDA GPU (`top_k=None` returns scores for every label).
- **Error logs.** Files named `__ERROR-LOG__*` are skipped.

Outputs:

- `JSON_results/<Category>/<thread>.json`: the input JSON with a `results` object (`label → score`) added to every post.
- `results.csv`: one row per post, with these 34 columns:

  | Columns | Content |
  |---|---|
  | 1–6 | `Forum Category`, `File Name`, `Thread URL`, `Page`, `Timestamp`, `Message Text` |
  | 7–34 | `admiration`, `amusement`, `anger`, `annoyance`, `approval`, `caring`, `confusion`, `curiosity`, `desire`, `disappointment`, `disapproval`, `disgust`, `embarrassment`, `excitement`, `fear`, `gratitude`, `grief`, `joy`, `love`, `nervousness`, `neutral`, `optimism`, `pride`, `realization`, `relief`, `remorse`, `sadness`, `surprise` |

---

## Requirements

Versions reported in the paper:

| Package | Version |
|---|---|
| Python | 3.11.5 |
| beautifulsoup4 | 4.12.2 |
| torch | 2.2.2 (with CUDA) |

Also required (I don't remember what versions were being used at the time, but here are the libs):

- `requests`
- `transformers`
- `matplotlib`

`emotion_analysis.py` hard-codes `torch.device("cuda")` and will fail on a CPU-only machine unless you change it.

```bash
# Install the CUDA build of PyTorch that matches your driver: https://pytorch.org/get-started/locally/
pip install beautifulsoup4==4.12.2 requests transformers matplotlib
```

## Usage

Both scripts use relative paths, so run them from the repository root.

**1. Create the output directories.** Neither script creates them.

```bash
# macOS / Linux
mkdir -p JSON/{Major,Cargo,Military} JSON_results/{Major,Cargo,Military}
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force -Path JSON/Major, JSON/Cargo, JSON/Military, JSON_results/Major, JSON_results/Cargo, JSON_results/Military
```

**2. Scrape.**

```bash
python scrape.py
```

**3. Classify.**

```bash
python emotion_analysis.py
```

The model (~500 MB) downloads from Hugging Face the first time you run this. The script prints the total elapsed time when it finishes.

## Ethics

- The study was reviewed by the University of Nevada, Reno Institutional Review Board and determined **exempt** (IRB 2174745-2, Exemption Category 4(i), 45 CFR 46.104).
- Only publicly available posts were collected.
- Usernames were not collected.
- If you rerun the scraper, check the site's terms of use and `robots.txt`, and throttle your requests.

## Citation

If you use this code, please cite the paper:

```bibtex
@article{renwick2025emotional,
  title   = {The Emotional Landscape of Aviation Pilots: Analysis of Online Professional Forums Using Natural Language Processing},
  author  = {Renwick, Adrienne S. and Gonzalez, Leo and Silber, Charles L. and Mullen, Alyson and Dykeman, Cass and Stewart, Adam and Ross, Jennifer C. and Geisler, James},
  journal = {Journal of Aviation/Aerospace Education \& Research},
  volume  = {34},
  number  = {3},
  year    = {2025},
  doi     = {10.58940/2329-258X.2132},
  url     = {https://commons.erau.edu/jaaer/vol34/iss3/1/}
}
```

## License

The **code** in this repository is released under the [MIT License](LICENSE).

The **paper** is a separate work, published by the journal under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/). The MIT License does not apply to it.
