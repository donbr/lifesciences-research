---
title: "Kno wledge gr aph-based thought: a kno wledge graph-enhanced LLM framework for pan-cancer question answering"
authors: "Yichun Feng, Lu Zhou, Chao Ma, Yikai Zheng, Ruikun He, and Yixue Li, Smartquerier Gene Technology (Shanghai) Co ., Ltd., Shanghai, China, Contributed equally."
source: "giae082.pdf"
status: converted
---

<!-- image -->

DOI:

10.1093/gigascience/giae082

RESEARCH

## Kno wledge gr aph-based thought: a kno wledge graph-enhanced LLM framework for pan-cancer question ans w ering

Yichun Feng 1 ,2 , ‡ , Lu Zhou 2 , ‡ , Chao Ma 3 , ‡ , Yikai Zheng 2 , Ruikun He 4 ,5 , * , and Yixue Li 1 ,2 , *

1 Hangzhou Institute for Advanced Study, University of Chinese Academy of Sciences, 310024 Hangzhou, China

2 Guangzhou National Laboratory, Guangzhou International Bio Island, 510005 Guangzhou, China

3 Smartquerier Gene Technology (Shanghai) Co ., Ltd. , 200100 Shanghai, China

4 BYHEALTH Institute of Nutrition &amp; Health, 510663 Guangzhou, China

5 Shanghai Institute of Nutrition and Health, Chinese Academy of Sciences Shanghai, 200030 Shanghai, China

∗ Corr espondence addr ess . Ruikun He , BYHEALTH Institute of Nutrition &amp; Health, 510663 Guangzhou, China. E-mail: herk@by-health.com ; Yixue Li, Guangzhou National Laboratory, No. 9 XingDaoHuanBei Road, Guangzhou International Bio Island, 510005 Guangzhou. E-mail: yxli@sibs.ac.cn .

‡ Contributed equally.

## Abstract

Bac kgr ound: In recent years, large language models (LLMs) have shown promise in various domains, notably in biomedical sciences. Howev er, their r eal-world application is often limited by issues like erroneous outputs and hallucinatory responses.

Results: We developed the knowledge graph-based thought (KGT) framework, an innov ati v e solution that integrates LLMs with knowledge graphs (KGs) to impr ov e their initial r esponses by utilizing v erifia b le information from KGs, thus significantl y r educing factual err ors in r easoning. The KGT fr amew ork demonstr ates str ong adapta bility and performs well acr oss v arious open-source LLMs. Nota b l y, KGT can facilitate the discov er y of new uses for existing drugs through potential drug-cancer associations and can assist in pr edicting r esistance by anal yzing r elev ant biomarkers and genetic mechanisms. To ev aluate the kno wledge graph question ans wering task within biomedicine , w e utilize a pan-cancer knowledge graph to develop a pan-cancer question answering benchmark, named pan-cancer question answering.

Conclusions: The KGT fr amew ork substantiall y impr ov es the accuracy and utility of LLMs in the biomedical field. This study serves as a proof of concept, demonstrating its exceptional performance in biomedical question answering.

Ke yw ords: pan-cancer knowledge graph, large language model, knowledge graph question answering, prompt engineering

## Ke y P oints:

- /a114 We introduce a framework combining large language models (LLMs) with knowledge gr a phs (KGs) to impr ov e factual accuracy in LLM reasoning.
- /a114 Our system is a flexible arc hitectur e that seamlessly integr ates v arious LLMs.
- /a114 Utilizing a pan-cancer knowledge gr a ph, we hav e pr oposed the first knowledge gr a ph question answering benchmark in the field of biomedicine.
- /a114 Case studies r e v eal our method enhanced LLMs in addressing biomedical challenges such as drug repositioning, r esistance r esearc h, individualized tr eatment, and biomarker analysis.
- /a114 The method performs favor abl y in comparison to existing methods.

## Introduction

With the increasing prominence of large language models (LLMs) in the field of artificial intelligence, the advent of influential models such as ChatGPT [ 1 ] and Llama [ 2 ] consequently catalyze the de v elopment of a wide array of applications in biomedicine and health care. Ho w ever, LLMs still face the challenge of factual hallucination, wher e they gener ate incorr ect statements due to limited inherent knowledge [ 3 ]. Factual hallucination presents a significant challenge for the practical use of LLMs, especially in realworld scenarios where factual accuracy is crucial. Consequently, there is a growing focus on addressing factual hallucinations in LLMs within the field of natural language processing (NLP) [ 4 , 5 ].

LLMs often struggle to ca ptur e and access factual knowledge, primarily due to 3 aspects: the inability to comprehend questions due to the lack of contextual information, the insufficient knowledge to generate accurate ans wers , and the incapacity to recall specific facts [ 6 ]. Consequently, researchers consider the fine-tuning technique as a solution to address these issues. For example, MedAlpaca [ 7 ] builds upon medical data to fine-tune Stanford Alpaca for applications related to medical question ans wering and dialogue . ChatDoctor [ 8 ] is designed to simulate a conversation between a doctor and a patient by fine-tuning

<!-- image -->

|

LLaMA with medical liter atur e. Additionall y, Med-P aLM [ 9 ] shows promising performance on the MedQA exam based on clinical cor por a and human feedback. Meanwhile, aiming at the Chinese medical domain, LLMs such as BenTsao [ 10 ], DoctorGLM [ 11 ], and HuatuoGPT [ 12 ] are developed on the Chinese medical dialogue data. Mor e r ecentl y, Zhongjing [ 13 ] and ChiMed-GPT [ 14 ] adopted full pipeline training from pretraining, SFT, to reinforcement learning with human feedback (RLHF) [ 15 ]. While fine-tuning can reduce hallucinations in LLMs, it brings about considerable training expenses. Additionally, it poses a critical challenge known as catastrophic forgetting. This issue manifests when a model for gets its pr e viousl y learned information as a consequence of parameter modifications during the acquisition of new tasks. This forgetfulness results in a deterioration of performance on prior tasks, consequently constraining the model's practical applicability [ 16 , 17 ].

In addition to fine-tuning, r esearc hers also enhance the output of LLMs through the field of prompt engineering. Prompt engineering focuses on the creation and optimization of prompts to impr ov e the effectiv eness of LLMs acr oss v arious a pplications and r esearc h domains [ 18 ]. It can enhance the ca pabilities of LLMs in a wide range of complex tasks, including question answering, sentiment classification, and commonsense reasoning. Chain-ofthought (CoT) prompts [ 19 ] enable complex reasoning capabilities by incor por ating intermediate r easoning steps . T he Automatic Pr ompt Engineer (APE) pr oposes an automatic pr ompt gener ation method aimed at enhancing the performance of LLMs [ 20 ]. Prompt engineering offers a straightforw ar d approach to harnessing the potential of LLMs without fine-tuning.

On the other hand, knowledge gr a phs (KGs) ar e r epositories of vast quantities of high-quality structured data, offering the potential to effectiv el y mitigate the issue of factual hallucinations when integrated with LLMs . Hence , employing KGs for question answering can enhance the precision of the responses and furnish a dependable foundation for the factual verification of information produced by LLMs. Knowledge gr a ph question answering (KGQA) has long been a hot r esearc h topic. Befor e the advent of LLMs, certain studies [ 21-23 ] typically begin by r etrie ving a subgr a ph r elated to the question to r educe the searc h space, then perform m ultihop r easoning on this basis . T his r etrie v alplus-r easoning par adigm has shown its adv anta ges ov er dir ect r easoning acr oss the entir e KG [ 24 , 25 ]. Additionall y, r esearc hers tackle KGQA by parsing the question into a structured query language (e.g., SPARQL) and using a query engine to obtain accurate answers [ 26 , 27 ]. UniKGQA [ 28 ] introduces a unified finetuning fr ame work for r etrie v al and r easoning, mor e closel y linking these 2 stages. Ho w ever, traditional KGQA methods usually perform poorly in accurate semantic understanding and high-quality text generation due to the lack of LLMs for r etrie v al and r easoning. Hence, r ecent r esearc h is incr easingl y utilizing external KGs to enhance LLMs in addressing KGQA challenges. For instance, StructGPT [ 29 ] navigates through knowledge graphs by identifying pathways from an initial seed entity to the target answer entity, while Think-on-Gr a ph (ToG) [ 30 ] intr oduces iter ativ e exploration of the knowledge gr a ph, whic h can become inefficient with v ery lar ge KGs. Additionall y, Reasoning on Gr a phs (RoG) [ 31 ] necessitates fine-tuning to accur atel y gener ate and plan the r elation paths. KG-GPT [ 32 ] opts for r etrie ving an entire subgraph from the knowledge gr a ph and then deduces the answer thr ough infer ence. Although these methods hav e ac hie v ed gr atifying r esults in gener al ar eas, as shown in Fig. 1 B, when the intermediate entity in the multihop question is unknown, it is impossible to retrieve the a ppr opriate knowledge from the KG.

In this article, we intr oduce an innov ativ e fr ame work called knowledge gr a ph-based thought (KGT), whic h integr ates LLMs with KGs through employing LLMs for reasoning on the schema of KGs to mitigate factual hallucinations of LLMs, as shown in Fig. 1 C. Unlike traditional methods, KGT does not dir ectl y r etrie v e factual information based on the question. Instead, it uses LLMs to infer entity information on the schema of the knowledge graph, generating an optimal subgraph based on k e y information dir ectl y extr acted fr om the question and inferr ed information fr om the sc hema. Subsequentl y, the optimal subgr a ph is used to infer the answer to the question through LLMs. KGT r equir es no fine-tuning, offers seamless integration with multiple LLMs, and is plug-and-play, facilitating easy deployment. It demonstrates generalizability, making it adaptable for use with diverse knowledge gr a phs . T his fr ame work is tailor ed for wide-r anging a pplications in numerous biomedical challenges, such as (i) enhancing clinical decision-making for physicians and medical organizations, (ii) delivering medical advice to patients and health care pro viders , (iii) unco vering crucial biomarkers for early disease detection and tailored therapy, and (iv) exploring novel therapeutic applications for existing medications through insights into their mechanisms , side effects , and the biological processes of associated diseases . Furthermore , we utilize the SmartQuerier Oncology Knowledge Gr a ph (SOKG), a pan-cancer knowledge gr a ph developed by SmartQuerier, to create a benchmark for the KGQA task within biomedicine, named pan-cancer question answering (PcQA). We release this benchmark and its accompanying knowledge gr a ph, whic h is a subgr a ph of the SOKG, in [ 33 ]. This benchmark is curr entl y the sole question-ans wering dataset a vailable in the domain of biomedical knowledge gr a phs.

## Materials and Methods

## Kno wledge gr aph introduction

In this w ork, w e tac kle the pr oblem of logical r easoning ov er the KG K : E × R that store entities ( E ) and relations ( R ). Without loss of generality, KG can be organized as a set of triplets { ( e 1 , r , e 2 ) } ⊆ K , wher e eac h r elation r ∈ R exists between the pair of entities ( e 1 , e 2 ) ∈ E × E . We define a relational path { ( t 1 , r , t 2 ) } as a sequence of entity types ( T ) and the relation between them, where ( t 1 , t 2 ) ∈ T × T . In contrast, a relational chain { ( e 1 , r , e 2 ) } refers to a specific set of relational triplets between entities. To further enrich the KG, attribute information is included through pairs ( e , at t r ) , where at t r represents an attribute associated with an entity e , thereby enhancing the KG's semantic richness and precision by incorporating detailed characteristics of each entity.

Within the specialized realm of pan-cancer resear ch, w e use a subgr a ph of the SOKG that pr ovides detailed oncological information. As depicted in Table 1 , SOKG includes a collection of over 3 million entities, which is substantially larger than the entity count in the compared knowledge graphs, SynLethKG [ 34 ] and SDKG [ 35 ], with 540,012 and 165,062 entities, r espectiv el y. Furthermor e, SOKG's nearl y 6 million unique concept relations exceed those of SynLethKG and SDKG, which have 2,231,921 and 727,318 r elations, r espectiv el y. Additionall y, SOKG includes 98 distinct attribute types, enriching data comprehension and improving the efficiency and precision of queries, a capability not matched by SynLethKG or SDKG, which do not include comparable attributes. For this r esearc h, we utilize only a subgraph of the SOKG, which is available as open data [ 33 ], while the full knowledge graph remains proprietary.

Figure 1: Illustr ativ e examples contr asting our work with pr e vious efforts. (A) LLM-onl y-based infer ence , ans wering questions solel y thr ough the inherent knowledge of LLMs. (B) Subgraph-based inference, enhancing LLMs by retrieving the knowledge from KGs based on the question. If intermediate entities are not provided in the multihop question, no appropriate knowledge can be retrieved. (C) Graph schema-based inference, enhancing r etrie v al ca pabilities by r easoning intermediary entity types on the sc hema of the KG, using the knowledge of the KG to enhance LLMs' responses.

<!-- image -->

Table 1. Comparison of SOKG with SynLethKG and SDKG

|           |   Entity types |   Relational types | Nodes     | Edges      |   Attributes |
|-----------|----------------|--------------------|-----------|------------|--------------|
| SynLethKG |             11 |                 24 | 54,012    | 2,231,921  |            0 |
| SDKG      |              7 |                 12 | 165,062   | 727,318    |            0 |
| SOKG      |             24 |                 21 | 3,640,259 | 10,656,273 |           98 |

## Task description

In order to tackle a div erse arr ay of c hallenges in the field of biomedicine, we have designed 4 categories of problems: 1hop pr oblems, m ultihop pr oblems, intersection pr oblems, and attribute pr oblems, as illustr ated in Table 2 . Based on these 4 types of tasks, we le v er a ge the SOKG to establish a benchmark for the KGQA task within biomedicine, named PcQA. Unlike KGQA tasks in general domains, such as MetaQA [ 36 ] and FACTKG [ 37 ], whic h typicall y pr ovide the entity types of intermediate entities, KGQA problems in the biomedical domain often do not have any information about intermediate entities. Instead, the information about intermediate entities must be inferred from the question itself rather than being dir ectl y pr ovided, as shown in Supplementary Table S1 . Additionally, our PcQA dataset includes attributes such as whether a drug is tar geted ther a py or if a mutated gene is oncogenic. This makes our tasks slightly more challenging and better suited to the actual needs of biomedical KGQA.

## One-hop problems

One-hop pr oblems involv e single-r elation c hain r easoning, wher e the objective is to deduce the tail entity T ? given a head entity H 1 and a relation R 1 , or to infer the relation R ? when a head entity H 1 and a tail entity T 1 are known, as depicted in equations ( 1 ) and ( 2 ).

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

|

|

Table 2. Four differ ent r easoning types of task. Eac h r easoning type ma y include o v erla pping questions, so the sum acr oss the 4 differ ent reasoning types of the task may exceed the total number of questions

| Reasoning type   | Claim example                                                                            |   Question number |
|------------------|------------------------------------------------------------------------------------------|-------------------|
| One-hop          | What types of cancer can be treated with diethylstilbestrol?                             |               243 |
| Multihop         | What genetic mutations are present in adenoid cystic carcinoma?                          |               124 |
| Intersection     | Which drugs are ALK in basaloid large cell carcinoma of the lung sensitivity to?         |                37 |
| Attribute        | What is the maximum age for recruitment of clinical trials for patients with meningioma? |                59 |

## Multihop problems

Multihop pr oblems involv e m ultiple-r elation c hain r easoning that can be br oadl y categorized into 2 types . T he first category in volves deducing potential relationships between entities by navigating thr ough indir ect r elations. By examining the indir ect r elations ( R 1 , R 2 ) between a head entity H 1 and a tail entity T 1 , it is possible to infer an unknown or potential relation R ? linking them dir ectl y. This inference process is encapsulated in the following equation:

<!-- formula-not-decoded -->

The second category extends the reasoning to include the discovery of entities themselves b y follo wing a path from a head entity through intermediate relations to a final tail entity. Starting with a head entity H 1 , coupled with an indir ect r elation R 1 , an intermediary entity M can be inferred. This intermediary entity M is then applied with an indirect relation R 2 to deduce the final tail entity T ? . This infer ence pr ocess is summarized in the following equation:

<!-- formula-not-decoded -->

## Intersection problems

Intersection pr oblems r efer to taking the intersection of multiple relational chains. Two head entities ( H 1 , H 2 ) lead to the deduction of 2 types of tail entities ( T 1 , T 2 ) based on different relations ( R 1 , R 2 ). The final tail entity T ? is determined by intersecting these 2 types of tail entities ( T 1 , T 2 ). This inference process is summarized as following:

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

## Attribute problems

Attribute problems refer to the attribute information of the entity, where the task involves retrieving the attributes of a known head entity H 1 or determining whether the tail entity T 1 , identified through a known head entity H 1 and relation R 1 , satisfies the attributes specified in the query, as illustrated in equations ( 8 ) and ( 9 ).

<!-- formula-not-decoded -->

## Datasets

In the continuously evolving field of biomedical r esearc h, the integration of LLMs with KGs offers a more efficient and effective method for knowledge discovery and utilization, particularly in adv ancing cancer r esearc h. Nonetheless, we note a scarcity of a ppr opriate datasets for e v aluating these sophisticated methodologies within this field. To address this, we leverage the SOKG to establish a benchmark for the KGQA task within biomedicine, named PcQA. Our questions were carefully crafted by experts based on the content of the knowledge gr a ph. GPT-4 [ 38 ] was then emplo y ed to generate Cypher queries, which were used to retrie v e answers fr om the knowledge gr a ph. The gener ated Cypher queries and corresponding answers underwent an initial r e vie w by a biomedical PhD candidate, who manually verified and corrected the dataset against the knowledge graph. Finally, the entire dataset was thoroughly reviewed by 2 biomedical experts to ensure its accuracy and reliability. This multistep process was meticulously designed to uphold the highest standards of quality throughout the dataset creation. This dataset, along with the accompan ying knowledge gr a ph, is completel y open source [ 33 ]. The PcQA includes 405 data entries, covering a wide range of applications in the field of pan-cancer r esearc h, including genetic predisposition to cancer, medication tr eatment planning, drug r epositioning, identification of potential drug targets, studies on drug r esistance, and pr edictions of cancer pr ogr ession and metastasis. By deeply exploring cancer-related reasoning and information retrie v al c hallenges, this dataset can inspir e r esearc hers and clinicians to gain a deeper understanding of cancer and explore more effectiv e tr eatment methods.

## KGT fr ame w ork

T he o v er all fr ame work of KGT is laid out in Fig. 2 . When users input their question in natural language, the first step is to analyze the question, extracting the main information with the goal of breaking down the question into smaller, more manageable units. This main information is then passed to an LLM, which applies gr a ph r easoning on the sc hema gr a ph of the knowledge gr a ph, yielding the optimal r elational path. Subsequentl y, a r etrie v al statement is generated, and a subgraph is constructed within the

<!-- formula-not-decoded -->

|

F igure 2: F r ame work of KGT. (A) Question anal ysis. Decompose the question and extr act its k e y information. (B) Gr a ph sc hema-based infer ence. Input the types of the head and tail entities into the gr a ph sc hema of the knowledge gr a ph, complete the gr a ph r easoning, and obtain the optimal r elational path. (C) Subgr a ph construction. Gener ate a query statement and r etrie v e the subgr a ph. (D) Infer ence. Complete the final r easoning and output the results in natural language. Note: The symbol ' × ' r epr esents content that has been filtered out by the LLM, while ' /check ' denotes the optimal content selected by the LLM.

<!-- image -->

KG thr ough searc h. The r elational c hains and attributes in the subgr a ph ar e then fed back into the LLM to finalize the reasoning and generate an output in natural language.

## Question analysis

## Key information extraction

The user inputs a question text ( Q ) in natural language, which is initially deconstructed and parsed. An LLM is applied to analyze the question, resulting in the identification of the head entity name ( H n ), the tail entity type ( T t ), and the attributes of tail entity ( T a ). The prompt for the LLM to extract k e y information from the question is presented in Supplementary Fig. S1 .

## Retrie ving ke y information from the KG

Based on H n , a fixed Cypher format is set to query the head entity type ( H t ), facilitating subsequent reasoning.

## Graph schema-based inference

## Construction of a graph based on KG schema

Based on the entity types ( E t ) and the relations ( R ) between them in the SOKG, an undirected graph G is established where E t serve as nodes N and R act as edges P .

## Candidate path sear c h

Br eadth-first searc h (BFS) is emplo y ed to identify the shortest paths connecting H t and T t from the constructed graph G . Initiate the search at H t , creating a queue to hold nodes encountered along the way. Sim ultaneousl y, form a set to tr ac k nodes that have been visited to avoid r e visiting them. Insert H t into the queue. Continue processing as long as the queue remains nonempty, removing a node from the queue at each step. For each of its unvisited neighbors, enqueue the neighbor, mark it as visited, and log the pathway from H t to this neighbor. Upon arrival at T t , use the accu- mulated path data to compile the set of shortest paths ( SPs ) from H t to T t , with each individual path within the set r eferr ed to as an SP . The nodes in each SP represent entity types, while the edges denote the relationships between these entity types.

## Optimal path selection

By utilizing embedding technology, textual information is mapped into a low-dimensional space, resulting in N-dimensional realv alue v ectors . T he similarity between each SP and the Q is calculated based on their r espectiv e r eal-v alue v ectors, with the SP exhibiting the highest similarity being selected as the optimal path ( OP ).

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

## Subgraph construction

## Query statement generation

Input H t , H n , T t , T a , and OP into an LLM to generate a query statement, such as Cypher . T ext2Cypher Prompt is presented in Supplementary Fig. S2 .

## Subgr aph gener ation

Enter the query statement in the KG to obtain a reasonable subgr a ph.

|

## Inference Subgraph inference

Based on the relational chains and attribute data in the subgraph, determine the r ele v ance to the question text. Prune an y err oneous information, r etaining onl y the corr ect r elational c hains.

## Natural language output

The LLM divides the subgr a ph into multiple relational chains, each of which outputs a sentence in natural language, and then the LLM generates natural language output. LLMs Inference and Output Prompt is presented in Supplementary Fig. S3 .

## Results

## Ev alua tion criteria

We use e v aluators based on GPT-4 [ 38 ], BERTScore [ 39 ], and ROUGE [ 40 ] to assess the accuracy of the generated ans wers . As a scoring bot, GPT-4 e v aluates and assigns scores based on the similarity in meaning between 2 sentences. GPT-4-based Evaluation Pr ompt is pr esented in Supplementary Fig. S4 . BERTScor e e v aluates semantic similarity using context-sensiti ve embed dings, offering a compr ehensiv e e v aluation of langua ge model outputs. ROUGE, on the other hand, e v aluates the longest common subsequence (LCS) between the generated text and the reference text, focusing on sequence-based similarity to assess the fluency and the pr eserv ation of semantic content.

## Baselines

To assess the adv anta ges of our fr ame w ork, w e compare it with se v er al a ppr oac hes that can be dir ectl y a pplied for KGQA tasks without fine-tuning. We introduce a straightforw ar d baseline appr oac h, named Base, which is similar to KG-GPT [ 32 ], curr entl y the leading method in the KGQA field, excluding the sentence segmentation step of KG-GPT. Initiall y, this involv es le v er a ging an LLM to r etrie v e r ele v ant information fr om the KG by gener ating a query statement. Then, another LLM is used to answer the question with the r etrie v ed information. To enhance the baseline, we incor por ate CoT pr ompting [ 19 ] and in-context learning (ICL) tec hniques [ 41 ], collectiv el y r eferr ed to as CoT&amp;ICL. The pr ompts for these methods are illustrated in Supplementary Table S5 . Additionally, we implement KG-GPT [ 32 ] to enhance the r etrie v al and r easoning ca pabilities of the LLMs. For a fair comparison, all methods are based on Code-Llama-13B [ 42 ].

To further underscore the efficacy of our fr ame w ork, w e conduct a compar ativ e anal ysis of KGT, whic h is built upon CodeLlama-13B, a gainst 2 highl y ca pable lar ge langua ge models that ar e pr ominent in the general and biomedical domains: ChatGPT3.5 [ 1 ] and Taiyi [ 43 ]. ChatGPT-3.5, a leader in tasks across the general domain, has exhibited competitive performance in a wide r ange of a pplications. To compensate for its limited biomedical kno wledge, w e emplo y 2 methodologies pr e viousl y described, Base and CoT&amp;ICL, as advanced baselines to augment ChatGPT3.5's capabilities. Taiyi, a cutting-edge LLM in biomedicine, pretrained on 2 trillion tokens, le v er a ges its extensiv e biomedical knowledge base for direct question answering, bypassing the need for knowledge gr a ph r etrie v al.

Due to the scarcity of KGQA datasets within the biomedical domain, all experiments are conducted on our ne wl y pr oposed benchmark, named PcQA.

## Compar a ti v e analysis across different KGQA methods

We e v aluated the ca pabilities of v arious methods based on Code-Llama-13B, with the experimental results presented in Table 3 . The experimental results indicate that the Code-Llama13B model, enhanced with KGT, consistently surpasses competing methods across all metrics assessed. Notabl y, KG-GPT impr ov es the F1 score by 15.7% over previous methods CoT&amp;ICL, while our method KGT increases the F1 score by 33% over KG-GPT. Because KG-GPT overlooks the impact of entity types and attributes on answers within the biomedical domain, this ac hie v ement positions our a ppr oac h as a pioneering benc hmark in biomedical KGQA, eclipsing pr e viousl y established best pr actices.

## Compar a ti v e analysis across di v erse LLMs

We present a comparative study of KGT applied to Code-Llama13B against 2 highly capable LLMs in the general and biomedical domains, with experimental results displayed in Table 4 . CodeLlama-13B, enhanced by KGT, significantly outperforms its peers, ac hie ving the highest marks in e v ery assessment metric: a GPT4 Eval score of 92.4, a BERTScore of 97.7, and a ROUGE F1 score of 86.8. Remarkably, our approach's F1 score surpasses that of ChatGPT-3.5 with the Base method by 52.7%, the CoT&amp;ICL method by 36.3%, and Taiyi's base model by 67.3%. These results highlight KGT's substantial contribution to improving the performance of lar ge langua ge models for the pan-cancer KGQA task. Ev en when integrated with open-source general models, KGT exhibits remarkable performance, outstripping both the recognized stateof-the-art closed-source large language models and those specificall y tailor ed for the biomedical domain. This showcases KGT's adeptness at parsing and le v er a ging knowledge gr a ph data, setting a new standard for future research and applications in the field.

## Assessing KGT's effecti v eness on di v erse LLM platforms

To underscore the adaptability and effectiveness of our KGT fr ame work when applied to a range of large language models, we conduct experiments on se v er al LLMs: Zephyr [ 44 ], Llama-2 [ 2 ], and Code-Llama [ 42 ]. The outcomes, illustrated in Fig. 3 , reveal that while the CoT&amp;ICL techniques significantly boost performance in terms of F1 score, our KGT methodology delivers e v en mor e substantial enhancements acr oss all e v aluated models . T his demonstrates not only the effectiveness of CoT&amp;ICL as a performance-enhancing strategy but also highlights the superior advancements and impact of KGT, establishing its dominance and efficiency in knowledge gr a ph question-answering tasks.

## Ablation study for dissecting the components of KGT

In our effort to illuminate the individual contributions of the components that constitute our KGT fr ame work and their collective impact on enhancing the performance of LLMs, we define 4 foundational modules: (i) question analysis for the extraction of pivotal information, (ii) gr a ph sc hema-based infer ence to identify the optimal relational chains in the knowledge graph, (iii) the generation of query statements to facilitate subgraph construction, and (iv) the inference process coupled with the articulation of results in natural language . T his ablation study, grounded on the Code-Llama-13B model, is meticulously designed to e v aluate the efficacy of these components. Since gr a ph sc hema-based infer ence r equir es the pr ocess of question anal ysis, the ques-

|

Table 3. Comparison of results between KGT and other commonly used methods based on the Code-Llama-13B. The best results are displayed in bold for each indicator

|            |                |               | ROUGE (%)   | ROUGE (%)   | ROUGE (%)   |
|------------|----------------|---------------|-------------|-------------|-------------|
| Method     | GPT-4 Eval (%) | BERTScore (%) | Recall      | Precision   | F1 score    |
| Base       | 46.6           | 85.3          | 25.3        | 28.5        | 24.5        |
| CoT&ICL    | 57.9           | 88.8          | 38.9        | 39.4        | 37.6        |
| KG-GPT     | 68.2           | 93.5          | 55.2        | 55.8        | 53.3        |
| KGT (ours) | 92.4           | 97.7          | 87.4        | 87.7        | 86.8        |

Table 4. Comparison of KGT based on Code-Llama-13B with results from other commonly used models . T he best results are displayed in bold for each indicator

F igure 3: P erformance of v arious models using differ ent str ategies.

|                |            |                |               | ROUGE (%)   | ROUGE (%)   | ROUGE (%)   |
|----------------|------------|----------------|---------------|-------------|-------------|-------------|
| Model          | Method     | GPT-4 Eval (%) | BERTScore (%) | Recall      | Precision   | F1 score    |
| ChatGPT-3.5    | Base       | 65.4           | 91.0          | 42.7        | 32.3        | 34.1        |
|                | CoT&ICL    | 70.3           | 93.3          | 57.0        | 50.6        | 50.5        |
| Taiyi          | \          | 40.6           | 85.3          | 15.4        | 39.6        | 19.5        |
| Code-Llama-13B | KGT (ours) | 92.4           | 97.7          | 87.4        | 87.7        | 86.8        |

<!-- image -->

tion analysis module cannot be removed in isolation; simultaneousl y, subgr a ph construction is indispensable for knowledge gr a ph r etrie v al. If the subgr a ph construction module is independently omitted, the outputs of the initial 2 modules will not impact the final results, making the isolated exclusion of this component illogical. Ther efor e, we intr oduce 3 specific ablated configurations for examination: (i) excluding gr a ph sc hema-based inference (without GSBI), (ii) omitting both question analysis and gr a ph sc hema-based infer ence (without QA&amp;GSBI), and (iii) r emo ving question analysis , graph schema-based inference , and subgr a ph construction (without QA&amp;GSBI&amp;SC), effectiv el y bypassing the structured query of the SOKG and relying solely on the LLM's inherent knowledge for question answering.

Models

The results of the ablation study, as shown in Table 5 , demonstrate that when we remove the GSBI, we observe a 20% decrease in the F1 score . Remo ving both GSBI and QA results in an additional 8.6% decrease in the F1 score compared to removing GSBI alone . Furthermore , remo ving GSBI, QA, and SC together leads to a 46% decrease in the F1 score compared to removing just GSBI and QA. The experiments r e v eal that SC is crucial; its absence forces the LLM to r el y solel y on its inher ent knowledge, significantl y r educing effectiv eness. GSBI is also k e y, as it aids in navigating complex multihop questions by providing necessary intermediate entity information for subgr a ph construction. QA is equall y essential, ensuring accurate identification of entities and properties for corr ect subgr a ph construction. All these v ariants under perform

|

Table 5. Ablation study of the KGT fr ame work under Code-Llama-13B

|                    |                |               | ROUGE (%)   | ROUGE (%)   | ROUGE (%)   |
|--------------------|----------------|---------------|-------------|-------------|-------------|
| Method             | GPT-4 Eval (%) | BERTScore (%) | Recall      | Precision   | F1 score    |
| KGT (ours)         | 92.4           | 97.7          | 87.4        | 87.7        | 86.8        |
| Without GSBI       | 71.8           | 95.5          | 68.1        | 69.8        | 66.8        |
| Without QA&GSBI    | 69.7           | 94.7          | 55.0        | 66.3        | 58.2        |
| Without QA&GSBI&SC | 24.7           | 77.4          | 14.8        | 12.3        | 12.2        |

compared to the complete KGT, indicating that each of the 3 modules is vital for the final performance . Furthermore , such observations confirm that our KGT can indeed le v er a ge knowledge to enhance the final performance of LLMs.

## Implementation settings

Our knowledge gr a ph is quite large, with a complex schema, and typicall y involv es input tokens within 1,300. Our experiment does not r equir e fine-tuning, and the infer ence time is r elated to the model size and computational resources. For example, when using our method, KGT, with the Code-Llama-13B model on an 80 GB A100 GPU, it occupies 33 GB of VRAM. Without any acceleration fr ame works, the infer ence r equir es 4 passes, eac h taking ar ound 20 seconds.

## Case studies

## Drug repositioning

Drug r epositioning emer ges as a pr omising str ategy to acceler ate the process of drug development. This approach involves identifying new therapeutic uses for existing drugs, thereby saving time and r esources typicall y r equir ed for bringing a ne w drug to market [ 45 ]. Our system is capable of investigating the potential repositioning of carteolol for the treatment of hemangiomas . T he example is shown in Supplementary Table S2 and r elational dia gr am is shown in Fig. 4 A. Utilizing the system's knowledge gr a ph, a r elational chain is delineated, illustrating that propranolol, another inhibitor of ADRB1, is effectiv el y emplo y ed in the treatment of hemangiomas . T he system harnesses this insight to formulate a hypothesis that carteolol, by virtue of its similar mechanism of inhibition, could be potentially repositioning for treating hemangiomas [ 46 ]. This hypothesis would serve as a precursor to clinical trials and r esearc h, potentiall y expediting the availability of an additional ther a peutic option for patients with hemangiomas.

## Drug resistance resear c h

Drug resistance in cancer treatment poses a significant challenge in clinical oncology. Understanding the genetic basis of resistance can lead to mor e effectiv e tr eatment str ategies and personalized medicine a ppr oac hes. Researc h in drug r esistance involv es determining why certain cancer-carrying mutated genes are not responsive to specific drugs and finding ways to overcome this resistance [ 47 ]. Our system is capable of exploring drug resistance in cancer. The example is shown in Supplementary Table S3 , and a relational diagram is shown in Fig. 4 B. The KG data indicate that the ALK-p.L1196M m utation, whic h is associated with gastric cancer, has a known resistance to nalatinib [ 48 , 49 ]. The LLM processes this information and infers that due to this resistance, nalatinib might not be an effective medication for treating cancers caused by the ALK-p.L1196M mutation. The case highlights the critical importance of understanding specific gene-drug interactions in drug resistance research. It demonstrates how cer- tain gene mutations could render a drug ineffective, which in turn could guide oncologists in choosing alternative treatments or dev eloping ne w drugs that can bypass or tar get the r esistance mec hanisms. By accelerating the process of understanding drug resistance, these artificial intelligence-driven systems can contribute to impr ov ed patient outcomes and the optimization of cancer tr eatment pr otocols.

## Individualized treatment

Details on individualized tr eatment ar e pr ovided in Supplementary Case Studies A . It is important to note that this example is included solely to illustrate the technical capabilities of the proposed method. The output generated in this example has not been validated for clinical use, and further validation in clinical settings would be r equir ed befor e an y suc h a pplication.

## Selection and understanding of biomarkers

Details on selection and understanding of biomarkers are provided in Supplementary Case Studies B .

## Discussion

In this article, we introduce a novel framework KGT, which employs LLMs for reasoning on the schema of KGs, to enhance the reasoning abilities of LLMs in areas with missing domain data by utilizing domain-specific knowledge gr a phs, suc h as oncology knowledge gr a phs, ther eby addr essing the issue of factual hallucinations in LLMs. Our method excels in extr acting, v alidating, and refining factual knowledge throughout the LLMs' reasoning process. It seamlessly integrates with various LLMs, including open-source models like Code-Llama, and enhances the capabilities of LLMs solely through prompt engineering and incontext learning without any fine-tuning. This grants it significant generalizability.

We possess an extensive oncology knowledge graph and have established a benchmark based on it to e v aluate the ca pabilities of various methods. When tested on PcQA using various open-source LLMs, the KGT fr ame work performs exceptionall y well, sur passing the current best methods by 33%. This significant improvement positions our a ppr oac h as a pioneering benchmark in biomedical KGQA, setting a new standard that advances beyond previously established best pr actices. Additionall y, thr ough case studies, our a ppr oac h has been shown to effectiv el y pr ovide ther a peutic plans, gener ate v aluable hypotheses for drug r epositioning, identify potential drug targets, and study drug resistance . T his underscores the pr actical v alue of the KGT fr ame work in deliv ering insightful contributions that aid in the de v elopment and optimization of treatment strategies. Each case study's conclusions are further v alidated by e vidence fr om pr e viousl y published r esearc h pa pers, enhancing the credibility and impact of our findings.

Ho w e v er, it is important to note that the constructed QA dataset and the corresponding published subset of the SOKG

|

Figure 4: (A), (B), (C), and (D) r espectiv el y r epr esent the r elational dia gr ams of drug r epositioning, drug r esistance r esearc h, individualized tr eatment, and selection and understanding of biomarkers.

<!-- image -->

wer e specificall y designed to v alidate the effectiv eness of the KGT fr ame work within this study. While the dataset is highly relevant to biomedical applications, its scope is primarily focused on validating the proposed method. T herefore , it ma y not co ver all potential use cases. Additionally, our system curr entl y has the dr awbac k of not performing fuzzy matching; if a drug name is misspelled by e v en 1 letter, it fails to r etrie v e information from the knowledge gr a ph. Ther efor e, we plan to impr ov e this aspect in the future to enhance the system's usability and reliability. Our ultimate goal is to create a robust framework applicable to the rapidly evolving domain of medical knowledge, supporting health care professionals in delivering personalized, precise medication tailored to the individual needs of each patient.

Finally, we affirm that this study serves as a proof of concept, aiming to showcase the technical feasibility and initial efficacy of the method, which has not been validated in actual clinical practice. In any clinical or medical decision-making, reliance should always be placed on the judgment and guidance of professional health care practitioners.

## Additional Files

Supplementary Table S1. Comparison of PcQA with MetaQA and FACTKG in multihop tasks . T he types of intermediate entities are indicated in bold.

Supplementary Table S2. Example of drug repositioning.

Supplementary Table S3. Example of drug resistance research.

Supplementary Table S4. Example of individualized treatment.

Supplementary Table S5. Example of selection and understanding of biomarkers.

Supplementary Table S6. Prompts for Base and CoT&amp;ICL.

Supplementary Fig. S1. Prompt for k e y information extraction.

Supplementary Fig. S2. Prompt for query statement generation.

Supplementary Fig. S3. Prompt for LLM inference and output.

Supplementary Fig. S4. Prompt for GPT-4-based evaluation.

Supplementary Fig. S5. (A), (B), (C), and (D) r espectiv el y r epr esent the r elational dia gr ams of drug r epositioning, drug r esistance r esearc h, individualized tr eatment, and selection and understanding of biomarkers.

|

## Abbreviations

APE: automatic prompt engineer; BFS: breadth-first search; CF: catastr ophic for getting; CoT: c hain of thought; GPT: gener ativ e pr etr ained tr ansformer; ICL: in-context learning; KG: knowledge gr a ph; KGQA: knowledge gr a ph question answering; LLM: large langua ge model; NLP: natur al langua ge pr ocessing; PcQA: pancancer question answ ering; RLHF: reinfor cement learning with human feedback; SFT: supervised fine-tuning.

## Availability of Source Code and Requirements

Project name:

bioKGQA-KGT

- /a114 Pr oject homepa ge: https:// github.com/ yichun10/ bioKGQAKGT.git
- /a114 Operating system(s): Linux (Ubuntu)
- /a114 Resource usage in inference ste p: A Lin ux (Ubuntu) system with at least 2 CPU cores and 32 GB of VRAM. The GPU card needs at least 60 GB VRAM (either two 32 GB V100s or one 80 GB A100)
- /a114 Pr ogr amming langua ge: Shell Script (Bash) with Python 3.10.13
- /a114 Other r equir ements: Python 3.10.13 with GPU/CPU support, neo4j 5.13.0 (please see more requirements on GitHub repository)
- /a114 Licenses: MIT license
- /a114 Resear ch Resour ce Identifier (#RRID): SCR\_025176

## Ethical Statement

This study involves the generation of a biomedical questionanswer dataset derived from a biomedical knowledge gr a ph developed by our team. The knowledge gr a ph has been meticulously constructed using nonpersonalized data obtained from various credible biomedical sources . T he data collection and utilization pr ocesses strictl y compl y with all r ele v ant legal r egulations and ethical guidelines, ensuring the highest standards of data security and privacy. The dataset adheres rigorously to data protection principles and contains no sensitive personal information or identifiable individual health data. Furthermore, as the data collection and processing activities in this study do not involve human subjects, this r esearc h did not r equir e ethical r e vie w or a ppr ov al.

## Author Contributions

Y.F. and L.Z. conceiv ed the pr oject. Y.F. pr oposed a KGQA benc hmark, de v eloped the KGT fr ame work, implemented the code, conducted the experiments, and drafted the manuscript. C.M. contributed the SmartQuerier Oncology Knowledge Gr a ph. Y.L. and L.Z. supervised the study. All authors read and a ppr ov ed the final manuscript.

## Funding

This work was supported in part by funds from the National K ey Researc h and De v elopment Pr ogr am of China (Nos. 2022YFF1202101 and 2023YFC3041600), the Chinese Academy of Sciences Research Fund (No. XDB38050200), and the Selfsupporting Pr ogr am of Guangzhou National Labor atory (Nos. SRPG22001 and SRPG22007).

## Da ta Av ailability

We have publicly provided a subset of the SmartQuerier Oncology Knowledge Gr a ph necessary for r epr oducing the r esearc h. An arc hiv al copy of the code and the subgr a ph of the knowledge gr a ph used in this r esearc h is av ailable via Softwar e Herita ge [ 33 ], and the code and datasets can be accessed via GitHub [ 50 ]. Additionall y, the pr ompts used in inter actions with LLMs [ 1 , 2 , 38 , 42-44 ] during this r esearc h ar e av ailable in the supplemental material. For access to the complete SmartQuerier Oncology Knowledge Gr a ph data, please contact at service@smartquerier.com.

## Competing Interests

Chao Ma is emplo y ed b y SmartQuerier Gene Technology (Shanghai) Co., a company active in the biomedical field relevant to the content of this r esearc h. The SmartQuerier Oncology Knowledge Gr a ph (SOKG) used in this study is proprietary to SmartQuerier Gene Technology (Shanghai) Co. The other authors declare that they have no competing interests.

## References

1. OpenAI. ChatGPT (Nov 30 version) [large language model]. 30 Nov 2022. https:// chat.openai.com/ chat .
2. Touvron H, Martin L, Stone K, et al. Llama 2: Open foundation and fine-tuned chat models [large language model]. 2023. arXiv pre print arXi v:230709288. 19 Jul 2023. https:// doi.org/ 10.48550/a rXiv.2307.09288 .
3. Ji Z, Lee N, Frieske R, et al. Survey of hallucination in natural langua ge gener ation. ACM Comput Surv 2023;55(12):1-38. https: // doi.org/ 10.1145/ 3571730 .
4. Liu T, Zheng X, Chang B, et al. To w ar ds faithfulness in open domain table-to-text generation from an entity-centric view. In: Yang Qiang, ed. Proceedings of the AAAI Conference on Artificial Intelligence. AAAI Press. Vol. 35; 2021:13415-423. https: // doi.org/ 10.48550/arXiv.2102.08585 .
5. Kang D, Hashimoto T. Impr ov ed natur al langua ge gener ation via loss truncation. 2020. arXiv preprint arXiv:200414589. 1 May 2020. https:// doi.org/ 10.48550/arXiv.2004.14589 .
6. Pan S, Luo L, Wang Y, et al. Unifying large language models and knowledge gr a phs: a r oadma p. IEEE Tr ans Knowl Data Eng. 2024;36(7):3580-99. https:// doi.org/ 10.1109/ TKDE.2024.3352100 .
7. Han T, Adams LC, P a paioannou JM, et al. MedAlpaca-an opensource collection of medical conversational AI models and training data. 2023. arXiv preprint arXiv:230408247. 4 Oct 2023. https: // doi.org/ 10.48550/arXiv.2304.08247 .
8. Yunxiang L, Zihan L, Kai Z, et al. Chatdoctor: A medical chat model fine-tuned on Llama model using medical domain knowledge. Cureus 2023;15(6):e40895. https:// doi.org/ 10.7759/ cureus .40895 .
9. Singhal K, Azizi S, Tu T, et al. Lar ge langua ge models encode clinical knowledge. Nature 2023;620:172-80. https:// doi.org/ 10.103 8/s41586023062912 .
10. Wang H, Liu C, Xi N, et al. Huatuo: tuning Llama model with Chinese medical knowledge. 2023. arXi v pre print arXi v:230406975. 14 Apr 2023. https:// doi.org/ 10.48550/arXiv.2304.06975 .
11. Xiong H, Wang S, Zhu Y, et al. Doctorglm: fine-tuning your Chinese doctor is not a herculean task. 2023. arXiv preprint arXiv:230401097. 17 Apr 2023. https:// doi.org/ 10.48550/arXiv.2 304.01097 .
12. Zhang H, Chen J, Jiang F, et al. HuatuoGPT, to w ar ds taming language model to be a doctor. 2023. arXiv preprint

- arXiv:230515075. 24 May 2023. https:// doi.org/ 10.48550/arXiv.2 305.15075 .
13. Yang S, Zhao H, Zhu S, et al. Zhongjing: enhancing the Chinese medical capabilities of large language model through expert feedback and real-world multi-turn dialogue. In: Proceedings of the AAAI Conference on Artificial Intelligence. 2023;38(17):19368-76. https:// doi.org/ 10.1609/ aaai.v38i17.2990 7 .
14. Tian Y, Gan R, Song Y, et al. ChiMed-GPT: a Chinese medical large language model with full training regime and better alignment to human pr efer ences. 2023. arXiv pr e print arXi v:231106025. 15 Jul 2024. https:// doi.org/ 10.48550/arXiv.2311.06025 .
15. Ouyang L, Wu J, Jiang X, et al. Tr aining langua ge models to follow instructions with human feedback. Adv Neur Inf Proc Syst 2022;35:27730-44. https:// doi.org/ 10.48550/arXiv.2203. 02155 .
16. Luo Y, Yang Z, Meng F, et al. An empirical study of catastr ophic for getting in lar ge langua ge models during continual fine-tuning. 2023. arXi v pre print arXi v:230808747. 17 Aug 2023. https:// doi.org/ 10.48550/arXiv.2308.08747 .
17. Li Z, Hoiem D. Learning without forgetting. IEEE Trans Pattern Anal Machine Intell 2017;40(12):2935-47. https:// doi.org/ 10.110 9/TPAMI.2017.2773081 .
18. Liu V, Chilton LB. Design guidelines for prompt engineering textto-ima ge gener ativ e models. In: Pr oceedings of the 2022 CHI Conference on Human Factors in Computing Systems. 2022:123. https:// doi.org/ 10.1145/ 3491102.3501825 .
19. W ei J, W ang X, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models. Adv Neur Inf Proc Syst 2022;35:24824-37. https:// doi.org/ 10.48550/arXiv.2201.1190 3 .
20. Zhou Y, Muresanu AI, Han Z, et al. Large language models ar e human-le v el pr ompt engineers. 2022. arXiv pr eprint arXiv:221101910. 3 Nov 2022. https:// doi.org/ 10.48550/arXiv.221 1.01910 .
21. Sun H, Dhingra B, Zaheer M, et al. Open domain question answering using early fusion of knowledge bases and text. In: Riloff E., Chiang D., Hockenmaier J., and Tsujii J.eds. Proceedings of the 2018 Conference on Empirical Methods in Natural Langua ge Pr ocessing. 2018:4231-42. https:// doi.org/ 10.18653/v 1/D18-1455 .
22. Sun H, Bedrax-Weiss T, Cohen WW. Pullnet: open domain question answering with iter ativ e r etrie v al on knowledge bases and text. In: Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLPIJCNLP). Association for Computational Linguistics; 2019:238090. https:// doi.org/ 10.18653/v1/ D19-1242 .
23. Zhang J, Zhang X, Yu J, et al. Subgr a ph r etrie v al enhanced model for multi-hop knowledge base question answering. 2022. arXiv pre print arXi v:220213296. 27 Jul 2022. https:// doi.org/ 10.48550/a rXiv.2202.13296 .
24. Chen Y, Wu L, Zaki MJ. Bidir ectional attentiv e memory networks for question answering over knowledge bases. In: Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers); Minneapolis, Minnesota: Association for Computational Linguistics; 2913-23. https:// doi.org/ 10.18653/v1/ N19-1299 .
25. Saxena A, Tripathi A, Talukdar P. Impr oving m ulti-hop question ans wering o v er knowledge gr a phs using knowledge base embeddings . In: J urafsky D., Chai J., Schluter N., and T etreault J .eds. Proceedings of the 58th Annual Meeting of the Association for

|

- Computational Linguistics. Association for Computational Linguistics; 2020:4498-507. https:// doi.org/ 10.18653/v1/ 2020.acl-m ain.412 .
26. Lan Y, He G, Jiang J, et al. A survey on complex knowledge base question ans wering: methods , challenges and solutions . In: Proceedings of the 30th International Joint Conference on Artificial Intelligence (IJC AI-21). IJC AI; 4483-91. https:// doi.org/ 10.24963/i jcai.2021/611 .
27. Das R, Zaheer M, Thai D, et al. Case-based reasoning for natur al langua ge queries ov er knowledge bases. In: Pr oceedings of the 2021 Conference on Empirical Methods in Natural Langua ge Pr ocessing. Online and Punta Cana: Association for Computational Linguistics; 2021:9594-611. https:// doi.org/ 10.18653 /v1/2021.emnlp-main.755 .
28. Jiang J, Zhou K, Zhao WX, et al. Unikgqa: unified r etrie v al and reasoning for solving multi-hop question ans wering o ver knowledge gr a ph. 2022. arXiv pr eprint. arXiv:221200959. 2 Dec 2022. https:// doi.org/ 10.48550/arXiv.2212.00959 .
29. Jiang J, Zhou K, Dong Z, et al. Structgpt: a gener al fr ame work for lar ge langua ge model to r eason ov er structur ed data. In: Pr oceedings of the 2023 Conference on Empirical Methods in Natur al Langua ge Pr ocessing. Singa por e. Association for Computational Linguistics; 2023:9237-51. https:// doi.org/ 10.18653/v1/ 20 23.emnlp-main.574 .
30. Sun J, Xu C, Tang L, et al. Think-on-gr a ph: deep and responsible reasoning of large language model on knowledge graph. In: The Twelfth International Conference on Learning Representations. Vienna, Austria: arXiv; 2024. https:// doi.org/ 10.48550/arXiv.230 7.07697 .
31. Luo L, Li YF, Haf R, et al. Reasoning on gr a phs: faithful and inter pr etable lar ge langua ge model r easoning. In: The Twelfth International Conference on Learning Representations.Vienna, Austria. arXiv; 2024. https:// doi.org/ 10.48550/arXiv.2310.01061 .
32. Kim J, Kwon Y, Jo Y, et al. KG-GPT: A general framework for reasoning on knowledge graphs using large language models. In: Bouamor H., Pino J., and Bali K.eds. Findings of the Association for Computational Linguistics: EMNLP. Singa por e: Association for Computational Linguistics. 2023; 9410-21. https: // doi.org/ 10.48550/arXiv.2310.11220 .
33. Feng Y, Zhou L, Ma C, et al.. Knowledge gr a ph-based thought: a knowledge gr a ph enhanced LLMs fr ame work for pan-cancer question answering (Version 1). 2024 Softwar e Herita ge [Computer softwar e]. https://arc hive.softwar eheritage.or g/br owse/ sna pshot/1906dbbfc88c9d1c8b7acf7deb7495e8002cbafa/dir ect ory/ ?origin \_ url=https:// github.com/yichun10/ bioKGQA-KGT .
34. W ang J, W u M, Huang X, et al. SynLethDB 2.0: a web-based knowledge gr a ph database on synthetic lethality for novel anticancer drug discovery. Database 2022;2022:baac030. https://doi. org/ 10.1093/ database/baac030 .
35. Zhu C, Yang Z, Xia X, et al. Multimodal reasoning based on knowledge gr a ph embedding for specific diseases. Bioinformatics 2022;38(8):2235-45. https:// doi.org/ 10.1093/ bioinformatics/b tac085 .
36. Zhang Y, Dai H, Kozar e v a Z, et al. Variational reasoning for question answering with knowledge gr a ph. In: McIlr aith S.A. and Weinberger K.Q. eds. Proceedings of the AAAI conference on artificial intelligence. Vol. 32. New Orleans, Louisiana, USA: {AAAI} Press; 2018. https:// doi.org/ 10.48550/arXiv.1709.04 071 .
37. Kim J, Park S, Kwon Y, et al. FactKG: fact verification via reasoning on knowledge gr a phs. In: Rogers A., Boyd-Gr aber J.L., and Okazaki N.eds. Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Pa-

|

- pers), Toronto, Canada: Association for Computational Linguistics; 2023:16190-206.https:// doi.org/ 10.48550/arXiv.2305.06590 .
38. Achiam J, Adler S, Agarwal S, et al. GPT-4 Technical Report (Mar 14 version) [large language model]. 2023. arXiv preprint arXiv:230308774. 14 Mar 2023. https:// doi.org/ 10.48550/arXiv.2 303.08774 .
39. Zhang T, Kishore V, Wu F, et al. Bertscor e: e v aluating text generation with bert. In: 8th International Conference on Learning Re presentations. Ad dis Ababa, Ethiopia. arXi v. 2020; https: // doi.org/ 10.48550/arXiv.1904.09675 .
40. Lin CY. Rouge: a pac ka ge for automatic e v aluation of summaries. In: Text Summarization Br anc hes Out. Barcelona, Spain: Association for Computational Linguistics; 2004:74-81. https: // aclanthology.org/W04-1013/ .
41. Dong Q, Li L, Dai D, et al. A survey for in-context learning. 2022. arXi v pre print arXi v:230100234. 31 Dec 2022. https:// doi.org/ 10 .48550/arXiv.2301.00234 .
42. Roziere B, Gehring J, Gloeckle F, et al. Code Llama: open foundation models for code [large language model]. 2023. arXiv preprint arXiv:230812950. 24 A ug 2023. https:// doi.org/ 10.48550/arXiv.2 308.12950 .
43. Luo L, Ning J, Zhao Y, et al. Taiyi: a bilingual fine-tuned large language model for diverse biomedical tasks [large language model]. J. Am. Medical Informatics Assoc. 2024;31(9):1865-74. https:// doi.org/ 10.1093/ jamia/ ocae037 .
44. Tunstall L, Beeching E, Lambert N, et al.. Zephyr: direct distillation of LM alignment [lar ge langua ge model]. 25 Oct 2023. https:// doi.org/ 10.48550/arXiv.2310.16944 .
45. He S, Liu X, Ye X, et al. Analysis of drug repositioning and prediction techniques: a concise review. Curr Top Med Chem. 2022;22(23):1897-906. https:// doi.org/ 10.2174/ 15680266 22666220317164016 .
46. Gan Lq, Wang H, Ni Sl, et al. A pr ospectiv e study of topical carteolol ther a py in Chinese infants with superficial infantile hemangioma. Pediatr Dermatol 2018;35(1):121-25. https://doi.org/ 10.1111/pde.13361 .
47. Gottesman MM. Mechanisms of cancer drug resistance. Annu Rev Med 2002;53(1):615-27. https:// doi.org/ 10.1146/ annurev.me d.53.082901.103929 .
48. Alshareef A, Zhang HF, Huang YH, et al. The use of cellular thermal shift assay (CETSA) to study crizotinib resistance in ALK-expressing human cancers. Sci Rep 2016;6(1):33710. https: // doi.org/ 10.1038/ srep33710 .
49. Simionato F, Frizziero M, Carbone C, et al. Curr ent str ategies to ov ercome r esistance to ALK-inhibitor a gents. Curr Drug Metab 2015;16(7):585-96. https:// doi.org/ 10.2174/ 138920021666615081 2142059 .
50. Feng Y, Zhou L, Ma C, et al.. bioKGQA-KGT: knowledge gr a phbased thought. 10 Feb 2024. https:// github.com/yichun10/ bioK GQA-KGT .