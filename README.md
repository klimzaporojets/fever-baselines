# Fact Extraction and VERification

This is the PyTorch implementation of the FEVER pipeline baseline described in the NAACL2018 paper: [FEVER: A large-scale dataset for Fact Extraction and VERification.]()

> Unlike other tasks and despite recent interest, research in textual claim verification has been hindered by the lack of large-scale manually annotated datasets. In this paper we introduce a new publicly available dataset for verification against textual sources, FEVER: Fact Extraction and VERification. It consists of 185,441 claims generated by altering sentences extracted from Wikipedia and subsequently verified without knowledge of the sentence they were derived from. The claims are classified as Supported, Refuted or NotEnoughInfo by annotators achieving 0.6841 in Fleiss κ. For the first two classes, the annotators also recorded the sentence(s) forming the necessary evidence for their judgment. To characterize the challenge of the dataset presented, we develop a pipeline approach using both baseline and state-of-the-art components and compare it to suitably designed oracles. The best accuracy we achieve on labeling a claim accompanied by the correct evidence is 31.87%, while if we ignore the evidence we achieve 50.91%. Thus we believe that FEVER is a challenging testbed that will help stimulate progress on claim verification against textual sources

The baseline model constists of two components: Evidence Retrieval (DrQA) + Textual Entailment (Decomposable Attention).

## Find Out More

 * Visit [http://fever.ai](http://fever.ai) to find out more about the shared task and download the data.

## Quick Links

 * [Installation](#installation)
 * [Data preparation](#data-preparation)
 * [Training](#training)
 * [Evaluation](#evaluation)
 * [Demo](#interactive-demo)

## Pre-requisites

This was tested and evaluated using the Python 3.6 verison of Anaconda 5.0.1 which can be downloaded from [anaconda.com](https://www.anaconda.com/download/)

Mac OSX users may have to install xcode before running git or installing packages (gcc may fail). 
See this post on [StackExchange](https://apple.stackexchange.com/questions/254380/macos-sierra-invalid-active-developer-path)

To train the Decomposable Attention models, it is highly recommended to use a GPU. Training will take about 3 hours on a GTX 1080Ti whereas training on a CPU will take days. We offer a pre-trained model.tar.gz that can be [downloaded](https://jamesthorne.co/fever/model.tar.gz). To use the pretrained model, simply replace any path to a model.tar.gz file with the path to the file you downloaded. (e.g. `logs/da_nn_sent/model.tar.gz` could become `~/Downloads/model.tar.gz`) 

## Installation

Create a virtual environment for FEVER with Python 3.6 and activate it

    conda create -n fever python=3.6
    source activate fever

Manually Install PyTorch (different distributions should follow instructions from [pytorch.org](http://pytorch.org/))

    conda install pytorch torchvision -c pytorch

Clone the repository

    git clone https://github.com/sheffieldnlp/fever-baselines
    cd fever-baselines

Install requirements (run `export LANG=C.UTF-8` if installation of DrQA fails)

    pip install -r requirements.txt

Download the FEVER dataset from [our website](https://sheffieldnlp.github.io/fever/data.html) into the data directory

    mkdir data
    mkdir data/fever-data
    
    #To replicate the paper, download paper_dev and paper_test files. These are concatenated for the shared task
    wget -O data/fever-data/train.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/train.jsonl
    wget -O data/fever-data/dev.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/paper_dev.jsonl
    wget -O data/fever-data/test.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/paper_test.jsonl
    
    #To train the model for the shared task (the test set will be released in July 2018)
    wget -O data/fever-data/dev.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/shared_task_dev.jsonl
    wget -O data/fever-data/test.jsonl https://s3-eu-west-1.amazonaws.com/fever.public/shared_task_test.jsonl
    
Download pretrained GloVe Vectors

    wget http://nlp.stanford.edu/data/wordvecs/glove.6B.zip
    unzip glove.6B.zip -d data/glove
    gzip data/glove/*.txt
    
## Data Preparation
The data preparation consists of three steps: downloading the articles from Wikipedia, indexing these for the Evidence Retrieval and performing the negative sampling for training . 

### 1. Download Wikipedia data:

Download the pre-processed Wikipedia articles from [our website](https://sheffieldnlp.github.io/fever/data.html) and unzip it into the data folder.
    
    wget https://s3-eu-west-1.amazonaws.com/fever.public/wiki-pages.zip
    unzip wiki-pages.zip -d data
 

### 2. Indexing 
Construct an SQLite Database and build TF-IDF index (go grab a coffee while this runs)

    PYTHONPATH=src python src/scripts/build_db.py data/wiki-pages data/fever/fever.db
    PYTHONPATH=src python src/scripts/build_tfidf.py data/fever/fever.db data/index/

### 3. Sampling
Sample training data for the NotEnoughInfo class. There are two sampling methods evaluated in the paper: using the nearest neighbour (similarity between TF-IDF vectors) and random sampling.

    #Using nearest neighbor method
    PYTHONPATH=src python src/scripts/retrieval/document/batch_ir_ns.py --model data/index/fever-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --count 1 --split train
    PYTHONPATH=src python src/scripts/retrieval/document/batch_ir_ns.py --model data/index/fever-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --count 1 --split dev

And random sampling

    #Using random sampling method
    PYTHONPATH=src python src/scripts/dataset/neg_sample_evidence.py data/fever/fever.db

    
## Training

Model 1: Multilayer Perceptron (expected oracle dev set performance: 62.27%)

    #If using a GPU, set
    export GPU=1
    #If more than one GPU,
    export CUDA_DEVICE=0 #(or any CUDA device id. default is 0)

    # Using nearest neighbor sampling method for NotEnoughInfo class (better)
    PYTHONPATH=src python src/scripts/rte/mlp/train_mlp.py data/fever/fever.db data/fever/train.ns.pages.p1.jsonl data/fever/dev.ns.pages.p1.jsonl --model ns_nn_sent --sentence true

    #Or, using random sampled data for NotEnoughInfo (worse)
    PYTHONPATH=src python src/scripts/rte/mlp/train_mlp.py data/fever/fever.db data/fever/train.ns.rand.jsonl data/fever/dev.ns.rand.jsonl --model ns_rand_sent --sentence true


Model 2: Decomposable Attention (expected dev set performance: 77.97%)

    #if using a CPU, set
    export CUDA_DEVICE=-1

    #if using a GPU, set
    export CUDA_DEVICE=0 #or cuda device id

    # Using nearest neighbor sampling method for NotEnoughInfo class (better)
    PYTHONPATH=src python src/scripts/rte/da/train_da.py data/fever/fever.db config/fever_nn_ora_sent.json logs/da_nn_sent --cuda-device $CUDA_DEVICE

    #Or, using random sampled data for NotEnoughInfo (worse)
    PYTHONPATH=src python src/scripts/rte/da/train_da.py data/fever/fever.db config/fever_rs_ora_sent.json logs/da_rs_sent --cuda-device $CUDA_DEVICE

Score:

    PYTHONPATH=src python src/scripts/score.py --predicted logs/da_nn_sent_test --actual data/fever-data/test.jsonl


## Evaluation

### Oracle Evaluation (no evidence retrieval):
    
Model 1: Multi-layer perceptron

    PYTHONPATH=src python src/scripts/rte/mlp/eval_mlp.py data/fever/fever.db --model ns_nn_sent --sentence true --log logs/mlp_nn_sent
    
Model 2: Decomposable Attention 
    
    PYTHONPATH=src python src/scripts/rte/da/eval_da.py data/fever/fever.db logs/da_nn_sent/model.tar.gz data/fever/dev.ns.pages.p1.jsonl
    
 
### Evidence Retrieval Evaluation:

#### Step 1: Retrive Evidence
    PYTHONPATH=src python src/scripts/retrieval/document/batch_ir.py --model data/index/fever-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --count 5 --split dev
    PYTHONPATH=src python src/scripts/retrieval/document/batch_ir.py --model data/index/fever-tfidf-ngram=2-hash=16777216-tokenizer=simple.npz --count 5 --split test

NLTK Sentence Selection (worse)

    PYTHONPATH=src python src/scripts/retrieval/sentence/process_tfidf.py data/fever/fever.db data/fever/dev.pages.p5.jsonl --max_page 5 --max_sent 5 --split dev
    PYTHONPATH=src python src/scripts/retrieval/sentence/process_tfidf.py data/fever/fever.db data/fever/test.pages.p5.jsonl --max_page 5 --max_sent 5 --split test

DrQA Sentence Selection (better)

    PYTHONPATH=src python src/scripts/retrieval/sentence/process_tfidf_drqa.py --db data/fever/fever.db --in_file data/fever/dev.pages.p5.jsonl --max_page 5 --max_sent 5 --split dev --use_precomputed false
    PYTHONPATH=src python src/scripts/retrieval/sentence/process_tfidf_drqa.py --db data/fever/fever.db --in_file data/fever/test.pages.p5.jsonl --max_page 5 --max_sent 5 --split test --use_precomputed false
    
(note that this produces data with a different name to DrQA, you can run `mv data/fever/dev.sentences.not_precomputed.p5.s5.jsonl data/fever/dev.sentences.p5.s5.jsonl` and `mv data/fever/test.sentences.not_precomputed.p5.s5.jsonl data/fever/test.sentences.p5.s5.jsonl` to evaluate on this data)


#### Step 2: Run Model
Model 1: Multi-layer perceptron

    PYTHONPATH=src python src/scripts/rte/mlp/eval_mlp.py data/fever/fever.db data/fever/dev.sentences.p5.s5.jsonl --model ns_nn_sent --sentence true --log logs/mlp_nn_sent_dev
    PYTHONPATH=src python src/scripts/rte/mlp/eval_mlp.py data/fever/fever.db data/fever/test.sentences.p5.s5.jsonl --model ns_nn_sent --sentence true --log logs/mlp_nn_sent_test
    
Model 2: Decomposable Attention 
    
    PYTHONPATH=src python src/scripts/rte/da/eval_da.py data/fever/fever.db logs/da_nn_sent/model.tar.gz data/fever/dev.sentences.p5.s5.jsonl  --log logs/da_nn_sent_dev
    PYTHONPATH=src python src/scripts/rte/da/eval_da.py data/fever/fever.db logs/da_nn_sent/model.tar.gz data/fever/test.sentences.p5.s5.jsonl  --log logs/da_nn_sent_test


#### Step 3a: Score locally  
Score:

    PYTHONPATH=src python src/scripts/score.py --predicted_labels logs/da_nn_sent_test --predicted_evidence data/fever/test.sentences.p5.s5.jsonl --actual data/fever-data/test.jsonl

#### Step 3b: Or score on Codalab

Prepare Submission for Codalab:

    PYTHONPATH=src python src/scripts/prepare_submission.py --predicted_labels logs/da_nn_sent_test --predicted_evidence data/fever/test.sentences.p5.s5.jsonl --out_file predictions.jsonl
    zip submission.zip predictions.jsonl

          
