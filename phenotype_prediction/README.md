# Type I Diabetes Prediction from Whole Shotgun Metagenome of Human Infant Gut

## Background
A somewhat recent IBM Research study [(Carrieri et al., 2019)](https://research.ibm.com/publications/a-fast-machine-learning-workflow-for-rapid-phenotype-prediction-from-whole-shotgun-metagenomes) introduces a process for rapid phenotype prediction from whole shotgun metagenomic data. It primarily makes use of a dimensionality reduction technique called [HULK (Histosketching Using Little K-mers)](https://github.com/will-rowe/hulk) as introduced by [Rowe et al. (2018)](https://www.biorxiv.org/content/10.1101/408070v1.full.pdf). Amusingly, it is one of many related tools named after Marvel characters. It provides a compact representation (in KB) of the whole metagenome (which can be multiple GB in magnitude) that can be utilised for classification tasks, acting as a feature vector for ML models. It extends the work of [Asgari et. al (2018)](https://pubmed.ncbi.nlm.nih.gov/30500871/) that showed the use of k-mer distributions outperforms Operational Taxonomic Units (OTU) as features. That is by utilising the whole shotgun metagenome rather than their 16S rRNA sequence.

Another study [(Kostic et al., 2015)](https://www.cell.com/cell-host-microbe/fulltext/S1931-3128(15)00021-9) explores the relationship between the progression of type I diabetes (T1D) with the gut microbiome diversity of infants. Notably, they have their [metagenomic sequence data publicly available](https://diabimmune.broadinstitute.org/diabimmune/t1d-cohort/resources/metagenomic-sequence-data). In total, there are 124 samples from 19 subjects collected at different periods as well as their T1D diagnosis. Using the relatively new technique of histosketching, I sought the viability of using prediction models for this use case.

## Methodology
Whole genome shotgun (WGS) sequences from the study carried out by [Kostic et al. (2015)](https://www.cell.com/cell-host-microbe/fulltext/S1931-3128(15)00021-9) were retrieved and pairs of paired-end FASTQ files were interleaved. These were then histosketched to produce feature vectors. Sketch sizes of 50 (default) and 512 (used in IBM paper) were both explored, but only the 512-sized sketches results are laid out below. Each sample took approximately ten minutes in total to process (~four min. for downloading and interleaving and six min. for histosketching) and took roughly 22 hours of runtime on a c6i.4xlarge AWS EC2 instance. 

As the data was fairly imbalanced (only about a quarter resulted in T1D), the Synthetic Minority Oversampling technique (SMOTE) was employed. LASSO was further used to narrow down statistically relevant features. Out of 512 features, 19 were considered. Classification models used parallel that of the IBM paper, namely: Relevance Vector Machines (RVM), Support Vector Machines (SVM), Random Forests (RF), and Naive Bayes (NB). Similarly, for their performance metrics, each is trained with 80% of the data and tested on the remaining 20%. Ten-fold cross-validation (CV) was performed to quantify oversampling issues (which is particular for SMOTE-applied datasets). Training and testing took about 2.5 minutes in total.

## Results
Notably, the CV results suggest little sign of overfitting despite using SMOTE. Although, a greater number of samples is likely required for more conclusive results. Similar to the paper, the SVM model performed the best, followed by that of RF, RVM, and lastly NB, albeit by minuscule margins. The results are as follows:

| |RVM Regular|RVM Lasso|SVM Regular|SVM Lasso|RF Regular|RF Lasso|NB Regular|NB Lasso|
|:----|:----|:----|:----|:----|:----|:----|:----|:----|
|Train|**1.000000**|0.993377|**1.000000**|0.978417|**1.000000**|**1.000000**|0.883436|0.919708|
|Test|0.933333|0.812500|**1.000000**|0.952381|0.971429|0.976744|0.894737|0.926829|
|Mean CV|0.921555|0.935437|0.971282|0.895584|**0.976667**|0.872031|0.834162|0.845405|
|Std CV|0.086265|0.049469|**0.035321**|0.077666|0.051747|0.087467|0.073676|0.157911|

From the above, it can be inferred that T1D diagnosis could be considered among viable classification tasks for models.

## Further Discussion
Initially, a sketch size of 50 was used but did not produce satisfactory results within the models. These are still available in the `sketches` folder. A point of interest is investigating the optimality of sketch size and how it varies from dataset to dataset. Although, a caveat might be the computationally expensive nature of creating multiple batches of sketches. Another of interest is the prospective use of Lasso for determining which bins have some correspondence to the phenotype studied. If these bins could be characterised somehow, such as in terms of the taxonomy of microorganisms, this could be incredibly useful. As an example, the results of Kostic et. al's (2015) study suggest that an increase in inflammation-associated organisms precedes the onset of T1D. A mapping between the sketch and such info could make a great case for the more widespread use of histosketching over 16S rRNA sequencing.


