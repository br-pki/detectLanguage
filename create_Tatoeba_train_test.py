# Create a train-test set from Tatoeba
import tarfile
import urllib.request
import pandas as pd
from datetime import datetime
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

def get_language_mappings() -> pd.DataFrame:
    """
    Load a local file containing mappings between the English names
    & the ISO 639-3 & ISO 639-1 abbreviations.

    Args:
    None

    Returns:
    language_mappings - pd.DataFrame; mappings between names & abbreviations.
    """
    file_path = "data/language_mappings.csv"
    try:
        language_mappings = pd.read_csv(file_path)
    except:
        print(f"Could not find file at {file_path}.")
    return language_mappings

def filter_sentences(these_sentences: pd.DataFrame, min_sentences: int = 5000, these_languages: list = PKI_LANGUAGES) -> pd.DataFrame:
    """
    Filter the contents of a DataFrame containing Tatoeba sentences based on
    language & sentence count per language.

    Args:
    these_sentences - pd.DataFrame; sentences.
    these_languages - list; languages to include.
    min_sentences - int; minimum number of sentences each language should have.

    Returns:
    result - pd.DataFrame; a subset of sentences.
    """
    print("Filtering sentences...")
    # find which languages have minimum sentences == min_sentences
    language_counts = these_sentences["Language"].value_counts()
    language_counts = language_counts.to_frame().reset_index()
    language_counts.rename(columns={"index":"ISO 639-3 Name", "Language": "Count"}, inplace=True)
    # map from these_languages to ISO 639-3 & filter
    language_mappings = get_language_mappings()
    language_mappings = language_mappings[language_mappings["English Name"].isin(these_languages)]
    iso_639_3_English = language_mappings[["ISO 639-3", "English Name"]].set_index(keys="ISO 639-3")["English Name"].to_dict()
    language_counts["English Name"] = language_counts["ISO 639-3 Name"].map(iso_639_3_English)
    # filter this_df by languages with min_sentences & in these_languages
    language_filter = language_counts[(language_counts["Count"]>=min_sentences)&(~language_counts["English Name"].isna())]["ISO 639-3 Name"].tolist()
    # use 3 digit language identifier: ISO 639-3 Name
    result = these_sentences[these_sentences["Language"].isin(language_filter)]
    print(f"...sentences trimmed by {(round(len(result) / len(these_sentences), 3))*100}%")
    return result

def get_sentences() -> pd.DataFrame:
    """
    Get the Tatoeba sentences from a local file or
    download from Tatoeba if not found.

    Args:
    None

    Returns:
    result - pd.DataFrame; a subset of sentences.
    """
    print("Getting Tatoeba sentences...")
    file_path = "data/sentences.csv"
    try:
        sentences = pd.read_csv(file_path, delimiter="\t", header=None, index_col=0, names=["Language", "Sentence"])
    except:
        print("...no local file, downloading from Tatoeba...")
        tatoeba_url = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"
        response = urllib.request.urlopen(tatoeba_url)
        tar = tarfile.open(fileobj=response, mode="r|bz2")
        tar.extractall(path="data/")
        tar.close()
        sentences = pd.read_csv(file_path, delimiter="\t", header=None, index_col=0, names=["Language", "Sentence"])
        # print(f"Could not find file at {file_path}. Try downloading & unzipping file from {tatoeba_url} there.")    
    result = filter_sentences(sentences)
    return result

def take_sample(these_sentences: pd.DataFrame) -> pd.DataFrame:
    """
    Take a random sample from a DataFrame containing Tatoeba sentences
    with each language contributing no more than the minimum number
    of sentences in the smallest language.

    Args:
    these_sentences - pd.DataFrame; sentences & their assigned language.

    Returns:
    this_sample - pd.DataFrame; a subset of sentences.
    """
    print("Taking a sample...")
    max_sample_size = int(these_sentences["Language"].value_counts().min() / 1000) * 1000
    print(f"...of {max_sample_size} sentences per language.")
    this_sample = these_sentences.groupby("Language", group_keys=False).apply(lambda x: x.sample(max_sample_size))
    return this_sample

def main():
    sentences = get_sentences()
    sample = take_sample(sentences)
    y = sample["Language"]
    X_train, X_test, y_train, y_test = train_test_split(
        sample["Sentence"],
        y,
        train_size=0.8,
        shuffle=True,
        stratify=y
    )
    # TODO: implement option for stratifying by sentence length as well
    # combine train & test into DFs & save each in output/
    train = X_train.to_frame().merge(right=y_train, how="inner", left_index=True, right_index=True)
    test = X_test.to_frame().merge(right=y_test, how="inner", left_index=True, right_index=True)
    # save train & test files
    now = datetime.now()
    datetime_stamp = f"{now.year}-{now.month}-{now.day}_{now.hour}{now.minute}"
    train.to_csv(f"output/Tatoeba_train_{datetime_stamp}.csv", index_label="Original Index")
    test.to_csv(f"output/Tatoeba_test_{datetime_stamp}.csv", index_label="Original Index")
    print("Train & test files saved to output/\nFinished!")

if __name__ == "__main__":
    main()