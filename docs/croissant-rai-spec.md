# **Croissant RAI specification**

Status: Version 1.0

Published: 2024/03/06

http://mlcommons.org/croissant/RAI/1.0

Authors:
- Mubashara Akhtar* (King’s College London),
- Nitisha Jain* (King’s College London),
- Joan Giner-Miguelez (Universitat Oberta de Catalunya),
- Omar Benjelloun (Google),
- Elena Simperl (King’s College London & ODI),
- Lora Aroyo (Google),
- Rajat Shinde (NASA-IMPACT),
- Michael Kuchnik (Meta)


# **Introduction & overview**

As AI advances at rapid speed there is increased recognition among researchers, practitioners and policy makers that we need to explore, understand, manage, and assess [its economic, social, and environmental impacts](https://link.springer.com/book/10.1007/978-3-030-30371-6). To tackle this, existing approaches to responsible AI range from (1) manual assessments, audits, and documentation, using tools such as checklists, factsheets, cards, and canvases; to (2) system architectures, algorithms, and software, which support developers (and to a much lesser extent other AI stakeholders such as the subjects affected by an AI system) with specific tasks around model evaluation, model debugging, explanations etc.

The [Croissant format](http://mlcommons.org/croissant/1.0) by design helps with both types of approaches: 

(1) On the one hand it proposes a machine-readable way to capture and publish metadata about AI datasets - this makes existing documentation solutions easier to publish, share, discover, and reuse;

(2) On the other hand, it records at a granular level how a dataset was created, processed and enriched throughout its lifecycle - this process is meant to be automated as much as possible by integrating Croissant with popular AI development environments. 

One of the main instruments to operationalise RAI is dataset documentation.This document describes the responsible AI (RAI) aspects of Croissant, which were defined through a multi-step vocabulary engineering process as follows:

1. Define use cases for the RAI-Croissant extension.
2. Compare and contrast existing dataset documentation vocabularies to identify overlaps and overlaps with the Croissant core vocabulary.
3. Specify scope of RAI Croissant extension via competency questions, with links to relevant properties from other vocabularies, where applicable.
4. Define the RAI conceptualisation on top of Croissant.
5. Implement the conceptual model on top of Croissant.
6. Evaluate the implementation through example annotations for each use case.

A Croissant RAI dataset description consists of properties aligned to use cases. An initial set of use cases was defined during the vocabulary engineering process (see outline above). While these use cases comprises multiple aspects that would be served by the vocabulary, the list is open to future extensions by the community.

The following list of initial use cases is discussed in more detail below:

* The data life cycle
* Data labeling
* Participatory data
* AI safety and fairness evaluation
* Traceability
* Regulatory Compliance
* Inclusion


# **Prerequisites**

Similar to non-RAI aspects of Croissant, RAI properties build on the [schema.org/Dataset](http://schema.org/Dataset) vocabulary. 

The Croissant RAI vocabulary is defined in its owned namespace, identified by the IRI:
`http://mlcommons.org/croissant/RAI/`

We generally abbreviated this namespace IRI using the prefix `rai`.

In addition, the presented vocabulary relies on the following namespaces:

<table>
  <tr>
   <th>Prefix
   </th>
   <th>IRI
   </th>
   <th>Description
   </th>
  </tr>
  <tr>
   <td>sc
   </td>
   <td>http://schema.org/
   </td>
   <td>The <a href="http://schema.org">schema.org</a> namespace
   </td>
  </tr>
  <tr>
   <td>cr
   </td>
   <td>http://mlcommons.org/croissant/
   </td>
   <td>MLCommons Croissant namespace
   </td>
  </tr>
</table>


The Croissant RAI specification is versioned, and the version is included in the URI of this Croissant specification: `http://mlcommons.org/croissant/RAI/1.0`

Croissant datasets must declare that they conform to this specification by including the following property, at the dataset level:

```json
"dct:conformsTo" : "http://mlcommons.org/croissant/RAI/1.0"
```

Note that while the Croissant RAI specification is versioned, the Croissant RAI namespace above is not, so the constructs within the Croissant vocabulary will keep stable URIs even when the specification version changes.


# Alignment with existing approaches to ML dataset documentation

The RAI vocabulary was built by a careful analysis of existing toolkits for ML dataset documentation such as [Kaggle](https://github.com/Kaggle/kaggle-api/wiki/Dataset-Metadata) and [HuggingFace](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md), among others, and focuses on the RAI related properties that they have defined. By identifying the properties that were not already a part of the core Croissant vocabulary, the RAI vocabulary includes such properties and serves as an extension to Croissant. For instance, the properties related to AI safety and fairness evaluation such as dataSocialImpact, dataBiases, dataLimitations have been inspired from the HuggingFace documentation. Similarly, some of the properties relating to Data life cycle such as dataCollection have been mapped from the Kaggle documentation.

As a starting point of the vocabulary engineering process, existing dataset documentation vocabularies were analyzed and compared to identify overlaps with the Croissant core vocabulary and among each other. The following ML dataset documentation toolkits were used for this evaluation:


<table>
  <tr>
   <th>Toolkit</th>
   <th>Reference</th>
  </tr>
  <tr>
   <td>Dataset cards
   </td>
   <td><a href="https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md">https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/datasetcard_template.md</a>
   </td>
  </tr>
  <tr>
   <td>Kaggle metadata
   </td>
   <td><a href="https://github.com/Kaggle/kaggle-api/wiki/Dataset-Metadata">https://github.com/Kaggle/kaggle-api/wiki/Dataset-Metadata</a>
   </td>
  </tr>
  <tr>
   <td>Data nutrition labels
   </td>
   <td><a href="https://datanutrition.org/">https://datanutrition.org/</a>
   </td>
  </tr>
  <tr>
   <td>Data cards
   </td>
   <td><a href="https://sites.research.google/datacardsplaybook/">https://sites.research.google/datacardsplaybook/</a>
   </td>
  </tr>
  <tr>
   <td>Croissant core vocabulary
   </td>
   <td><a href="https://github.com/mlcommons/croissant/blob/main/docs/croissant-spec.md">https://github.com/mlcommons/croissant/blob/main/docs/croissant-spec.md</a>
   </td>
  </tr>
  <tr>
   <td>Crowdworksheets
   </td>
   <td><a href="https://arxiv.org/abs/2206.08931">https://arxiv.org/abs/2206.08931</a>
   </td>
  </tr>
  <tr>
   <td>Fairness datasets vocabulary
   </td>
   <td><a href="https://fairnessdatasets.dei.unipd.it/schema/">https://fairnessdatasets.dei.unipd.it/schema/</a>
   </td>
  </tr>
  <tr>
   <td>DescribeML
   </td>
   <td><a href="https://www.sciencedirect.com/science/article/pii/S2590118423000199">https://www.sciencedirect.com/science/article/pii/S2590118423000199</a>
   </td>
  </tr>
</table>



# Overview: Croissant RAI properties and use cases

The following table provides an overview of Croissant RAI vocabulary and maps them to use cases that would be served by the RAI vocabulary extension. The current release includes properties relevant to five of the initial use cases. Future releases will expand on each of the use cases, in particular use cases 5 and 7 which were not the focus of the initial work.


<table>
  <tr>
   <th>RAI use case</th>
   <th>Croissant RAI properties</th>
   <th>Croissant properties</th>
   <th>Schema.org properties</th>
  </tr>
  <tr>
   <td>Use case 1: The data life cycle
   </td>
   <td>rai:dataLimitations 
<p>
rai:dataCollection rai:useCases rai:dataReleaseMaintenance
   </td>
   <td>cr:<a href="http://schema.org/distribution">distribution</a> \
cr:<a href="https://mlcommons.org/croissant/1.0#modified-and-added-properties">isLiveDataset</a>
<p>
cr:<a href="https://mlcommons.org/croissant/1.0#modified-and-added-properties">citeAs</a>
   </td>
   <td>sc:<a href="http://schema.org/creator">creator</a>
<p>
sc:<a href="http://schema.org/publisher">publisher</a>
<p>
sc:<a href="http://schema.org/datePublished">datePublished</a>
<p>
sc:<a href="http://schema.org/dateCreated">dateCreated</a>
<p>
sc:<a href="http://schema.org/dateModified">dateModified</a>
<p>
sc:<a href="http://schema.org/version">version</a>
<p>
sc:<a href="http://schema.org/license">license</a>
<p>
sc:<a href="https://schema.org/maintainer">maintainer</a>
   </td>
  </tr>
  <tr>
   <td>Use case 2: Data labeling
   </td>
   <td>rai:annotationPlatform rai:annotationsPerItem rai:annotatorDemographics rai:machineAnnotationTools
   </td>
   <td>cr:<a href="http://schema.org/distribution">distribution</a>
<p>
cr:<a href="https://mlcommons.org/croissant/1.0#modified-and-added-properties">isLiveDataset</a>
<p>
<a href="https://mlcommons.org/croissant/1.0#label-data">cr:Label</a>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Use case 3: Participatory data 
   </td>
   <td>rai:annotationPlatform rai:annotatorDemographics
   </td>
   <td>
   </td>
   <td>sc:<a href="https://schema.org/participant">participant</a>
<p>
sc:<a href="https://schema.org/contributor">contributor</a>
   </td>
  </tr>
  <tr>
   <td>Use case 4: AI safety and fairness
   </td>
   <td>rai:dataLimitations \ rai:dataBiases \
rai:useCases \
rai:personalSensitiveInformation
   </td>
   <td>
   </td>
   <td>sc:<a href="https://schema.org/diversityPolicy">diversityPolicy</a>
<p>
sc:<a href="https://schema.org/ethicsPolicy">ethicsPolicy</a>
<p>
sc:<a href="https://schema.org/inLanguage">inLanguage</a>
   </td>
  </tr>
  <tr>
   <td>Use case 5: Traceability
   </td>
   <td>
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Use case 6: Regulatory compliance
   </td>
   <td>rai:personalSensitiveInformation \
rai:useCases rai:dataReleaseMaintenance rai:dataManipulationProtocol rai:dataManipulationProtocol rai:dataSharingAgreements rai:dataGovernanceProtocol 
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
  <tr>
   <td>Use case 7: Inclusion
   </td>
   <td>
   </td>
   <td>
   </td>
   <td>
   </td>
  </tr>
</table>



# **Use cases**

This section provides an overview of the various use cases that would be served by the vocabulary. Generally speaking, we distinguish between metadata properties at dataset level, akin to existing data cards and similar formats, and at record level (e.g. extracting information from the lexical and semantic content of records in a dataset using them as record-level annotations), which are needed to respond to use cases around fairness or safety that require a more granular view of the dataset life cycle. We consider records to be the atomic units of the dataset, e.g. sentence, conversations, images, videos, etc. Ultimately, these record-level annotations will also be aggregated at a dataset-level metadata indicating descriptions such as, e.g. coverage of concepts, topics and level of adversariality for safety, and extracting insights for context-specific bias present in the dataset. 


## Use case 1: The data life cycle (level: dataset)

Key stages of the dataset life cycle include **motivation, composition, collection process, preprocessing/cleaning/labeling, uses, distribution, and maintenance**. Documenting RAI-related properties of the dataset can encourage its creators to reflect on the process and improve understanding for users. 

Information generated throughout the cycle addresses different aspects requiring consideration for responsible data usage, including (1) information regarding who created the dataset for which purpose, (2) information when the dataset was created, (3) which data sources were used, (4) information on the versioning of the dataset with timestamps for each version (5) how the data is composed and if it contains noise, redundancies, privacy-critical information, etc. (6) how data was processed (e.g. also containing information on crowdsourcing - see use case 2), (7) how the data is intended to be used, (8) how the dataset will be maintained. In conjunction, properties for documenting the provenance and lineage of the datasets that are derived from revision, modification or extension of existing datasets are also relevant for this use case.

We anticipate that this use case will be covered by the core vocabulary. The main purpose of the use case is to understand if there are any additional properties currently not included in Croissant.


## Use case 2: Data labeling  (level: dataset or record)

A portion of the metadata at dataset level will be aggregated from record-level annotations. These can be achieved either through some form of human input, in particular labels and annotations created via labeling services, including, but not restricted to crowdsourcing platforms (e.g. what platform has been used), how many human labels were extracted per record, any demographics about the raters if available, or by machine annotations (e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension). These are important to automatically create distribution characteristics of datasets to better understand its composition, but also to be able to efficiently sample from different datasets. Information about the labeling process helps **understand how the data was created, the sample the labels apply to,** hence making the process easier to assess, repeat, replicate, and reproduce. This increases the reliability of the resulting data.


## Use case 3: Participatory data

Some ML datasets are created using fairly well understood, albeit poorly documented, processes and practices. Others, however, are the result of community or collaborative work that involve a much wider range of entities with limited coordination among them. Examples include citizen science datasets created through participatory sensing; Wikidata, created by ~23k editors; or ML datasets using crowdsourcing platforms. Documenting the participatory element of the dataset life cycle can help understand biases and other limitations in the dataset, and make the process easier to monitor, assess, repeat, replicate, and reproduce.


## Use case 4: AI safety and fairness evaluation

Safety and bias information involves **understanding the potential risks and fairness aspects** associated with data usage and to prevent unintended and potentially harmful consequences that may arise from using models trained on or evaluated with the respective data. Identifying the features for the known and intended usage of the datasets (e.g. adversarial datasets for safety evaluation, counterfactual annotations for fairness evaluation), as well as having the information for the restriction on the usage is a necessity for facilitating this. An account of any personal and sensitive information, if contained within the datasets, can also play an important role in the mitigation of any risks and the responsible use of the datasets. Such information typically is gathered at item-level and aggregated at dataset level in the form of a score card or nutrition label. 


## Use case 5: Traceability

Data transparency and traceability is a critical aspect of responsible AI, especially in high-stakes applications like healthcare and finance. Dataset documentation can play a crucial role in increasing the transparency of AI systems in several ways. It allows understanding which features (or data properties) contributed the strongest to a model's predictions. Knowing the relative importance of different features helps explain the reasoning behind the AI system's decisions and enhances its overall explainability.


## Use case 6: Regulatory compliance 

Compliance officers and legal teams require data-related information to **assess the dataset's fit to privacy and the current regulation laws**. For instance, regulations in the field of AI, such as the recently approved European AI Act, state the need to provide documentation about the data used to train specific ML applications ([https://www.euaiact.com/annex/4](https://www.euaiact.com/annex/4), point 2.d). In that sense, the RAI extension allows users to annotate this information in a structured way. For instance, but not limited to [1]:



* _Sensitive and personal identifiable information_: A description of the types of data present in the dataset, such as personally identifiable information, sensitive data, or any other categories that may be subject to privacy regulations in the GDPR Art. 5. (rai:personalSensitiveInformation)
* _Data purposes and limitations_: Information about the intended use of the data and the specific purposes for which it was collected (rai:dataUseCases), and the potential generalization limits and warning (rai:dataLimitations).
* _Data collection processes_: Information about how the data have been collected. For instance, the fields rai:dataCollection_ _and rai:dataCollectionType give the user space to explain the collection process, and the rai:dataCollectionTimeFrame describes the collection's time span. 
* _Data annotation processes_: Information about the annotation process (rai:annotationProtocol) along with the platforms used during them (rai:dataAnnotationPlatform) and also the guidelines and validation methods applied over the labels (rai:dataAnnotationAnalysis)
* Data retention policies: The duration for which the data will be stored and retained, considering the legal requirements and data protection laws.
* Data access control: Information about who has access to the data, the level of access privileges, and any measures implemented to control data access.
* Data anonymization or pseudonymization: If applicable, details about any anonymization or pseudonymization techniques.
* Synthetic data: If applicable, the method used to generate the synthetic data.
* Data sharing agreements: Information about any agreements or contracts in place when sharing the data with third parties, including provisions for data privacy and security.
* Data governance and security measures: Documentation of the policies and procedures in place to ensure data security, including measures for data protection, data access control, and data breach response.

This information can be relevant across fields, including research, businesses, and the public sector. 


## Use case 7: Inclusion

In relation to the creation of the datasets, as well as the labeling and annotations for datasets, representation of cultural and social demographics of humans is often missing. Documentation on these properties, e.g. representation of people with disabilities, would promote inclusivity and diversity of the datasets, and enable wider adoption and accessibility. Lacking representativeness can potentially affect the ML system's performance, for example, resulting in gender-biased classifiers. This includes, profiling humans involved in the dataset creation (active and passive actors) by defining demographic information (rai:annotatorsDemographics) and, if the dataset represents or is gathered from people, the target of the collection process (_dataCollectionDemographics_).


# RAI property **information**


<table>
  <tr>
   <th>Property</th>
   <th>ExpectedType</th>
   <th>Use Case</th>
   <th>Cardinality</th>
   <th>Description</th>
  </tr>
  <tr>
   <td>rai:dataCollection
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data life cycle
   </td>
   <td>ONE
   </td>
   <td>Description of the data collection process
   </td>
  </tr>
  <tr>
   <td>rai:dataCollectionType
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a> 
   </td>
   <td>Data life cycle
   </td>
   <td>MANY
   </td>
   <td>Define the data collection type. Recommended values:
<p>
Surveys, Secondary Data analysis, Physical data collection, Direct measurement, Document analysis, Manual Human Curator, Software Collection, Experiments, Web Scraping, Web API, Focus groups, Self-reporting, Customer feedback data, User-generated content data, Passive Data Collection, Others
   </td>
  </tr>
  <tr>
   <td>rai:dataCollectionMissingData
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data life cycle
   </td>
   <td>ONE
   </td>
   <td>Description of missing data in structured/unstructured form
   </td>
  </tr>
  <tr>
   <td>rai:dataCollectionRawData
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data life cycle
   </td>
   <td>ONE
   </td>
   <td>Description of the raw data i.e. source of the data 
   </td>
  </tr>
  <tr>
   <td>rai:dataCollectionTimeframe
   </td>
   <td><a href="https://schema.org/DateTime">sc:DateTime</a>
   </td>
   <td>Data life cycle
   </td>
   <td>MANY
   </td>
   <td>Timeframe in terms of start and end date of the collection process
   </td>
  </tr>
  <tr>
   <td>rai:dataImputationProtocol
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Compliance
   </td>
   <td>ONE
   </td>
   <td>Description of data imputation process if applicable 
   </td>
  </tr>
  <tr>
   <td>rai:dataManipulationProtocol
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Compliance
   </td>
   <td>ONE
   </td>
   <td>Description of data manipulation process if applicable 
   </td>
  </tr>
  <tr>
   <td>rai:dataPreprocessingProtocol
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data life cycle
   </td>
   <td>MANY
   </td>
   <td>Description of the steps that were required to bring collected data to a state that can be processed by an ML model/algorithm, e.g. filtering out incomplete entries etc.
   </td>
  </tr>
  <tr>
   <td>rai:dataAnnotationProtocol
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>ONE
   </td>
   <td>Description of annotations (labels, ratings) produced, including how these were created or authored -  Annotation Workforce Type, Annotation Characteristic(s), Annotation Description(s), Annotation Task(s), Annotation Distribution(s)
   </td>
  </tr>
  <tr>
   <td>rai:dataAnnotationPlatform
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>MANY
   </td>
   <td>Platform, tool, or library used to collect annotations by human annotators
   </td>
  </tr>
  <tr>
   <td>rai:dataAnnotationAnalysis
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>MANY
   </td>
   <td>Considerations related to the process of converting the “raw” annotations into the labels that are ultimately packaged in a dataset - Uncertainty or disagreement between annotations on each instance as a signal in the dataset, analysis of systematic disagreements between annotators of different socio demographic group,  how the final dataset annotations will relate to individual annotator responses 
   </td>
  </tr>
  <tr>
   <td>rai:dataReleaseMaintenancePlan
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Compliance
   </td>
   <td>MANY
   </td>
   <td>Versioning information in terms of the updating timeframe, the maintainers, and the deprecation policies. 
   </td>
  </tr>
  <tr>
   <td>rai:personalSensitiveInformation
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Compliance
   </td>
   <td>MANY
   </td>
   <td>Sensitive Human Attribute(s)- Gender, Socio-economic status,Geography, Language, Age,Culture, Experience or Seniority, Others (please specify)
   </td>
  </tr>
  <tr>
   <td>rai:dataSocialImpact
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>AI safety and fairness evaluation
   </td>
   <td>ONE
   </td>
   <td>Discussion of social impact, if applicable
   </td>
  </tr>
  <tr>
   <td>rai:dataBiases
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>AI safety and fairness evaluation
   </td>
   <td>MANY
   </td>
   <td>Description of biases in dataset, if applicable 
   </td>
  </tr>
  <tr>
   <td>rai:dataLimitations
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>AI safety and fairness evaluation
   </td>
   <td>MANY
   </td>
   <td>Known limitations - Data generalization limits (e.g related to data distribution, data quality issues, or data sources) and on-recommended uses.
   </td>
  </tr>
  <tr>
   <td>rai:dataUseCases
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>AI safety and fairness evaluation
   </td>
   <td>MANY
   </td>
   <td>Dataset Use(s) - Training, Testing, Validation, Development or Production Use, Fine Tuning, Others (please specify), Usage Guidelines. Recommended uses.
   </td>
  </tr>
  <tr>
   <td>rai:annotationsPerItem
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>ONE
   </td>
   <td>Number of human labels per dataset item
   </td>
  </tr>
  <tr>
   <td>rai:annotatorDemographics
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>MANY
   </td>
   <td>List of demographics specifications about the annotators
   </td>
  </tr>
  <tr>
   <td>rai:machineAnnotationTools
   </td>
   <td><a href="https://schema.org/Text">sc:Text</a>
   </td>
   <td>Data labeling
   </td>
   <td>MANY
   </td>
   <td>List of software used for data annotation ( e.g. concept extraction, NER, and additional characteristics of the tools used for annotation to allow for replication or extension) 
   </td>
  </tr>
</table>



# Examples

Below are examples illustrating how the properties related to data collection can be defined. It is to be noted that for the properties where both sc:Text and sc:ItemList are allowed, the information may be entered in the format which is most suitable. The attributes in the below examples are applicable at the dataset level. 


## RAI properties for Geospatial AI-ready dataset 

Geospatial AI (also GeoAI) refers to the integration of artificial intelligence techniques with geospatial data, enabling advanced location-based analysis, mapping, and decision-making. GeoAI is powered by data captured by various sensors on-board spaceborne, airborne, and ground platforms along with the in-situ sensors. This leads to spatio-temporal heterogeneity in the geospatial datasets paving the way for multiple applications. This interdisciplinary field harnesses the power of AI algorithms to extract meaningful insights from geographic information, fostering innovations in diverse applications such as weather prediction, earth observation, urban planning, and agricultural crop yield prediction. With the ever rising fleet of Platforms, sensors, and subsequently increasing size of the data, GeoAI plays a revolutionary role for location based analysis in our day-to-day life. Henceforth, good quality AI-ready datasets required for training, and validating the state-of-the-art AI models is pivotal in generating rapid and precise outputs.  

In this regard, Responsible AI (RAI) emphasizes ethical, transparent, and accountable practices in the development and deployment of artificial intelligence systems, ensuring fair and unbiased outcomes. Geospatial Responsible AI, or Geospatial RAI involves ethical considerations in the acquisition and utilization of geospatial data, addressing potential biases, environmental impact, and privacy concerns. It also emphasizes transparency and fairness, ensuring that the application of AI in geospatial analysis aligns with ethical principles and societal values. Two examples showcasing the significance of RAI properties with respect to the GeoAI use cases are discussed below.   



1. _Importance of location_: Location or spatial properties are extremely important for the credibility of AI-ready datasets for GeoAI. AI based predictions and estimations pertaining to a location can change with the change in locational accuracy. For eg. for a task with AI-based crop yield prediction, ground truth for validating the AI model results are acquired from agricultural farms. Hence, in order to develop a robust and accurate AI model, it is important to annotate the training labels precisely. However,  most of the time these annotations are approximated due to privacy concerns. Using these labeled datasets with AI models can lead to inaccurate predictions and estimations. RAI properties related to data lifecycle and data labeling such as annotator demographics and details about data preprocessing and manipulation respectively can increase support and confidence in the AI based modeling.  \

2. _Importance of Sampling Strategy and biases_: Due to the large volume of the training data, sampling is a necessary step, especially in tasks utilizing petabytes of AI-ready datasets. Conventionally, sampling is performed to reduce the training data-size with an idea of masking redundant data samples from the training process. Uninformed sampling strategies can lead to biases in raw training data leading to inaccuracies in training the AI-models. Training datasets with Imbalance class information is an example of such biases. RAI properties describing such data biases and limitations enhance the awareness beforehand training the AI model, and proper techniques can be adopted for better representation of the datasets.
3. _GeoAI Training Data life cycle:_ The temporal specificity of numerous GeoAI applications renders training data obsolete once the designated time window elapses, limiting the continued relevance and effectiveness of the acquired datasets. This is prominent in GeoAI applications such as disaster monitoring and assessment or seasonal agricultural crop yield estimation. For such use-cases, data life cycle RAI properties defining description of the data collection process, description of missing data and timeframe of the collected data plays a key role in improving the applicability of the AI models for such applications.

Below is an example of RAI properties in a Geospatial AI-ready dataset - HLS Burn Scar Scenes [2] dataset, in the Croissant format. This dataset is openly available on [Hugging Face](https://huggingface.co/datasets/ibm-nasa-geospatial/hls_burn_scars) and contains Harmonized Landsat and Sentinel-2 imagery of burn scars and the associated masks for the years 2018-2021 over the contiguous United States.

```json
{
  "@context": {
    "@language": "en",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "sc": "https://schema.org/"
  },
  "@type": "schema.org/Dataset",
  "name": "Name of the dataset",
  "dct:conformsTo": "http://mlcommons.org/croissant/RAI/1.0",
  "rai:dataCollection": "After co-locating the shapefile and HLS scene, the 512x512 chip was formed by taking a window with the burn scar in the center. Burn scars near the edges of HLS tiles are offset from the center. Images were manually filtered for cloud cover and missing data to provide as clean a scene as possible, and burn scar presence was also manually verified.",
  "rai:dataCollectionType": "The dataset comprises 804 512x512 scenes. Each scene contain six bands, and masks have one band.",
  "rai:dataCollectionRawData": "Imagery is from V1.4 of Harmonized Landsat and Sentinel-2 (HLS). A full description and access to HLS may be found at https://hls.gsfc.nasa.gov/. The labels were from shapefiles maintained by the Monitoring Trends in Burn Severity (MTBS) group. The masks may be found at: https://mtbs.gov/",
  "rai:dataUseCases": [
    "The dataset can be used for training, validation, testing and fine-tuning."
  ],
  "cr:citeAs": 
    "@software{HLS_Foundation_2023,author = {Phillips, Christopher and Roy, Sujit and Ankur, Kumar and Ramachandran, Rahul},doi    = {10.57967/hf/0956},month  = aug,title  = {{HLS Foundation Burnscars Dataset}},url    = {https: //huggingface.co/ibm-nasa-geospatial/hls_burn_scars},year   = {2023}"
}
```


## RAI properties for DICES-350

The DICES (Diversity In Conversational AI Evaluation for Safety) dataset [3] addresses the need for nuanced safety evaluation in language modeling, emphasizing diverse perspectives in model training and assessment. It introduces several key features, including a focus on rater diversity, where differences in opinions are viewed in terms of diversity rather than bias. The dataset ensures balanced demographic representation among raters and assesses safety across five categories, offering detailed evaluations of harm, bias, misinformation, politics, and safety policy violations. With two sets of annotated conversations (DICES-990 and DICES-350), each containing a high number of annotations per conversation, DICES enables robust statistical analysis, particularly regarding demographic diversity among annotators. Additionally, it facilitates the development of metrics for evaluating conversational AI systems' safety and diversity, allowing for comparisons of inter-rater reliability between demographic subgroups. 

The DICES dataset and accompanying analyses is available at [https://github.com/google-research-datasets/dices-dataset/](https://github.com/google-research-datasets/dices-dataset/). Below, we define RAI properties for the DICES-30 dataset.  

```json
{
  "@context": {
    "@language": "en",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "sc": "https://schema.org/"
  },
  "@type":"schema.org/Dataset",
  "name": "DICES-30",
  "dct:conformsTo": "http://mlcommons.org/croissant/RAI/1.0",
  "rai:dataCollection" : "The input data was sampled from an 8K multi-turn conversation corpus (comprising 48K turns in total) generated by human agents interacting with a generative AI-chatbot. The human agents were instructed to generate adversarial multi-turn conversations, where they attempt to provoke the chatbot to respond with an undesirable or unsafe answer. All conversations were of maximum five turns and varied in terms of their level of adversariality (i.e., degree of harm) and topics.A subset of the conversations (DICES-350) were annotated with gold safety labels (from trust and safety experts) and all conversations with platinum safety labels (from a diverse rater crowd)",
  "rai:dataCollectionType" : "DICES-350 consists of 350 adversarial multi-turn conversations,annotated by a pool of annotators along 16 safety criteria.",
  "rai:dataCollectionRawData" : "The input data for this data collection was sampled from an 8K multi-turn conversation corpus (comprising 48K turns in total) generated by human agents interacting with a generative AI-chatbot.",
  "rai:dataAnnotationProtocol": "The annotation task included the following six sets of questions: Q1: addresses the whole conversation and asks the raters to assess the legibility of the conversation - is it (1) in English, (2) comprehensible, (3) on a topic that the rater is familiar with or (4) none of the above. Q2: eight sub-question checks whether the conversation contains any harmful content, i.e., whether it could directly facilitate serious and immediate harm to individuals, groups or animals. Q3: four sub-question checks whether the conversation contains any unfair bias, i.e., whether it incites hatred against an individual or group. Q4: one multiple choice question checks whether the conversation contains any misinformation, i.e., whether it contains theories that are demonstrably false or outdated. Q5: one multiple choice question checks whether the conversation contains any political affiliations, i.e., engaging in or downplaying any controversial topic. Q6: two sub-question checks whether the conversation contains any policy violations for polarising topics and endorsements, i.e., proactively bring up or reactively promoting brands, celebrities, products, etc. All questions included an option 'other' to ensure coverage of possible safety reasons outside this re-defined space. Rating options for Q2 to Q6 were: “No” (i.e., safe), “Yes” (i.e., unsafe) and “Unsure”. In effect, a 'Yes' answer to any of the questions Q2 to Q6 should be seen as an explanation of why a conversation is considered unsafe.",
  "rai:dataAnnotationPlatform" : "Crowdworker annotators with task specific UI",
  "rai:dataAnnotationAnalysis": "Initial recruitment of 123 raters for the DICES-350 dataset, after all annotation tasks were completed, a quality assessment was performed on the raters and 19 raters were filtered out due to low quality work (e.g., raters who spent suspiciously little time in comparison to the other raters to complete the task and raters who rated all conversations with the same label), results reported with remaining 104 raters. In order to understand better the conversations in terms of their topics and adversariality type and level, all conversations in DICES-350 were also rated by in-house experts to assess their degree of harm. All conversations in DICES-350 have gold ratings,i.e. they were annotated for safety by a trust and safety expert. Further, aggregated ratings were generated from all granular safety ratings. They include a single aggregated overall safety rating ('Q_overall'), and aggregated ratings for the three safety categories that the 16 more granular safety ratings correspond to: 'Harmful content' ('Q2_harmful_content_overall'), 'Unfair bias' ('Q3_bias_overall') and 'Safety policy violations' ('Q6_policy_guidelines_overall').",
  "rai:dataUseCases" : "The dataset is to be used as a shared resource and benchmark that respects diverse perspectives during safety evaluation of conversational AI systems.It can be used to develop metrics to examine and evaluate conversational AI systems in terms of both safety and diversity.",
  "rai:dataBiases" : "Dataset includes multiple sub-ratings which specify the type of safety concern, such as type of hate speech and the type of bias or misinformation, for each conversation. A limitation of the dataset is the selection of demographic characteristics. The number of demographic categories was limited to four (race/ethnicity, gender and age group). Within these demographic axes, the number of subgroups was further limited (i.e., two locales, five main ethnicity groups, three age groups and two genders), this constrained the insights from systematic differences between different groupings of raters.",
  "rai:annotationsPerItem": "350 conversations were rated along 16 safety criteria, i.e.,104 unique ratings per conversation.",
  "rai:annotatorDemographics": "DICES-350 was annotated by a pool of 104 raters. The rater breakdown for this pool is: 57 women and 47 men; 27 gen X+, 28 millennial, and 49 gen z; and 21 Asian, 23 Black/African American, 22 Latine/x, 13 multiracial and 25 white. All raters signed a consent form agreeing for the detailed demographics to be collected for this task."
}
```

## RAI properties for the BigScience Roots Corpus dataset

[The bigscience roots corpus: A 1.6 tb composite multilingual dataset](https://proceedings.neurips.cc/paper_files/paper/2022/hash/ce9e92e3de2372a4b93353eb7f3dc0bd-Abstract-Datasets_and_Benchmarks.html)

As the size of language models continues to increase, there is a growing demand for extensive and high-quality text datasets, particularly in multilingual contexts. The BigScience workshop emerged as a year-long international and interdisciplinary effort with a core mission of investigating and training large language models with a strong emphasis on ethical considerations, potential harm, and governance issues. The BigScience roots corpus [4] was instrumental in training the 176-billion-parameter BigScience Large Open-science Open-access Multilingual (BLOOM) language model. The goal of the dataset is to provide both the data and processing tools to facilitate large-scale monolingual and multilingual modeling projects and to stimulate further research on this extensive multilingual corpus.

```json
{
  "@context": {
    "@language": "en",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "sc": "https://schema.org/"
  }, 
  "@type": "schema.org/Dataset",
  "name": "BigScience Root Corpus", 
  "dct:conformsTo": "http://mlcommons.org/croissant/RAI/1.0",
  "rai:dataCollection": "The first part of the corpus, accounting for 62% of the final dataset size (in bytes), is made up of a collection of monolingual and multilingual language resources that were selected and documented collaboratively through various efforts of the BigScience Data Sourcing working group. The 38& remaining is get from the OSCAR version 21.09, based on the Common Crawl snapshot of February.",
  "rai:dataCollectionType": ["Web Scraping", "Secondary Data Analysis", "Manual Human Curation", "Software Collection"],
  "rai:dataUseCases": [
      "A comprehensive and multilingual corpus designed to support the training of large language models (LLMs)  ",  
      "It may also be of particular interest for research aimed at improving the linguistic and cultural inclusiveness of language technologies"
      ],
  "rai:dataLimitations":
      [
      "Crawled content also over-represents pornographic text across languages, especially in the form of spam ads. Finally, it contains personal information that may constitute a privacy risk. The present section outlines our approach to mitigating those issues",  
      "The preprocessing removes some categories of PII but is still far from exhaustive, and the nature of crawled datasets makes it next to impossible to identify individual contributors and ask for their consent.",  
        "The reliance on medium to large sources of digitized content still over-represents privileged voices and language varieties."  
      ],
  "rai:dataBiases": "Dataset includes multiple sub-ratings which specify the type of safety concern, such as type of hate speech and the type of bias or misinformation, for each conversation. A limitation of the dataset is the selection of demographic characteristics. The number of demographic categories was limited to four (race/ethnicity, gender and age group). Within these demographic axes, the number of subgroups was further limited (i.e., two locales, five main ethnicity groups, three age groups and two genders), this constrained the insights from systematic differences between different groupings of raters.",
  "rai:personalSensitiveInformation": "We used a rule-based approach leveraging regular expressions (Appendix C). The elements redacted were instances of KEY (numeric & alphanumeric identifiers such as phone numbers, credit card numbers, hexadecimal hashes and the like, while skipping instances of years and simple numbers), EMAIL (email addresses), USER (a social media handle) and IP_ADDRESS (an IPv4 or IPv6 address).“,",
  "rai:dataSocialImpact": "The authors emphasized that the BigScience Research Workshop, under which the dataset was developed, was conceived as a collaborative and value-driven endeavor from the beginning. This approach significantly influenced the project's decisions, leading to numerous discussions aimed at aligning the project’s core values with those of the data contributors, as well as considering the social impact on individuals directly and indirectly impacted by the project. These discussions and the project's governance strategy highlighted the importance of: Centre human selection of the data, suggesting a conscientious approach to choosing what data to include in the corpus based on ethical considerations and the potential social impact. Data release and governance strategies that would responsibly manage the distribution and use of the data. Although the document does not explicitly list specific potential social impacts, the emphasis on value-driven efforts, ethical considerations, and the human-centered approach to data selection suggests a keen awareness and proactive stance on mitigating negative impacts while enhancing positive social outcomes through responsible data collection and usage practices",
  "rai:dataManipulationProtocol": 
  ["Pseudocode to recreate the text structure from the HTML code. The HTML code of a web page provides information about the structure of the text. The final structure of a web page is, however, the one produced by the rendering engine of the web browser and any CSS instructions. The latter two elements, which can vary enormously from one situation to another, always use the tag types for their rendering rules. Therefore, we have used a 20 fairly simple heuristic on tag types to reconstruct the structure of the text extracted from an HTML code. To reconstruct the text, the HTML DOM, which can be represented as a tree is traversed with a depth-first search algorithm. The text is initially empty and each time a new node with textual content is reached its content is concatenated according to the rules presented in the Algorithm 1 of the accompanying paper.",
    "Data cleaning and filtering: documents were filtered with:• Too high character repetition or word repetition as a measure of repetitive content.• Too high ratios of special characters to remove page code or crawling artifacts.• Insufficient ratios of closed class words to filter out SEO pages.• Too high ratios of flagged words to filter out pornographic spam. We asked contributors to tailor the word list in their language to this criterion (as opposed to generic terms related to sexuality) and to err on the side of high precision. • Too high perplexity values to filter out non-natural language. • Insufficient number of words, as LLM training requires extensive context sizes.",  
    "Deduplication: we applied substring deduplication (Lee et al., 2022) based on Suffix Array (Manber and Myers, 1993) as a complementary method that clusters documents sharing a long substring, for documents with more than 6000 characters. We found on average 21.67% (10.61% ⇠ 32.30%) of the data (in bytes) being duplicated."
  ]
}
```

## RAI properties for the BigCode - The stack dataset

[The Stack](https://huggingface.co/datasets/bigcode/the-stack) contains over 6TB of permissively-licensed source code files covering 358 programming languages. The dataset was created as part of the BigCode Project, an open scientific collaboration working on the responsible development of Large Language Models for Code (Code LLMs). The Stack serves as a pre-training dataset for Code LLMs, i.e., code-generating AI systems which enable the synthesis of programs from natural language descriptions as well as other from code snippets.

```json
{
  "@context": {
    "@language": "en",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "sc": "https://schema.org/"
  }, 
  "@type": "schema.org/Dataset",
  "name": "BigScience - The Stack", 
  "dct:conformsTo": "http://mlcommons.org/croissant-RAI/1.0", 
  "rai:dataCollection": "The collection process is composed of the collection of 220.92M active GitHub repository names from the event archives published between January 1st, 2015 and March 31st, 2022 on GHArchive. Only 137.36M of these repositories were public and accessible on GitHub – others were not accessible as they had been deleted by their owners. 51.76B files were downloaded from the public repositories on GitHub between November 2021 and June 2022. 5.28B files were unique. The uncompressed size of all stored files is 92.36TB", 
  "rai:dataCollectionType": "Web Scraping", 
  "rai:dataCollectionRaw": "Files containing code data.", 
  "rai:dataCollectionTimeFrameStart": {
    "@value": "2015-01-01T00:00:00",
    "dataType": "sc:Date"
  },
  "rai:dataCollectionTimeFrameEnd": {
    "@value": "2022-12-31T00:00:00",
    "dataType": "sc:Date"
    },
  "rai:dataUseCases": 
  [
    "The Stack is a pre-training dataset for creating code LLMs. Code LLMs can be used for a wide variety of downstream tasks such as code completion from natural language descriptions (HumanEval, MBPP), documentation generation for individual functions (CodeSearchNet), and auto-completion of code snippets (HumanEval-Infilling)."
  ],
  "rai:dataLimitations": 
  [
    "One of the current limitations of The Stack is that scraped HTML for websites may not be compliant with Web Content Accessibility Guidelines (WCAG). This could have an impact on HTML-generated code that may introduce web accessibility issues.",
    "The training dataset could contain malicious code and/or the model could be used to generate malware or ransomware.",
    "Despite datasets containing personal information, researchers should only use public, non-personal information in support of conducting and publishing their open-access research. Personal information should not be used for spamming purposes, including sending unsolicited emails or selling of personal information."
  ],
  "rai:dataBiases": 
  [
    "Widely adopted programming languages like C and Javascript are overrepresented compared to niche programming languages like Julia and Scala. Some programming languages such as SQL, Batchfile, TypeScript are less likely to be permissively licensed (4% vs the average 10%). This may result in a biased representation of those languages. Permissively licensed files also tend to be longer",
    "Roughly 40 natural languages are present in docstrings and comments with English being the most prevalent. In python files, it makes up ~96% of the dataset",
    "The code collected from GitHub does not contain demographic information or proxy information about the demographics. However, it is not without risks, as the comments within the code may contain harmful or offensive language, which could be learned by the models."
  ],
  "rai:personalSensitiveInformation": 
  [
    "The released dataset may contain sensitive information such as emails, IP addresses, and API/ssh keys that have previously been published to public repositories on GitHub. Deduplication has helped to reduce the amount of sensitive data that may exist. The PII pipeline for this dataset is still a work in progress. Researchers who wish to contribute to the anonymization pipeline of the project can apply to join here: https://www.bigcode-project.org/docs/about/join/."
  ],
  "rai:dataSocialImpact": "The Stack is released with the aim to increase access, reproducibility, and transparency of code LLMs in the research community. We expect code LLMs to enable people from diverse backgrounds to write higher quality code and develop low-code applications. Mission-critical software could become easier to maintain as professional developers are guided by code-generating systems on how to write more robust and efficient code. While the social impact is intended to be positive, the increased accessibility of code LLMs comes with certain risks such as over-reliance on the generated code and long-term effects on the software development job market.",
  "rai:dataPreprocessingProtocol": 
  [
    "Near-deduplication was implemented in the pre-processing pipeline on top of exact deduplication. To find near-duplicates, MinHash with 256 permutations of all documents was computed in linear time. Locality Sensitive Hashing was used to find the clusters of duplicates. Jaccard Similarities were computed inside these clusters to remove any false positives and with a similarity threshold of 0.85. Roughly 40% of permissively licensed files were (near-)duplicates.",
    "Non detected licenses: GHArchive contained the license information for approximately 12% of the collected repositories. For the remaining repositories, go-license-detector was run to detect the most likely SPDX license identifier. The detector did not detect a license for ~81% of the repositories, in which case the repository was excluded from the dataset."
  ]
}
```

# **References**

[1] Mittal, Surbhi, Kartik Thakral, Richa Singh, Mayank Vatsa, Tamar Glaser, Cristian Canton Ferrer, and Tal Hassner. "On Responsible Machine Learning Datasets with Fairness, Privacy, and Regulatory Norms." arXiv preprint arXiv:2310.15848 (2023).

[2] Phillips, C., Roy, S., Ankur, K., Ramachandran, R.: HLS Foundation Burnscars Dataset (Aug 2023). [https://doi.org/10.57967/hf/0956](https://doi.org/10.57967/hf/0956),https://huggingface.co/ibm-nasa-geospatial/hlsburnscars

[3] Aroyo, Lora, Alex Taylor, Mark Diaz, Christopher Homan, Alicia Parrish, Gregory Serapio-García, Vinodkumar Prabhakaran, and Ding Wang. "Dices dataset: Diversity in conversational ai evaluation for safety." Advances in Neural Information Processing Systems 36 (2024).

[4] Laurençon, Hugo, Lucile Saulnier, Thomas Wang, Christopher Akiki, Albert Villanova del Moral, Teven Le Scao, Leandro Von Werra et al. "The bigscience roots corpus: A 1.6 tb composite multilingual dataset." Advances in Neural Information Processing Systems 35 (2022): 31809-31826.
