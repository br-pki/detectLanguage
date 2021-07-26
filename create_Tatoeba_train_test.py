# Create a train-test set from Tatoeba
import argparse
import tarfile
import urllib.request
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split

def get_language_mappings(this_path: str) -> pd.DataFrame:
    """
    Load a local file containing mappings between the English names
    & the ISO 639-3 & ISO 639-1 abbreviations.

    Args:
    this_path - str; the path to the mappings file.

    Returns:
    language_mappings - pd.DataFrame; mappings between names & abbreviations.
    """
    assert isinstance(this_path, str), "this_path is not of type str."
    assert len(this_path) != 0, "The length of this_path is zero. Submit a path to a file."
    
    language_mappings = pd.read_csv(this_path)
    # enforce expected format
    assert all(i in language_mappings.columns for i in ["English Name", "ISO 639-1", "ISO 639-3"]), f"Not all necessary columns found in language_mappings file. Check {file_path}"
    
    return language_mappings

def get_sentences(min_sentences: int, these_languages: list) -> pd.DataFrame:
    """
    Get the Tatoeba sentences from a local file or download from Tatoeba
    if not found. Filter down to a subset of the sentences based on criteria.

    Args:
    min_sentences - int; minimum number of sentences each language should have.
    these_languages - list; languages to include.

    Returns:
    result - pd.DataFrame; a subset of the Tatoeba sentences.
    """
    assert isinstance(min_sentences, int), "min_sentences is not of type int."
    assert isinstance(these_languages, list), "these_languages is not of type list."
    assert these_languages, "these_languages doesn't contain any elements"
    assert all(isinstance(i, str) for i in these_languages), "not all elements of these_languages are of type str."
    
    print(f"Getting Tatoeba sentences for {these_languages}...")
    file_path = "sentences.csv"
    try:
        sentences = pd.read_csv(file_path, delimiter="\t", header=None, index_col=0, names=["Language", "Sentence"])
    except:
        print("...no local file, downloading from Tatoeba...")
        tatoeba_url = "https://downloads.tatoeba.org/exports/sentences.tar.bz2"
        response = urllib.request.urlopen(tatoeba_url)
        tar = tarfile.open(fileobj=response, mode="r|bz2")
        tar.extractall(path=".")
        tar.close()
        sentences = pd.read_csv(file_path, delimiter="\t", header=None, index_col=0, names=["Language", "Sentence"])
        
    print(f"Filtering sentences based on language and minimum number of sentences...")
    # find which languages have minimum sentences == min_sentences
    language_counts = sentences["Language"].value_counts()
    language_counts = language_counts.to_frame().reset_index()
    language_counts.rename(columns={"index":"ISO 639-3 Name", "Language": "Count"}, inplace=True)
    # map from these_languages to ISO 639-3 & filter
    language_mappings = get_language_mappings(this_path="language_mappings.csv")
    language_mappings = language_mappings[language_mappings["English Name"].isin(these_languages)]
    iso_639_3_English = language_mappings[["ISO 639-3", "English Name"]].set_index(keys="ISO 639-3")["English Name"].to_dict()
    language_counts["English Name"] = language_counts["ISO 639-3 Name"].map(iso_639_3_English)
    # filter by languages with min_sentences & in these_languages using 3 digit language identifier: ISO 639-3 Name
    language_filter = language_counts[(language_counts["Count"]>=min_sentences)&(~language_counts["English Name"].isna())]["ISO 639-3 Name"].tolist()
    result = sentences[sentences["Language"].isin(language_filter)]
    if result.empty: print("No sentences found for given language/minimum sentence criteria...")
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
    assert isinstance(these_sentences, pd.DataFrame), "these_sentences is not of type pd.DataFrame."
    assert not these_sentences.empty, "these_sentences is an empty DataFrame."
    print("Taking a sample...")
    # TODO: implement a better way of limiting total sample size while considering the size of individual languges in subset of corpus so train-test isn't huge
    max_sample_size = int(these_sentences["Language"].value_counts().min() / 1000) * 1000
    print(f"...of {max_sample_size} sentences per language.")
    this_sample = these_sentences.groupby("Language", group_keys=False).apply(lambda x: x.sample(max_sample_size))
    return this_sample

def main():
    # parse args
    parser = argparse.ArgumentParser()
    # TODO: implement option to specify where to save sentences.csv (if downloaded)
    # TODO: implement option to specify where to save test-train (if outputted)
    # TODO: implement option to specify train size: float between 0 & 1
    parser.add_argument(
        "-l", "--languages",
        nargs="*",
        default = [
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
            "Dutch",
            "Norwegian", # no Norwegian in sentences?          
        ],
        help="languages to include in output",
        required=False
    )
    parser.add_argument(
        "-m", "--minimum_sentences",
        type=int,
        default=5000,
        help="minimum number of sentences found in corpus"
    )
    args = parser.parse_args()
    if args.languages:
        args.languages = [i.title() for i in args.languages]
    
    # get sentences, take sample, create train & test
    sentences = get_sentences(min_sentences=args.minimum_sentences, these_languages=args.languages)
    if not sentences.empty:
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
        print("Train & test files saved to output/")
    else:
        print("No sample generated.")
    print("Finished!")

if __name__ == "__main__":
    main()