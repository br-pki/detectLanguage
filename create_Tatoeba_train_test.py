# Create a train-test set from Tatoeba
import pandas as pd
from sklearn.model_selection import train_test_split

PKI_LANGUAGES = [
    "English",
    "Chinese",
    "German",
    "Spanish",
    "French",
    "Italian",
    "Japanese",
    "Korean",
    "Portuguese",
    "Danish",
    "Dutch", # no Dutch in sentences?
    "Norwegian", # no Norwegian in sentences?
]

def get_language_mappings():
    """
    """
    file_path = "data/language_mappings.csv"
    try:
        language_mappings = pd.read_csv(file_path)
    except:
        print(f"Could not find file at {file_path}.")
    return language_mappings

def process_sentences(this_df, min_sentences=5000, these_languages=PKI_LANGUAGES):
    """
    """
    print("Processing sentences file...")
    original_len = len(this_df)
    # find which languages have minimum sentences == min_sentences
    language_counts = this_df["Language"].value_counts()
    language_counts = language_counts.to_frame().reset_index()
    language_counts.rename(columns={"index":"ISO 639-3 Name", "Language": "Count"}, inplace=True)
    # map from these_languages to ISO 639-3 & filter
    language_mappings = get_language_mappings()
    language_mappings = language_mappings[language_mappings["English Name"].isin(these_languages)]
    iso_639_3_English = language_mappings[["ISO 639-3", "English Name"]].set_index(keys="ISO 639-3")["English Name"].to_dict()
    language_counts["English Name"] = language_counts["ISO 639-3 Name"].map(iso_639_3_English)
    # filter this_df by languages with min_sentences & in these_languages
    language_filter = language_counts[(language_counts["Count"]>=min_sentences)&(~language_counts["English Name"].isna())]["ISO 639-3 Name"].tolist()
    # language_filter = language_filter["ISO 639-3 Name"].tolist()
    # use 3 digit language identifier: ISO 639-3 Name
    result = this_df[this_df["Language"].isin(language_filter)]
    new_len = len(result)
    print(f"...sentences trimmed by {(round(new_len / original_len, 2))*100}%")
    return result

def get_sentences_file():
    """
    Return the path for sentences.csv.
    TODO: if not found download & unzip the file from Tatoeba into data/.

    Args:
    None

    Returns:
    result -- The path to the sentences file.
    """
    print("Getting sentences file...")
    file_path = "data/sentences.csv"
    tatoeba_url = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"
    try:
        sentences = pd.read_csv(file_path, delimiter="\t", header=None, index_col=0, names=["Language", "Sentence"])
        processed_sentences = process_sentences(sentences)
        return processed_sentences
    except:
        # TODO: attempt downloading from Tatoeba instead of raising error
        print(f"Could not find file at {file_path}. Try downloading & unzipping file from {tatoeba_url} there.")    

def get_sample(this_df):
    """
    """
    print("Taking a sample...")
    max_sample_size = int(this_df["Language"].value_counts().min() / 1000) * 1000
    print(f"...of {max_sample_size} sentences per language")
    sample = this_df.groupby("Language", group_keys=False).apply(lambda x: x.sample(max_sample_size))
    return sample

def main():
    sentences_df = get_sentences_file()
    sample = get_sample(sentences_df)
    X = sample["Sentence"] 
    y = sample["Language"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.8, shuffle=True, stratify=y)

if __name__ == "__main__":
    main()