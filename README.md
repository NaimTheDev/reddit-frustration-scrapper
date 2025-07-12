# Reddit Frustration Scraper

A configurable Python scraper that finds "frustration" posts/comments across any subreddits and any brand or keyword list.

## Features

- **Config-driven**: No code changes needed—just edit `config.json`.
- Supports multiple subreddits, search queries, and regex patterns.
- Scrapes both submissions and comments.
- Filter content based on frustration keywords and custom criteria
- Export data to various formats (JSON, CSV)
- Outputs a JSON results file with detailed post information

## Getting Started

### Prerequisites

To use this scraper, you need Reddit API credentials. Create a Reddit app by following the [PRAW quick start guide](https://praw.readthedocs.io/en/stable/getting_started/quick_start.html). You'll need your client ID, client secret, and user agent for the configuration file.

1. **Clone the repo**

   ```bash
   git clone https://github.com/yourusername/reddit-frustration-scraper.git
   cd reddit-frustration-scraper
   ```

2. **Install dependencies**:
   might need to run in a virual environemnt if you have different versions of these in your local machinge

```bash
cd reddit-frustration-scraper
python3 -m venv .venv
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

3. **Set up configuration**:

```bash
cp config.example.json config.json
```

4. **Edit `config.json`** with your Reddit API credentials and preferences.

## Usage

```bash
python reddit_frustration_scraper.py
```

## Configuration

The scraper uses a JSON configuration file. See `config.json` for available options.

## Testing

Run tests with:

```bash
python -m pytest tests/
```

## License

MIT License
