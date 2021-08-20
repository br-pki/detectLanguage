# detectLanguage
## Purpose
The purpose of this repository is twofold:
 1. Create train/test samples of sentences and their relevant languages from Tatoeba for NLP-related tasks.
 1. Evaluate the performance of solutions meant to detect the language of a given piece of text to identify a reliable solution (spoiler: langid).

## Tatoeba
Tatoeba is a database of sentences and their translations. Currently, there are +9 million sentences and +400 supported languages. The content is created and maintained by a community of volunteers. The data is freely available under a Creative Commons Attribution (CC-BY) license:

Tatoeba -- https://tatoeba.org/ -- CC-BY License

Tatoeba content has been used in other projects including the [Tatoeba Translation Challenge](https://github.com/Helsinki-NLP/Tatoeba-Challenge) maintained by the Language Technology Research Group at the University of Helsinki and the [Tatoeba Tools](https://github.com/LBeaudoux/tatoebatools) Python library maintained by L.Beaudoux.

## Components
 Currently, there are three main components in this repository.

### create_Tatoeba_train_test.py

 A script for generating customizable train-test samples of sentences and their languages. Such samples are useful for other NLP-related tasks (e.g. evaluating machine translations).

The default languages are English, Chinese, German, Spanish, French, Italian, Japanese, Korean, Portuguese, Danish, Dutch, and Norwegian. Any subset can be specified using the --languages flag.

The default threshold of sentences per language is 5,000. If a language has fewer sentences than the threshold available in the corpus then it won't be included in the output. Any integer can be specified using the --min_sentences flag.

The --sample_type flag gives the option to specify a simple random sample or a random sample stratified by sentence word/character length, the default is random.

You can generate unique sets of train/test samples using --number_sets, the default is 1. The train/test split is a standard 80/20.

    usage: create_Tatoeba_train_test.py [-h] [--languages [LANGUAGES ...]] [--minimum_sentences MINIMUM_SENTENCES] [--sample_type {random,stratify}] [--number_sets NUMBER_SETS]

    optional arguments:
      -h, --help            show this help message and exit

      --languages [LANGUAGES ...]
                            languages to include in output

      --minimum_sentences MINIMUM_SENTENCES
                            minimum number of sentences found in corpus

      --sample_type {random,stratify}
                            type of sample to take: "random" or "stratify"

      --number_sets NUMBER_SETS
                            number of train-test sets to generate

### evaluate.ipynb
A notebook for evaluating the performance of solutions for detecting the language of a given text. It's currently focused on [langid](https://github.com/saffsd/langid.py) and [langdetect](https://github.com/Mimino666/langdetect). I prefer langid due to its speed and better performance identifying Chinese, although both solutions achieve similar F1 scores.

Includes F1 scores, confusion matrices, and compiling the results as a function of sentence length to facilitate plotting.

### plot_results.ipynb
A notebook for plotting the performance results by language and as a function of sentence length.

### get_predictions.ipynb
A notebook for generating predictions for a large number of samples and finding the average F1 scores by language and by sentence length. It takes several hours (+8) to run and the results for 100 samples are not drastically different than the results for 1 sample.