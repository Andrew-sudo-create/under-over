from scripts.run_scraper import main

# Edit these in code when you want to change scrape target.
LOCATION = "gauteng"
LIMIT = 30


if __name__ == "__main__":
    main(location=LOCATION, limit=LIMIT)
