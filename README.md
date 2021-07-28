# detectLanguage
 The purpose of this repo is to evaluate the performance of different solutions for detecting various languages in text.

 Currently, there are three components:

 1. language_mappings.csv
     Simple file to faciliate mappings between the English name for a language and the ISO 639-1 (2-digit) and the ISO 639-3 (3-digit) code. 
 1. create_Tatoeba_train_test.py
    usage: create_Tatoeba_train_test.py [-h] [--languages [LANGUAGES ...]] [--minimum_sentences MINIMUM_SENTENCES] [--sample_type {random,stratify}]

    optional arguments:
      -h, --help            show this help message and exit
      --languages [LANGUAGES ...]
                            languages to include in output
      --minimum_sentences MINIMUM_SENTENCES
                            minimum number of sentences found in corpus
      --sample_type {random,stratify}
                            type of sample to take: "random" or "stratify"
                        
     You can limit the Tatoeba sentences based on language and/or number of sentences per language in the corpus.
     The default languages are English, Chinese, German, Spanish, French, Italian, Japanese, Korean, Portuguese, Danish, Dutch, and Norwegian. Any subset of those can be specified using the --languages flag.
     The default number of sentences per language in the corpus is 5,000. If a language has fewer sentences in the corpus than what's specified it won't be included in the output. Any integer can be specified using the --min_sentences flag.
 1. evaluate.ipynb
     Notebook for evaluating the performance of different solutions for detecting various languages in text including: langid, langdetect, and textblob. 
