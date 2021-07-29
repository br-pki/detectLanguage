# Create a train-test set from Tatoeba
import argparse
import tarfile
import urllib.request
import re
import pandas as pd
import warnings
warnings.filterwarnings('ignore')
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
    
    print(f"Getting Tatoeba sentences for {sorted(these_languages)}...")
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
    else: print(f"...languages in sample: {sorted([iso_639_3_English[i] for i in language_filter])}...")
    return result

def get_sentence_word_char_len(this_row: pd.Series) -> int:
    """
    Count the number of words or characters in a sentence based
    on the language of the sentence.
    
    Args:
    this_row - pd.Series, a row from a pd.DataFrame.
    
    Returns:
    result - int; the count of words or characters in the sentence.
    """
    assert isinstance(this_row, pd.Series), "this_row is not of type pd.Series."
    this_language = this_row["Language"]
    this_text = this_row["Sentence"]
    # remove punctuation from this_text
    this_text = re.sub(r"[。？?！!，.“”、「」]", "", this_text) # the pattern is just a number of punctuations I found in the Asian texts
    if this_language in ["Chinese", "Japanese", "Korean"]:
        result = len(this_text)
    else:
        result = len(this_text.split())
    return result

def take_sample(these_sentences: pd.DataFrame, sample_type: str) -> pd.DataFrame:
    """
    Take a random sample from a DataFrame containing Tatoeba sentences
    with each language contributing no more than the minimum number
    of sentences in the smallest language.

    Args:
    these_sentences - pd.DataFrame; sentences & their assigned language.
    sample_type - str; the type of sample to take: "random" or "stratify"

    Returns:
    this_sample - pd.DataFrame; a subset of sentences.
    """
    assert isinstance(these_sentences, pd.DataFrame), "these_sentences is not of type pd.DataFrame."
    assert not these_sentences.empty, "these_sentences is an empty DataFrame."
    assert isinstance(sample_type, str), "sample_type is not of type str."
    assert sample_type in ["random", "stratify"], 'sample_type is not "random" or "stratify"'
    print(f"Taking a {'stratified' if sample_type=='stratify' else 'random'} sample...")
    
    if sample_type == "random":
        # TODO: implement a better way of limiting total sample size while considering the size of individual languges in subset of corpus so train-test isn't huge
        max_sample_size = int(these_sentences["Language"].value_counts().min() / 1000) * 1000
        print(f"...of {max_sample_size} sentences per language.")
        this_sample = these_sentences.groupby("Language", group_keys=False).apply(lambda x: x.sample(max_sample_size))
    elif sample_type == "stratify":
        # call get_sentence_word_char_len
        these_sentences["Sentence_word_char_len"] = these_sentences.apply(lambda row: get_sentence_word_char_len(row), axis=1)
        # only keep sentences with <201 chars
        these_sentences = these_sentences[these_sentences["Sentence_word_char_len"]<100]
        # bin sentences by len
        bin_labels = ["1","2","3","4","5","6","7","8","9","10","11 to 16", "17 to 27", "28 to 48", "49 to 99"]
        these_sentences["bin"] = pd.cut(
            x=these_sentences["Sentence_word_char_len"],
            bins=[0,1,2,3,4,5,6,7,8,9,10,16,27,48,99],
            labels=bin_labels
        )
        # iterate through bins & take sample for that bin
        this_sample = pd.DataFrame()
        for this_bin in bin_labels:
            temp_sample = these_sentences[these_sentences["bin"]==this_bin]
            # find max sample size
            max_sample_size = temp_sample["Language"].value_counts(normalize=False).min()
            print(f"...of {max_sample_size} sentences per language for bin = {this_bin}.")
            temp_sample = temp_sample.groupby("Language", group_keys=False).apply(lambda x: x.sample(max_sample_size))
            this_sample = this_sample.append(temp_sample)
    return this_sample

def main():
    # parse args
    parser = argparse.ArgumentParser()
    # TODO: implement option to specify where to save sentences.csv (if downloaded)
    # TODO: implement option to specify where to save test-train (if outputted)
    # TODO: implement option to specify train size: float between 0 & 1
    parser.add_argument(
        "--languages",
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
        "--minimum_sentences",
        type=int,
        default=5000,
        help="minimum number of sentences found in corpus",
        required=False
    )
    parser.add_argument(
        "--sample_type",
        type=str,
        default="random",
        choices=["random", "stratify"],
        help='type of sample to take: "random" or "stratify"',
        required=False
    )
    args = parser.parse_args()
    if args.languages:
        args.languages = [i.title() for i in args.languages]
    
    # get sentences, take sample, create train & test
    sentences = get_sentences(min_sentences=args.minimum_sentences, these_languages=args.languages)
    if not sentences.empty:
        sample = take_sample(sentences, args.sample_type)
        y = sample["Language"]
        X_train, X_test, y_train, y_test = train_test_split(
            sample["Sentence"],
            y,
            train_size=0.8,
            shuffle=True,
            stratify=y
        )
        # combine train & test into DFs & save each in output/
        train = X_train.to_frame().merge(right=y_train, how="inner", left_index=True, right_index=True)
        test = X_test.to_frame().merge(right=y_test, how="inner", left_index=True, right_index=True)

        # save train & test files
        now = datetime.now()
        datetime_stamp = f"{now.year}-{now.month}-{now.day}_{now.hour}{now.minute}"
        train.to_csv(f"output/Tatoeba_{args.sample_type}_train_{datetime_stamp}.csv", index_label="Original Index")
        test.to_csv(f"output/Tatoeba_{args.sample_type}_test_{datetime_stamp}.csv", index_label="Original Index")
        print("Train & test files saved to output/")
    else:
        print("No sample generated.")
    print("Finished!")

if __name__ == "__main__":
    main()