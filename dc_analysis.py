from pathlib import Path
import re

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Project paths
BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "Doctrine_And_Covenants_Cleaned.csv"
SUMMARY_CSV = BASE_DIR / "dc_keyword_summary.csv"
WORD_FREQUENCY_CSV = BASE_DIR / "dc_word_frequencies.csv"

KEYWORDS = [
    "revelation",
    "priesthood",
    "zion",
    "covenant",
    "commandment",
    "repent",
    "obedience",
    "faith",
    "spirit",
    "church"
]

STOPWORDS = {
    "the",
    "and",
    "of",
    "to",
    "that",
    "in",
    "for",
    "be",
    "is",
    "it",
    "this",
    "with",
    "as",
    "which",
    "by",
    "ye",
    "shall",
    "unto",
    "your",
    "you",
    "my",
    "a",
    "an",
    "or",
    "from",
    "on",
    "are",
    "was",
    "were",
    "but",
    "not",
    "have",
    "has",
    "had",
    "their",
    "they",
    "them",
    "who",
    "all",
    "will",
    "at",
    "his",
    "her",
    "he",
    "she",
    "i",
    "we",
    "our",
    "unto",
    "thou",
    "thy",
    "thee",
    "yea",
    "verily",
    "behold",
    "saith",
    "hath",
    "thus",
    "thereof",
    "therein",
    "therewith",
    "wherefore",
    "wherein",
    "whoso",
    "whosoever",
    "let",
    "may",
    "say",
    "even",
    "also",
    "upon",
    "these",
    "those",
    "there",
    "hereby",
    "thereby",
    "thereunto",
    "therefrom",
    "thine",
    "doth",
    "shalt",
    "art",
    "hast",
    "giveth",
    "lest",
    "whereby",
    "thereon",
    "thereof",
}

WORD_VARIANTS = {
    "commandments": "commandment",
    "covenants": "covenant",
    "revelations": "revelation",
    "servants": "servant",
    "words": "word",
    "hearts": "heart",
    "children": "child",
    "days": "day",
    "hands": "hand",
    "men": "man",
    "saints": "saint",
    "sins": "sin",
    "laws": "law",
    "churches": "church",
    "houses": "house",
}


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load the cleaned Doctrine and Covenants dataset."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_columns = {
        "section",
        "year",
        "location",
        "text",
        "clean_text",
        "word_count",
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    return df


def create_output_folders() -> None:
    """Keep output handling simple by using the main project folder."""
    BASE_DIR.mkdir(exist_ok=True)


def print_basic_summary(df: pd.DataFrame) -> None:
    """Print a few simple exploratory summary statistics."""
    year_values = pd.to_numeric(df["year"], errors="coerce").dropna()
    word_counts = pd.to_numeric(df["word_count"], errors="coerce")

    print("Basic summary")
    print(f"Number of sections: {len(df)}")

    if year_values.empty:
        print("Year range: unavailable")
    else:
        print(f"Year range: {int(year_values.min())} to {int(year_values.max())}")

    print(f"Number of unique locations: {df['location'].dropna().nunique()}")
    print(f"Average word count: {word_counts.mean():.1f}")
    print(f"Minimum word count: {int(word_counts.min())}")
    print(f"Maximum word count: {int(word_counts.max())}")


def add_keyword_columns(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    """Count selected doctrinal terms in clean_text."""
    clean_text = df["clean_text"].fillna("").str.lower()

    for keyword in keywords:
        pattern = rf"\b{re.escape(keyword.lower())}\b"
        df[f"{keyword}_count"] = clean_text.str.count(pattern)

    keyword_columns = [f"{keyword}_count" for keyword in keywords]
    df["total_keyword_count"] = df[keyword_columns].sum(axis=1)

    return df


def save_summary_table(df: pd.DataFrame, keywords: list[str]) -> None:
    """Save a compact summary table for later analysis."""
    keyword_columns = [f"{keyword}_count" for keyword in keywords]
    summary_df = df[["section", "year", "location", "word_count", *keyword_columns]]
    summary_df.to_csv(SUMMARY_CSV, index=False)


def get_word_frequencies(df: pd.DataFrame) -> pd.Series:
    """Return word frequencies across the whole cleaned corpus."""
    all_text = " ".join(df["clean_text"].fillna("").str.lower())
    words = re.findall(r"\b[a-z]+\b", all_text)
    filtered_words = []

    for word in words:
        if word in STOPWORDS or len(word) <= 2:
            continue

        normalized_word = WORD_VARIANTS.get(word, word)
        filtered_words.append(normalized_word)

    return pd.Series(filtered_words).value_counts()


def save_word_frequencies_csv(word_frequencies: pd.Series) -> None:
    """Save the full word-frequency table as a CSV file."""
    word_frequencies_df = word_frequencies.rename_axis("word").reset_index(name="frequency")
    word_frequencies_df.to_csv(WORD_FREQUENCY_CSV, index=False)


def plot_common_words(word_frequencies: pd.Series, top_n: int = 25) -> None:
    """Plot the top words in the full Doctrine and Covenants corpus."""
    top_words = word_frequencies.head(top_n)

    plt.figure(figsize=(11, 6))
    plt.bar(top_words.index, top_words.values, color="#B279A2")
    plt.title(f"Top {top_n} Words in the Doctrine and Covenants")
    plt.xlabel("Word")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "most_common_words.png", dpi=300)
    plt.close()


def plot_sections_by_year(df: pd.DataFrame) -> None:
    """Plot the number of sections by year."""
    year_counts = (
        pd.to_numeric(df["year"], errors="coerce")
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
    )

    plt.figure(figsize=(10, 6))
    plt.bar(year_counts.index.astype(str), year_counts.values, color="#4C78A8")
    plt.title("Number of Sections by Year")
    plt.xlabel("Year")
    plt.ylabel("Number of Sections")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "sections_by_year.png", dpi=300)
    plt.close()


def plot_sections_by_location(df: pd.DataFrame) -> None:
    """Plot the number of sections by location."""
    location_counts = (
        df["location"]
        .fillna("Unknown")
        .value_counts()
    )

    plt.figure(figsize=(11, 6))
    plt.bar(location_counts.index, location_counts.values, color="#F58518")
    plt.title("Number of Sections by Location")
    plt.xlabel("Location")
    plt.ylabel("Number of Sections")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "sections_by_location.png", dpi=300)
    plt.close()


def plot_word_count_histogram(df: pd.DataFrame) -> None:
    """Plot the distribution of section word counts."""
    plt.figure(figsize=(10, 6))
    plt.hist(df["word_count"], bins=20, color="#54A24B", edgecolor="black")
    plt.title("Distribution of Section Word Counts")
    plt.xlabel("Word Count")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "word_count_histogram.png", dpi=300)
    plt.close()


def plot_section_vs_word_count(df: pd.DataFrame) -> None:
    """Plot section number against word count."""
    plt.figure(figsize=(10, 6))
    plt.scatter(df["section"], df["word_count"], color="#E45756", alpha=0.8)
    plt.title("Section Number vs Word Count")
    plt.xlabel("Section")
    plt.ylabel("Word Count")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "section_vs_word_count.png", dpi=300)
    plt.close()


def plot_keyword_totals(df: pd.DataFrame, keywords: list[str]) -> None:
    """Plot total doctrinal keyword frequencies across the dataset."""
    totals = pd.Series(
        {keyword: int(df[f"{keyword}_count"].sum()) for keyword in keywords}
    ).sort_values(ascending=False)

    plt.figure(figsize=(10, 6))
    plt.bar(totals.index, totals.values, color="#72B7B2")
    plt.title("Total Frequency of Selected Doctrinal Keywords")
    plt.xlabel("Keyword")
    plt.ylabel("Total Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "keyword_totals.png", dpi=300)
    plt.close()


def print_top_sections(df: pd.DataFrame) -> None:
    """Print the top 10 longest sections and top 10 by keyword totals."""
    print("\nTop 10 longest sections")
    longest_sections = df.nlargest(10, "word_count")[
        ["section", "year", "location", "word_count"]
    ]
    print(longest_sections.to_string(index=False))

    print("\nTop 10 sections by doctrinal keyword totals")
    keyword_sections = df.nlargest(10, "total_keyword_count")[
        ["section", "year", "location", "total_keyword_count", "word_count"]
    ]
    print(keyword_sections.to_string(index=False))


def print_common_words(word_frequencies: pd.Series, top_n: int = 100) -> None:
    """Print the top word frequencies in the corpus."""
    print(f"\nTop {top_n} words in the Doctrine and Covenants")
    print(word_frequencies.head(top_n).to_string())


def main() -> None:
    """Run the exploratory analysis workflow."""
    create_output_folders()

    df = load_data(INPUT_CSV)
    df = add_keyword_columns(df, KEYWORDS)
    word_frequencies = get_word_frequencies(df)

    print_basic_summary(df)
    print_top_sections(df)
    print_common_words(word_frequencies)

    plot_sections_by_year(df)
    plot_sections_by_location(df)
    plot_word_count_histogram(df)
    plot_section_vs_word_count(df)
    plot_keyword_totals(df, KEYWORDS)
    plot_common_words(word_frequencies)

    save_summary_table(df, KEYWORDS)
    save_word_frequencies_csv(word_frequencies)

    print(f"\nPlots saved to: {BASE_DIR}")
    print(f"Summary table saved to: {SUMMARY_CSV}")
    print(f"Word frequencies saved to: {WORD_FREQUENCY_CSV}")


if __name__ == "__main__":
    main()
