---
title: "DALK: Dynamic Co-Augmentation of LLMs and KG to answer Alzheimer's Disease Questions with Scientific Literature"
authors: "Dawei Li, Shu Yang  ∗, Zhen Tan, Jae Young Baik, Sunkwon Yun, Joseph Lee, Aaron Chacko, Bojian Hou, Duy Duong-Tran, Ying Ding, Huan Liu, Li Shen, Tianlong Chen"
source: "2405.04819v1.pdf"
status: converted
---

## DALK: Dynamic Co-Augmentation of LLMs and KG to answer Alzheimer's Disease Questions with Scientific Literature

Dawei Li 1 * , Shu Yang 2 ∗ , Zhen Tan 1 , Jae Young Baik 2 , Sunkwon Yun 3 , Joseph Lee 2 , Aaron Chacko 2 , Bojian Hou 2 , Duy Duong-Tran 2,4 , Ying Ding 5 , Huan Liu 1 † , Li Shen 2† , Tianlong Chen 3†

1 School of Computing, and Augmented Intelligence, Arizona State University

2 Department of Biostatistics, Epidemiology and Informatics, University of Pennsylvania Perelman School of Medicine

3 Department of Computer Science, The University of North Carolina at Chapel Hill

4 Department of Mathematics, United States Naval Academy

5

School of Information, The University of Texas at Austin, Austin

## Abstract

Recent advancements in large language models (LLMs) have achieved promising performances across various applications. Nonetheless, the ongoing challenge of integrating long-tail knowledge continues to impede the seamless adoption of LLMs in specialized domains. In this work, we introduce DALK, a.k.a. Dynamic Co-Augmentation of LLMs and KG, to address this limitation and demonstrate its ability on studying Alzheimer's Disease (AD), a specialized sub-field in biomedicine and a global health priority. With a synergized framework of LLM and KG mutually enhancing each other, we first leverage LLM to construct an evolving AD-specific knowledge graph (KG) sourced from AD-related scientific literature, and then we utilize a coarse-to-fine sampling method with a novel self-aware knowledge retrieval approach to select appropriate knowledge from the KG to augment LLM inference capabilities. The experimental results, conducted on our constructed AD question answering (ADQA) benchmark, underscore the efficacy of DALK. Additionally, we perform a series of detailed analyses that can offer valuable insights and guidelines for the emerging topic of mutually enhancing KG and LLM. We will release the code and data at https://github.com/David-Li0406/DALK.

## 1 Introduction

Alzheimer's Disease (AD) is a neurodegenerative disorder characterized by progressive declines in cognitive and functional status over a span of decades (Report, 2023). However, current AD therapy developments are facing critical challenges due to the lack of knowledge and understanding of the underlying etiological mechanisms of the disease. Although scientific literature and dedicated biomedical databases could supply rich sources of

* Equal Constributions

† Corresponding authors

AD knowledge, manual review of relevant information is impossible due to the large volume.

As large language models (LLMs) (Brown et al., 2020; Zhang et al., 2022; Anil et al., 2023; Touvron et al., 2023) with chain-of-thought (CoT)-based prompting (Wei et al., 2022; Wang et al., 2022; Tong et al., 2023; Yao et al., 2023; Besta et al., 2023) demonstrate strong language capabilities across various tasks, there have been attempts to leverage LLMs-based systems in general biomedical and AD-related applications (Mao et al., 2023; Li et al., 2023c; Yan et al., 2024; Feng et al., 2023). However, while the LLMs have shown promising performances in many general tasks, recent studies revealed LLMs' limitations in long-tail (Kandpal et al., 2023) and domain-specific (Li et al., 2023b, 2024) knowledge, thereby significantly impeding their adaptations in vertical fields such as AD. To deal with this issue, the most common strategies are retrieval augmented generation (RAG) and domainspecific LLMs training.

Nevertheless, directly applying these strategies in the context like AD would still suffer from several issues. First, Data Quality : As in many biomedical fields, scientific literature composes the largest publicly available corpus source in AD. Yet, the dense and information-overloaded nature of scientific literature, when combined with automatic retrieval methods, can lead to the retrieval of irrelevant and noisy information. Previous research has shown that noisy and irrelevant corpora can significantly undermine the performance of LLMs (Yu et al., 2023; Chen et al., 2024; Wu et al., 2024). Second, Efficiency &amp; Scale Issues : Being an critical field of research, the knowledge of AD is rapidly evolving with scientific advancements at a remarkable pace and scale. However, retraining a domain-specific LLM or updating certain knowledge in it demands substantial computational resources (Hu et al., 2021; Ovadia et al., 2023; Zhang et al., 2024). This efficiency issue would also limit the sizes of domain-specific LLMs, consequently affecting their performances.

To tackle these limitations, here we propose a Dynamic Co-Augmentation of LLMs and KG (DALK) framework that facilitates mutual benefits between LLMs and knowledge graphs (KG) for the AD domain. Initially, our framework addresses the data quality challenge by extracting more structural and accurate knowledge from unstructured and dense scientific literature and constructing a domain-specific knowledge graph tailored to AD. We employ two widely utilized knowledge graph construction methods, namely pair-wise construction (Carta et al., 2023; Wadhwa et al., 2023) and generative construction (Han et al., 2023; Bi et al., 2024), to comprehensively assess their impact on knowledge graph quality. Then, we adopt a coarseto-fine sampling method with a novel self-aware knowledge retrieval approach to select appropriate knowledge from the knowledge graph and thus further address the data quality problem. Notably, the tuning-free nature of our framework significantly enhances efficiency and facilitates its application in large-scale and API-based language models (OpenAI, 2022). In the evaluation section, we derive an Alzheimer's Disease question answering (ADQA) benchmark from existing general medical QA datasets with millions of samples filtered by a curated keyword list and selfsampling of LLMs. Our extensive experiment on ADQAdemonstrates the effectiveness of our framework in domain-specific applications compared with general biomedical LLMs and retrieval augmented models. Further evaluation and analysis provide valuable insights into constructing highquality knowledge graphs and sampling accurate knowledge from them.

In summary, our contribution in this work can be summarized as follows:

- Weidentify the constraints of the current methods for LLMs in domain-specific areas like AD and introduce DALK, a co-augmentation framework of the LLM and KG to address these issues.
- We build AD-specific KG and QA benchmark. Through extensive comparisons with other methods, we showcase the effectiveness of DALK.
- We delve into a comprehensive analysis of our proposed method and provide valuable

insights and guidance on how to construct a high-quality KG and sample accurate knowledge from it.

## 2 Related Work

The interplay between LLMs and KGs KGs (Miller, 1995; Speer et al., 2017; Vrandeˇ ci´ c and Krötzsch, 2014) serve as structured representations of factual knowledge, typically expressed as (head, relation, tail) triples. Their structured, factual, and interpretable nature renders them excellent complements to parametric language models (Pan et al., 2024). Recently, with the rise of large language models (LLMs), numerous studies have delved into exploring the synergy between LLMs and KGs for various purposes (Pan et al., 2024; Tan et al., 2024). There are a lot of efforts in conducting knowledge graph construction (Carta et al., 2023; Wadhwa et al., 2023; Han et al., 2023; Bi et al., 2024; Datta et al., 2024), completion (Wei et al., 2023; Zhang et al., 2023b; Li et al., 2024) with the aid of LLMs. Conversely, other works aim to enhance LLMs by integrating knowledge sampled from KGs during both training (Tang et al., 2023; Luo et al., 2024; Dernbach et al., 2024; Rangel et al., 2024) and inference (Kim et al., 2023; Wen et al., 2023; Jiang et al., 2023; Sun et al., 2023a) times. Our work distinguishes itself by proposing a co-augmentation framework for LLMs and KGs, facilitating their mutual enhancement, and applying it to the domain of AD.

LLMs and KGs for AD research LLMs and KGs have both been applied to Alzheimer's Disease research in previous studies. Pre-trained language models are utilized to work on AD detection and many other related tasks based on speech recordings and transcripts (Balagopalan et al., 2020; Agbavor and Liang, 2022), electronic health records (EHRs) (Mao et al., 2023; Li et al., 2023c; Yan et al., 2024), and tabular data (Feng et al., 2023). KGs have been widely used in biomedical research, yet only a few are specifically for AD research (Romano et al., 2023; Pu et al., 2023; Hsieh et al., 2023; Nian et al., 2022; Daluwatumulle et al., 2023). These KGs were generally constructed from a variety of information derived from heterogeneous biomedical databases (e.g. for genes, drugs, pathways, etc.) or scientific literature related to AD. Despite the aforementioned efforts for LLMs and KGs in AD research, no prior study has explored using LLM to augment AD-KG, or vice versa, let alone the potential for mutual enhancement between the two as we propose here.

## 3 Our Methodology

This section elaborates on our dynamic coaugmentation framework of LLMs and KG. Section 3.1 presents the details of augmenting an ADspecific evolving KG with LLMs and literature corpus in a time-slicing fashion (i.e. year by year). Following it, Section 3.2 describes the process of sampling appropriate knowledge from the evolving KG to enhance LLMs' reasoning. Figure 1 illustrates an overall pipeline of our method DALK.

Table 1: Detailed statistics about our augmented knowledge graph.

|            | KG pair   | KG gen   |
|------------|-----------|----------|
| #Corpus    | 9,764     | 9,764    |
| #Nodes     | 13,509    | 20,545   |
| #Relations | 3,952     | 3,651    |
| #Triples   | 171,431   | 53,585   |

## 3.1 LLMs for KG

Corpus Collection To create an AD-specific knowledge graph, we follow (Pu et al., 2023) and use the AD corpus collected by a domain expert Professor Colin Masters at the University of Melbourne who discovered amyloid proteins being the potential cause of AD (Masters et al., 1985). The corpus is based on his extensive bibliography of representative AD-related papers and consists of more than 16K PMID (PubMed ID)-indexed articles from 1977 to 2021. For our study, we focus on the papers since 2011 which reflect the most recent knowledge in the field and get 9,764 articles.

Entity Recognition In order to identify knowledge at the proper granularity level for AD, we extract relevant entities from the corpus by utilizing the PubTator Central (PTC) (Wei et al., 2013) developed and continuously maintained by NCBI. PTC is a widely-used tool to provide state-of-theart annotations of biomedical concepts for PubMed abstracts and full-text articles, and it supports six bioconcept types including genes, diseases, chemicals, mutations, species and cell lines. We apply PTC to the abstracts of all our AD papers and obtain the relevant named entities which will serve as nodes in the knowledge graph.

Relation Extraction To build an accurate and high-quality knowledge graph on AD, we aim to assign a specific relation type between the two related entities. Through a comprehensive survey of relation extraction methods for knowledge graph construction, we categorize current approaches with LLMs into two main groups: (a). Pair-wised Relation Extraction (Carta et al., 2023; Wadhwa et al., 2023) aims to prompt the LLMs to describe the relationship between any two entities in a segment of text. (b). Generative Relation Extraction (Han et al., 2023; Bi et al., 2024; Datta et al., 2024), where LLMs directly output all related entity pairs and their corresponding relationships. As shown in Figure 2, we incorporate both of these relation extraction methods into our knowledge graph augmentation process to provide a comprehensive comparison between them. We denote the resulting knowledge graphs from these approaches as KG pair and KG gen respectively.

Table 1 presents the detailed statistics about our augmented knowledge graph, including the number of corpora we used, and the number of nodes, relations and triples in KG pair and KG gen .

## 3.2 KGfor LLMs

In this section, we begin by outlining our process for sampling coarse-grained augmented knowledge from our evolving knowledge graph (Section 3.2.1). Subsequently, we delve into detail regarding our self-aware knowledge retrieval method, which aims to filter out noise and retrieve the most pertinent knowledge to provide to the LLM (Section 3.2.2).

## 3.2.1 Coarse-grained Knowledge Sample

Given a question query Q , we first construct a prompt and ask LLMs to extract all the domainspecific entities E = { e 1 , e 2 , ... } from it. Afterward, we adhere to the methodology proposed by Wen et al. (2023) and execute a similarity-based entity linking process to connect all entities within E to the entity structure in our knowledge graph G . Specifically, we employ a semantic similarity model (Reimers and Gurevych, 2019) to encode all entities in G and E into dense embeddings, denoted as H G and H E , respectively. Subsequently, utilizing cosine similarity, we establish links between each entity in E and its nearest neighbor entity in G . This procedure yields an initial entity set E G for the subsequent knowledge sampling step.

To build an evidence sub-graph to boost LLMs' reasoning process, we follow the previous

<!-- image -->

Figure 1: The overview pipeline of DALK. We first extract structural knowledge from unstructured corpora and construct a domain-specific knowledge graph tailored to AD (Section 3.1). Then, we utilize a coarse-to-fine sampling method with a novel self-aware knowledge retrieval approach to select appropriate knowledge from the knowledge graph (Section 3.2).

<!-- image -->

Pair-wised Relation Extraction

Figure 2: The detailed process of AD-specific KG construction.

study (Wen et al., 2023) and consider the following two kinds of explorations in our AD-KG:

Path-based Exploration entails the extraction of a sub-graph from G to encompass all entities within E G . The process unfolds as follows: (a) Begin by selecting one node from e 0 Q as the initial node, denoted as e 1 , and place the remaining nodes into a candidate node set, E cand . Explore at most k hops from e 1 to identify the subsequent node, e 2 , where e 1 ∈ E cand . If e 2 is successfully reached within k hops, update the start node to e 2 and remove e 2 from E cand . In the event e 2 cannot be found within k hops, concatenate the segment paths acquired thus far and store them in G path Q . Subsequently, choose another node e ′ 1 from V cand as the new start node, and eliminate both the original start node e 1 and the current node e 2 from E cand . (b) Verify if E cand is empty. If not, repeat step (a) to identify the next segment of the path. If E cand is empty, combine all segments to construct a set of subgraphs and place them into G path Q .

Neighbor-based Exploration endeavors to augment the evidence relevant to the query within G Q . This process consists of two steps: (a) Initially, expand each node e within E G by 1-hop to incorporate their neighbors e ′ , thus appending triples ( e, r, e ′ ) to G nei Q . (b) Then assess whether each e ′ exhibits semantic relevance to the query. If affirmative, further expand the 1-hop neighbors of e ′ , consequently adding triples ( e nei , r ′ , e ′ ) to G nei Q .

After obtaining the two sub-graphs G path Q and G nei Q , we perform post-processing to further prune redundant information in sub-graphs and prompt LLMs to describe the structure of each sub-graph.

## 3.2.2 Self-aware Knowledge Retrieval

In our initial experiment, we noticed the coarsegrained knowledge sampled with the abovementioned approaches still contained redundant and irrelevant information. This issue of noise is a common challenge encountered in automaticallyconstructed knowledge graphs (Fang et al., 2021; Zhang et al., 2020; Li et al., 2022; Bi et al., 2024).

Moreover, many recent works (Yu et al., 2023; Li et al., 2023d; Chen et al., 2024; Wu et al., 2024) have demonstrated LLMs can indeed be influenced by such noisy information. To address this challenge, we borrow insights from the recent selfpowered LLMs (Wang et al., 2022; Pan et al., 2023; Li et al., 2023a; Yuan et al., 2024; Tong et al., 2024) and propose a self-aware knowledge retrieval method to leverage LLMs' ranking capability (Sun et al., 2023b; Ma et al., 2023) to filter out noisy information.

In particular, we directly prompt the LLM to rerank the sampled knowledge and only retrieve top k triples to provide for itself in the final-round inference. Given the question Q and either the pathbased or neighbor-based sub-graph G Q , we create prompt p self by filling the pre-defined template:

<!-- formula-not-decoded -->

Then, we use p self as the input to prompt the LLM to obtain the self-retrieved knowledge:

<!-- formula-not-decoded -->

Finally, we provide the question Q and fine-grained knowledge G self Q to the LLM for reasoning and get the predicted answer a in two steps:

<!-- formula-not-decoded -->

<!-- formula-not-decoded -->

Weprovide detailed examples in Appendix A and B to demonstrate the input and output in our DALK.

## 4 Main Experiment

## 4.1 ADQA Benchmark

For performance evaluation, we consider four widely-used medical QA datasets spanning diverse biomedical topics (Jin et al., 2021; Pal et al., 2022; Hendrycks et al., 2021; Peñas et al., 2013) and derive an AD-specific QA dataset from them. The four medical QA datasets are all multiple-choice based and include: 1) MedQA (Jin et al., 2021) consisting of US Medical Licensing Examination (USMLE)-style questions, 2) MedMCQA (Pal et al., 2022) containing medical school entrance exam questions from India, 3) MMLU (Hendrycks et al., 2021) consisting of diverse biomedical and clinical questions from various sources, 4) QA4MRE (Peñas et al., 2013) containing a subset of questions for AD derived from PubMed and Medline. In order to extract from the medical QA datasets a subset of samples related to AD for our evaluation, we referred to NIH's Common Alzheimer's and Related Dementias Research Ontology (CADRO) 1 . Jointly developed by the National Institute on Aging and the Alzheimer's Association, CADRO is a three-tiered classification system with eight main categories and a dozen sub-categories for AD and related dementia, and it contains common terminologies or keywords used in the field. We derived from the CADRO a list of AD-related keywords most relevant to the medical QA datasets: &lt;Aging, Alzheimer, Amyloid beta, APOE, Dementia, Lipoprotein, Microglia&gt;. Then, we searched against each medical QA dataset for matches with these keywords to find putative QA samples, then further asked GPT-3.5-turbo to judge for each putative sample whether the question is indeed related to AD or not. Finally, we filtered out a subset of such samples that are considered highly relevant to AD to conduct our evaluation (number of samples in each dataset is shown in Table 2). More details about ADQA can be found in Appendix C.

## 4.2 Experiment Settings

We apply our framework with OpenAI GPT-3.5turbo models (OpenAI, 2022). We also include the following baseline methods for comparison:

Biomedical LLMs Both ChatDoctor (Yunxiang et al., 2023) and Med-Alpaca (Shu et al., 2023) are fine-tuned versions of LLaMA (Touvron et al.) on biomedical corpora. Compared with them, Meditron (Chen et al., 2023) is built on LLaMA2 (Touvron et al., 2023) and extends its pretraining on a comprehensively curated medical corpus. BiomedGPT (Zhang et al., 2023a) is also based on LLaMA-2 and pioneer as the first opensource and generalist visual language AI for diverse biomedical tasks. Biomistral (Labrak et al., 2024) is an open-source LLM crafted specifically for the biomedical domain, optimized for efficiency through quantization and model merging techniques.

Retrieval-Augmented LLMs Furthermore, we also compare our method with several representative retrieval-augmented LLMs in the biomedical domain. Almanac (Zakka et al., 2024) is a novel approach utilizing OpenAI's GPT model in-

1 https://iadrp.nia.nih.gov/about/cadro

Table 2: Experiment results on our constructed ADQA benchmark. The sample size is indicated after each dataset name. The best results of each metric are in bold and the second-best results are underlined. The 'A VG' column represents the average accuracy score on the four sub-dataset.

|                                     | MedQA   | MedMCQA   | MMLU   | QA4MRE   | AVG   |
|-------------------------------------|---------|-----------|--------|----------|-------|
| Biomedical LLMs                     |         |           |        |          |       |
| ChatDoctor (Yunxiang et al., 2023)  | 25.7    | 36.4      | 46.9   | 51.4     | 40.1  |
| Med-Alpaca (Shu et al., 2023)       | 41.4    | 42.8      | 44.9   | 57.1     | 46.5  |
| BiomedGPT (Zhang et al., 2023a)     | 38.8    | 41.9      | 48.9   | 42.6     | 43.1  |
| Meditron (Chen et al., 2023)        | 27.6    | 31.4      | 36.7   | 25.7     | 30.4  |
| Biomistral (Labrak et al., 2024)    | 44.7    | 49.5      | 53.1   | 68.6     | 54.0  |
| Retrieval-augmented LLMs            |         |           |        |          |       |
| GPT-3.5-turbo w/ Ada (OpenAI, 2024) | 57.2    | 65.7      | 83.7   | 62.9     | 67.4  |
| Almanac (Zakka et al., 2024)        | 48.0    | 69.5      | 71.4   | 60.0     | 62.2  |
| Clinfo.ai (Lozano et al., 2023)     | 54.3    | 77.0      | 81.3   | 67.7     | 70.1  |
| Clinfo.ai w/o PubMed API            | 49.3    | 68.6      | 79.6   | 74.3     | 67.9  |
| GPT-3.5-turbo                       | 50.0    | 71.9      | 83.6   | 62.9     | 67.1  |
| DALK                                | 57.9    | 75.2      | 85.4   | 71.4     | 72.6  |

tegrated with a Qdrant vector database to hold external sources of knowledge retrieved from local corpus, web search, and calculators, designed to answer open-domain clinical questions. Like Almanac, Lozano et al. (2023) introduced Clinfo.ai, which is an open-source, end-to-end retrievalaugmented LLM (GPT) to answer medical queries using scientific literature summarizations derived from PubMed search engine. We adopt both Almanac and Clinfo.ai with the same prompt as ours to answer multiple-choice questions to suit the ADQA benchmark. Lastly, we implement a simple retrieval-augmented GPT baseline with CoT prompting similar to our proposed DALK. All the GPT models used are set to GPT-3.5-turbo as detailed in the next paragraph, to be consistent.

Implementation Details We use the knowledge graph constructed with the generative approach ( KG gen ) in our main experiment and conduct an ablation study on the knowledge graph with RE method ( KG pair ) in Section 4.5. We use GPT-3.5turbo with the version 'gpt-3.5-turbo-0301' and set the sampling temperature to 0.7. We utilize 7B versions of all the biomedical LLMs baselines. For RAG methods, we split each document with a max length of 128 and retrieve the top 3 most relevant documents as the support evidence for LLMs to do inference. We set the parameter k in our selfaware knowledge retrieval to 5 and conduct further analysis on it in Section 5.2.

## 4.3 Main Result

Table 2 shows the experimental results on our ADQAbenchmark. We note that upon applying our dynamic co-augmentation framework, DALK's performance surpasses that of other biomedical LLMs and RAG methods overall. It consistently achieves either the best or the second-best accuracy score across all sub-datasets and attains the highest A VG score. Furthermore, the substantial improvement over vanilla GPT-3.5-turbo underscores the efficacy of our approach in domain-specific ADQA.

Furthermore, we observe that the performance of biomedical-specific LLMs generally lags behind that of GPT-3.5-turbo. We attribute this discrepancy to the smaller size of these biomedical LLMs. While they may perform adequately in general medical contexts, they fall short in the AD scenario, which demands more domain-specific knowledge. In the case of GPT-3.5-turbo combined with various RAG methods, it is evident that most RAG methods enhance the models' performance. Among them, GPT-3.5-turbo with Clinfo.ai yields the most significant improvement, boosting the accuracy score from 67.1 to 70.1 compared to vanilla GPT-3.5-turbo. However, it is important to note that the original Clinfo.ai necessitates access to the PubMed API, constituting an external resource. When we disable this access and solely utilize the same corpora as in DALK within the Clinfo.ai retrieval system, the improvement it brings becomes marginal and incomparable to our method. Due to the space limitation, we put more RAG results with different hyper-parameters in Appendix D.

## 4.4 Ablation Study on Self-aware Knowledge Retrieval

In this section, we evaluate the efficacy of our proposed self-aware knowledge retrieval method through an ablation study. As depicted in Table 3, we observe that while the dynamic coaugmentation framework without the self-aware

Table 3: Ablation study results with and without our proposed self-aware knowledge retrieval.

|                     |   MedQA |   MedMCQA |   MMLU |   QA4MRE |   AVG |
|---------------------|---------|-----------|--------|----------|-------|
| AVG Length          |   107.4 |      23.8 |  342.9 |     17.6 | 122.9 |
| GPT-3.5-turbo       |    50   |      71.9 |   83.6 |     62.9 |  67.1 |
| DALK                |    57.9 |      75.2 |   85.4 |     71.4 |  72.6 |
| DALK w/o self-aware |    56.5 |      71   |   77.6 |     77.1 |  70.6 |

knowledge retrieval module still enhances the model's performance, the overall improvement is less pronounced. Furthermore, we observe that the efficacy of self-aware knowledge retrieval correlates with the length of queries within a given context. For instance, a notable enhancement in performance is evident within the MMLU sub-dataset upon the implementation of self-aware knowledge retrieval. We attribute this to the fact that questions in the MMLU dataset typically contain longer contexts compared to other medical QA datasets integrated into ADQA. Consequently, irrelevant knowledge sourced from the context may exacerbate the issue of information noise thus underscoring the necessity for self-aware retrieval. Conversely, within QA4MRE, characterized by shorter query lengths, the application of self-aware knowledge retrieval can even lead to a decline in performance.

## 4.5 Ablation Study on KG Construction

Table 4: Ablation study results with generative construction and RE construction.

|                       |   AVG | #Triples   |
|-----------------------|-------|------------|
| GPT-3.5-turbo         |  67.1 | -          |
| DALK w/ Generative KG |  72.6 | 53,585     |
| DALK w/ RE KG         |  66.3 | 171,431    |

Table 4 illustrates the results of the ablation study conducted using generatively constructed KG and RE-constructed KG. Surprisingly, despite the RE method yielding a KG with a larger scale and more triples, knowledge sampled from it has unexpectedly resulted in a non-trivial drop in performance within ADQA. After a manual examination of the two constructed knowledge graphs, we find LLMs with the RE construction method have a strong inclination to wrongly assign a relationship to two unrelated entities, which has been exposed by the previous studies (Wan et al., 2023). In contrast, the generative construction approach exclusively outputs triples that LLMs confidently endorse, yielding a smaller yet more precise knowledge graph.

This trade-off between coverage and accuracy underscores the critical importance of denoising in the construction of KGs by LLMs.

## 5 Further Analysis

## 5.1 Co-augmentation Analysis

Accuracy (%)

Figure 3: The size of the knowledge graph (triplet number) and the KG-augmented GPT-3.5-turbo's performance (accuracy) over time.

<!-- image -->

To comprehensively understand how the performance of LLMs evolves in response to increasing KGsizes, we undertake a detailed co-augmentation analysis. Illustrated in Figure 3, our experiments aim to discern the changing performance trends of LLMs as the knowledge triples accumulate annually. Our findings reveal that our framework effectively fosters the co-evolution of LLMs and KG, with the performance of KG-augmented LLMs exhibiting a generally upward trajectory as the KG expands. Notably, when we remove the self-aware knowledge retrieval module, this upward trend becomes less significant. This further implies the importance of sampling and selecting appropriate knowledge for LLMs when the KG's size increases.

## 5.2 Hyper-parameter Analysis

In this section, we do a hyper-parameter analysis on the retrieval number k of our self-aware retrieval module. We select a group of value for k ([1,3,5,10,20,30]) and present the experiment results in Figure 4. We show the accuracy score on MedQA, MedMCQA, QA4MRE and AVG with different k . We find when k is small, an increment to it can lead to a performance enhancement. After the best performance shows up, continually increasing the value of k will cause a smooth decrease in the model accuracy score. This result indicates the knowledge ranked in the top positions

Table 5: A case to show the effectiveness of DALK. The question is: 'The area of the brain resistant to Neurofibrillary tangles of Alzheimer's disease is: A. Visual association areas B. Entorhinal coex C. Temporal lobe D.Lateral geniculate body'

|                                          | Path-based Sub-graph                                                                                                                                                                                                | Answer   |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| Baseline                                 | -                                                                                                                                                                                                                   | C %      |
| DALK -w/o self-aware knowledge retrieval | neurofibrillary tangles->FORM BY->microtubule-associated protein tau... ... entorhinal cortex->is a part of->brain->ASSOCIATES->mouse with Alzheimer's disease->brain region->temporal lobe                         | C %      |
| DALK                                     | Reranked Triples1: entorhinal cortex ->is a part of ->brain Reranked Triples2: entorhinal cortex ->associates ->mouse with Alzheimer's disease Reranked Triples3: temporal lobe ->affected by ->Alzheimer's disease | D !      |

Figure 4: Different self-aware knowledge retrieval settings in MedQA, MedMCQA, QA4MRE and the average score (AVG).

<!-- image -->

is more helpful while the knowledge ranked behind is something not very useful, thus successfully validating the capability of LLMs to do a fine-grained knowledge reranking.

Moreover, we find the best k value is correlated with the length of queries in each single dataset. For example, the best performance in MedQA (average query length is 107.4) shows up when k = 10 while the best performance in MedMCQA and QA4MRE shows up when k = 5 and 3 respectively. This is consistent with our findings in Section 4.4 that a longer query corresponds to a larger and noisier sub-knowledge graph.

## 5.3 Sensitivity Analysis on ADQA Benchmark

In this section, we conduct a sensitivity analysis for our constructed ADQA by conducting a leaveone-out evaluation on AD-related keywords. We do it by removing the samples with each keyword in our keyword list and calculating the A VG score of the remaining samples. As the result shown in Table 6, we find not all of the keywords are incorporated in our ADQA benchmark. Notably,

Table 6: Sensitivity analysis for ADQA benchmark with a leave-one-out evaluation on AD-related keywords.

| Benchmark          | DALK   | DALK                               |
|--------------------|--------|------------------------------------|
|                    | DALK   | w/o self-aware knowledge retrieval |
| ADQA               | 72.6   | 70.6                               |
| w/o 'Alzheimer'    | 72.1   | 70.4                               |
| w/o 'Dementia'     | 72.4   | 71.3                               |
| w/o 'APOE'         | 73.2   | 71.2                               |
| w/o 'Amyloid beta' | 73.5   | 70.7                               |
| w/o 'Aging'        | 72.9   | 71.4                               |
| w/o 'Lipoprotein'  | 73.1   | 71.0                               |
| w/o 'Microglia'    | 72.8   | 70.9                               |

the keywords 'CSF Biomarkers', 'Neurogenesis', 'PET Amyloid', 'PET Tau', 'Tau Phosphorylation' lack corresponding samples in ADQA. We believe one critical work in the future for benchmarking AD-related knowledge is to collect QA samples to cover these missing keywords. Moreover, analyzing the performance variation upon removing samples linked to each keyword offers insight into determining the relevance of the keyword to AD.

## 5.4 Case Study

We put an example in Table 5 to showcase the efficacy of DALK. We notice while the path-based subgraph contains the relevant knowledge to exclude option C, it still involves other irrelevant information and finally fails to prompt the LLMs to produce the correct answer. In contrast, our self-aware knowledge retrieval method successfully chooses the top 3 most relevant triples for the given problem and results in the correct answer D.

## 6 Conclusion

In this research, we begin by analyzing the main limitations of adopting the existing LLMs-based methods in AD-specific areas. To address these issues, we propose a novel approach in the merging of large language models and knowledge graphs in the context of Alzheimer's Disease. Our team provides an innovative dynamic co-augmentation framework for the refinement of large language models and knowledge graphs. Initially, our approach extracts structural insights from the unstructured scientific literature, crafting a specialized knowledge graph for AD. Subsequently, we employ a coarse-to-fine sampling technique coupled with a unique self-aware knowledge retrieval strategy to pinpoint relevant information from the knowledge graph. The extensive evaluation conducted in our constructed ADQA benchmark showcases the effectiveness of our method and provides further hints into the synergy of LLMs and knowledge graph in the context of AD. In the future, we will do more exploration in adopting and benchmarking LLMs in the AD areas.

## 7 Limitations

In the development of our AD-KG, our primary focus lies in the exploration of two distinct methods for extracting relationships between associated entities. For entity recognition, we employ a strong PubTator annotator directly, without delving into the utilization of LLMs in this context. However, we have observed that LLMs also exhibit promising entity extraction capabilities in Section 3.2.1. We defer the refinement of methods for extracting entities for KG construction with LLMs to future works. Furthermore, a significant contribution of our work is the establishment of the ADQA benchmark. Nonetheless, the datasets utilized in constructing ADQA primarily consist of medical school exam questions, potentially exhibiting a domain gap from the scientific literature informing AD-KG. One potential remedy is leveraging PubmedQA (Jin et al., 2019); however, it is hindered by limited data amount. In the future, we will keep gathering AD-related QA samples and expanding the size of our ADQA benchmark.

## 8 Ethics Statement

We have familiarized ourselves with and honour the ethical code set out in the ACL Code of Ethics 2 . The knowledge graphs constructed in the paper are based on published scientific literature from PubMed. The ADQA dataset used in the study is also derived from publicly available medical QA datasets that are properly cited. We strive to ensure our study upholds ethical principles and not cause any kind of safety or privacy concerns. Although

2 https://www.aclweb.org/portal/content/acl-code-ethics

not observed in our multiple-choice QA analysis, we recognize the possibility of factual errors and hallucinations when using pre-trained LLMs for medical QA tasks in general, and we do not recommend these models be applied in a practical setting at present.

## References

Felix Agbavor and Hualou Liang. 2022. Predicting dementia from spontaneous speech using large language models. PLOS Digital Health , 1:1-14.

Rohan Anil, Andrew M Dai, Orhan Firat, Melvin Johnson, Dmitry Lepikhin, Alexandre Passos, Siamak Shakeri, Emanuel Taropa, Paige Bailey, Zhifeng Chen, et al. 2023. Palm 2 technical report. arXiv preprint arXiv:2305.10403 .

Aparna Balagopalan, Benjamin Eyre, Frank Rudzicz, and Jekaterina Novikova. 2020. To BERT or not to BERT: Comparing Speech and Language-Based Approaches for Alzheimer's Disease Detection. In Proc. Interspeech 2020 , pages 2167-2171.

Maciej Besta, Nils Blach, Ales Kubicek, Robert Gerstenberger, Lukas Gianinazzi, Joanna Gajda, Tomasz Lehmann, Michal Podstawski, Hubert Niewiadomski, Piotr Nyczyk, et al. 2023. Graph of thoughts: Solving elaborate problems with large language models. arXiv preprint arXiv:2308.09687 .

Zhen Bi, Jing Chen, Yinuo Jiang, Feiyu Xiong, Wei Guo, Huajun Chen, and Ningyu Zhang. 2024. Codekgc: Code language model for generative knowledge graph construction. ACM Transactions on Asian and Low-Resource Language Information Processing , 23(3):1-16.

Tom Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared D Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. 2020. Language models are few-shot learners. Advances in neural information processing systems , 33:1877-1901.

Salvatore Carta, Alessandro Giuliani, Leonardo Piano, Alessandro Sebastian Podda, Livio Pompianu, and Sandro Gabriele Tiddia. 2023. Iterative zero-shot llm prompting for knowledge graph construction. arXiv preprint arXiv:2307.01128 .

Jiawei Chen, Hongyu Lin, Xianpei Han, and Le Sun. 2024. Benchmarking large language models in retrieval-augmented generation. In Proceedings of the AAAI Conference on Artificial Intelligence , volume 38, pages 17754-17762.

Zeming Chen, Alejandro Hernández Cano, Angelika Romanou, Antoine Bonnet, Kyle Matoba, Francesco Salvi, Matteo Pagliardini, Simin Fan, Andreas Köpf, Amirkeivan Mohtashami, et al. 2023. Meditron-70b: Scaling medical pretraining for large language models. arXiv preprint arXiv:2311.16079 .

- Geesa Daluwatumulle, Rupika Wijesinghe, and Ruvan Weerasinghe. 2023. In silico drug repurposing using knowledge graph embeddings for alzheimer's disease. In Proceedings of the 9th International Conference on Bioinformatics Research and Applications , ICBRA '22, page 61-66, New York, NY, USA. Association for Computing Machinery.
- Preetha Datta, Fedor Vitiugin, Anastasiia Chizhikova, and Nitin Sawhney. 2024. Construction of hyperrelational knowledge graphs using pre-trained large language models. arXiv preprint arXiv:2403.11786 .
- Stefan Dernbach, Khushbu Agarwal, Alejandro Zuniga, Michael Henry, and Sutanay Choudhury. 2024. Glam: Fine-tuning large language models for domain knowledge graph alignment via neighborhood partitioning and generative subgraph encoding. arXiv preprint arXiv:2402.06764 .
- Tianqing Fang, Hongming Zhang, Weiqi Wang, Yangqiu Song, and Bin He. 2021. Discos: bridging the gap between discourse knowledge and commonsense knowledge. In Proceedings of the Web Conference 2021 , pages 2648-2659.
- Yingjie Feng, Xiaoyin Xu, Yueting Zhuang, and Min Zhang. 2023. Large language models improve alzheimer's disease diagnosis using multi-modality data. In 2023 IEEE International Conference on Medical Artificial Intelligence (MedAI) , pages 61-66. IEEE.
- Jiuzhou Han, Nigel Collier, Wray Buntine, and Ehsan Shareghi. 2023. Pive: Prompting with iterative verification improving graph-based generative capability of llms. arXiv preprint arXiv:2305.12392 .
- Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. 2021. Measuring massive multitask language understanding. In International Conference on Learning Representations .
- Daniel Scott Himmelstein, Antoine Lizee, Christine Hessler, Leo Brueggeman, Sabrina L Chen, Dexter Hadley, Ari Green, Pouya Khankhanian, and Sergio E Baranzini. 2017. Systematic integration of biomedical knowledge prioritizes drugs for repurposing. Elife , 6:e26726.
- Kang-Lin Hsieh, German Plascencia-Villa, Ko-Hong Lin, George Perry, Xiaoqian Jiang, and Yejin Kim. 2023. Synthesize heterogeneous biological knowledge via representation learning for alzheimer's disease drug repurposing. iScience , 26(1):105678.
- Edward J Hu, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, Weizhu Chen, et al. 2021. Lora: Low-rank adaptation of large language models. In International Conference on Learning Representations .
- Jinhao Jiang, Kun Zhou, Zican Dong, Keming Ye, Wayne Xin Zhao, and Ji-Rong Wen. 2023. Structgpt: A general framework for large language model to
- reason over structured data. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 9237-9251.
- Di Jin, Eileen Pan, Nassim Oufattole, Wei-Hung Weng, Hanyi Fang, and Peter Szolovits. 2021. What disease does this patient have? a large-scale open domain question answering dataset from medical exams. Applied Sciences , 11(14):6421.
- Qiao Jin, Bhuwan Dhingra, Zhengping Liu, William W Cohen, and Xinghua Lu. 2019. Pubmedqa: A dataset for biomedical research question answering. arXiv preprint arXiv:1909.06146 .
- Nikhil Kandpal, Haikang Deng, Adam Roberts, Eric Wallace, and Colin Raffel. 2023. Large language models struggle to learn long-tail knowledge. In International Conference on Machine Learning , pages 15696-15707. PMLR.
- Jiho Kim, Yeonsu Kwon, Yohan Jo, and Edward Choi. 2023. Kg-gpt: A general framework for reasoning on knowledge graphs using large language models. In Findings of the Association for Computational Linguistics: EMNLP 2023 , pages 9410-9421.
- Yanis Labrak, Adrien Bazoge, Emmanuel Morin, PierreAntoine Gourraud, Mickael Rouvier, and Richard Dufour. 2024. Biomistral: A collection of opensource pretrained large language models for medical domains. arXiv preprint arXiv:2402.10373 .
- Dawei Li, Yanran Li, Jiayi Zhang, Ke Li, Chen Wei, Jianwei Cui, and Bin Wang. 2022. C3kg: A chinese commonsense conversation knowledge graph. In Findings of the Association for Computational Linguistics: ACL 2022 , pages 1369-1383.
- Dawei Li, Yaxuan Li, Dheeraj Mekala, Shuyao Li, Xueqi Wang, William Hogan, Jingbo Shang, et al. 2023a. Dail: Data augmentation for incontext learning via self-paraphrase. arXiv preprint arXiv:2311.03319 .
- Dawei Li, Zhen Tan, Tianlong Chen, and Huan Liu. 2024. Contextualization distillation from large language model for knowledge graph completion. arXiv preprint arXiv:2402.01729 .
- Dawei Li, Hengyuan Zhang, Yanran Li, and Shiping Yang. 2023b. Multi-level contrastive learning for script-based character understanding. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 5995-6013.
- Rumeng Li, Xun Wang, and Hong Yu. 2023c. Two directions for clinical data generation with large language models: Data-to-label and label-to-data. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 7129-7143.
- Yucheng Li, Bo Dong, Frank Guerin, and Chenghua Lin. 2023d. Compressing context to enhance inference efficiency of large language models. In Proceedings
- of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 6342-6353.
- Alejandro Lozano, Scott L Fleming, Chia-Chun Chiang, and Nigam Shah. 2023. Clinfo. ai: An open-source retrieval-augmented large language model system for answering medical questions using scientific literature. In PACIFIC SYMPOSIUM ON BIOCOMPUTING 2024 , pages 8-23. World Scientific.
- Xindi Luo, Zequn Sun, Jing Zhao, Zhe Zhao, and Wei Hu. 2024. Knowla: Enhancing parameter-efficient finetuning with knowledgeable adaptation. arXiv preprint arXiv:2403.14950 .
- Yubo Ma, Yixin Cao, Yong Hong, and Aixin Sun. 2023. Large language model is not a good few-shot information extractor, but a good reranker for hard samples! In Findings of the Association for Computational Linguistics: EMNLP 2023 , pages 10572-10601.
- Chengsheng Mao, Jie Xu, Luke Rasmussen, Yikuan Li, Prakash Adekkanattu, Jennifer Pacheco, Borna Bonakdarpour, Robert Vassar, Li Shen, Guoqian Jiang, Fei Wang, Jyotishman Pathak, and Yuan Luo. 2023. Ad-bert: Using pre-trained language model to predict the progression from mild cognitive impairment to alzheimer's disease. Journal of Biomedical Informatics , 144:104442.
- C L Masters, G Simms, N A Weinman, G Multhaup, B L McDonald, and K Beyreuther. 1985. Amyloid plaque core protein in alzheimer disease and down syndrome. Proceedings of the National Academy of Sciences , 82(12):4245-4249.
- George A Miller. 1995. Wordnet: a lexical database for english. Communications of the ACM , 38(11):39-41.
- Yi Nian, Xinyue Hu, Rui Zhang, Jingna Feng, Jingcheng Du, Fang Li, Yong Chen, and Cui Tao. 2022. Mining on alzheimer's diseases related knowledge graph to identity potential ad-related semantic triples for drug repurposing. BMC Bioinformatics , 23.
- OpenAI. 2022. Introducing chatgpt.
- OpenAI. 2024. New embedding models and api updates.
- Oded Ovadia, Menachem Brief, Moshik Mishaeli, and Oren Elisha. 2023. Fine-tuning or retrieval? comparing knowledge injection in llms. arXiv preprint arXiv:2312.05934 .
- Ankit Pal, Logesh Kumar Umapathi, and Malaikannan Sankarasubbu. 2022. Medmcqa: A large-scale multisubject multi-choice dataset for medical domain question answering. In Proceedings of the Conference on Health, Inference, and Learning , volume 174 of Proceedings of Machine Learning Research , pages 248-260. PMLR.
- Liangming Pan, Michael Saxon, Wenda Xu, Deepak Nathani, Xinyi Wang, and William Yang Wang. 2023. Automatically correcting large language models: Surveying the landscape of diverse self-correction strategies. arXiv preprint arXiv:2308.03188 .
- Shirui Pan, Linhao Luo, Yufei Wang, Chen Chen, Jiapu Wang, and Xindong Wu. 2024. Unifying large language models and knowledge graphs: A roadmap. IEEE Transactions on Knowledge and Data Engineering .
- Anselmo Peñas, Eduard H. Hovy, Pamela Forner, Álvaro Rodrigo, Richard F. E. Sutcliffe, and Roser Morante. 2013. Qa4mre 2011-2013: Overview of question answering for machine reading evaluation. In International Conference of the Cross-Language Evaluation Forum for European Languages , pages 303-320. Springer.
- Yiyuan Pu, Daniel Beck, and Karin Verspoor. 2023. Graph embedding-based link prediction for literaturebased discovery in alzheimer's disease. Journal of Biomedical Informatics , 145:104464.
- Julio C Rangel, Tarcisio Mendes de Farias, Ana Claudia Sima, and Norio Kobayashi. 2024. Sparql generation: an analysis on fine-tuning openllama for question answering over a life science knowledge graph. arXiv preprint arXiv:2402.04627 .
- Nils Reimers and Iryna Gurevych. 2019. Sentence-bert: Sentence embeddings using siamese bert-networks. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP) , pages 3982-3992.
- Alzheimer's Association Report. 2023. 2023 alzheimer's disease facts and figures. Alzheimer's &amp;Dementia , 19(4):1598-1695.
- Joseph Romano, Van Truong, Rachit Kumar, Mythreye Venkatesan, Britney Graham, Yun Hao, Nick Matsumoto, Xi Li, Zhiping Wang, Marylyn Ritchie, Li Shen, and Jason Moore. 2023. The alzheimer's knowledge base - a knowledge graph for therapeutic discovery in alzheimer's disease research (preprint). Journal of Medical Internet Research .
- Chang Shu, Baian Chen, Fangyu Liu, Zihao Fu, Ehsan Shareghi, and Nigel Collier. 2023. Visual medalpaca: A parameter-efficient biomedical llm with visual capabilities.
- Robyn Speer, Joshua Chin, and Catherine Havasi. 2017. Conceptnet 5.5: An open multilingual graph of general knowledge. In Proceedings of the AAAI conference on artificial intelligence , volume 31.
- Jiashuo Sun, Chengjin Xu, Lumingyuan Tang, Saizhuo Wang, Chen Lin, Yeyun Gong, Heung-Yeung Shum, and Jian Guo. 2023a. Think-on-graph: Deep and responsible reasoning of large language model with knowledge graph. arXiv preprint arXiv:2307.07697 .
- Weiwei Sun, Lingyong Yan, Xinyu Ma, Shuaiqiang Wang, Pengjie Ren, Zhumin Chen, Dawei Yin, and Zhaochun Ren. 2023b. Is chatgpt good at search? investigating large language models as re-ranking agents. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 14918-14937.
- Zhen Tan, Alimohammad Beigi, Song Wang, Ruocheng Guo, Amrita Bhattacharjee, Bohan Jiang, Mansooreh Karami, Jundong Li, Lu Cheng, and Huan Liu. 2024. Large language models for data annotation: A survey. arXiv preprint arXiv:2402.13446 .
- Jiabin Tang, Yuhao Yang, Wei Wei, Lei Shi, Lixin Su, Suqi Cheng, Dawei Yin, and Chao Huang. 2023. Graphgpt: Graph instruction tuning for large language models. arXiv preprint arXiv:2310.13023 .
- Yongqi Tong, Dawei Li, Sizhe Wang, Yujia Wang, Fei Teng, and Jingbo Shang. 2024. Can llms learn from previous mistakes? investigating llms' errors to boost for reasoning. arXiv preprint arXiv:2403.20046 .
- Yongqi Tong, Yifan Wang, Dawei Li, Sizhe Wang, Zi Lin, Simeng Han, and Jingbo Shang. 2023. Eliminating reasoning via inferring with planning: A new framework to guide llms' non-linear thinking. arXiv preprint arXiv:2310.12342 .
- Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothee Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models.
- Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. 2023. Llama 2: Open foundation and fine-tuned chat models. arXiv preprint arXiv:2307.09288 .
- Denny Vrandeˇ ci´ c and Markus Krötzsch. 2014. Wikidata: a free collaborative knowledgebase. Communications of the ACM , 57(10):78-85.
- Somin Wadhwa, Silvio Amir, and Byron C Wallace. 2023. Revisiting relation extraction in the era of large language models. In Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) , pages 1556615589.
- Zhen Wan, Fei Cheng, Zhuoyuan Mao, Qianying Liu, Haiyue Song, Jiwei Li, and Sadao Kurohashi. 2023. Gpt-re: In-context learning for relation extraction using large language models. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 3534-3547.
- Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc V Le, Ed H Chi, Sharan Narang, Aakanksha Chowdhery, and Denny Zhou. 2022. Self-consistency improves chain of thought reasoning in language models. In The Eleventh International Conference on Learning Representations .
- Chih-Hsuan Wei, Hung-Yu Kao, and Zhiyong Lu. 2013. Pubtator: a web-based text mining tool for assisting biocuration. Nucleic acids research , 41(W1):W518W522.
- Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, et al. 2022. Chain-of-thought prompting elicits reasoning in large language models. Advances in Neural Information Processing Systems , 35:24824-24837.
- Yanbin Wei, Qiushi Huang, Yu Zhang, and James Kwok. 2023. Kicgpt: Large language model with knowledge in context for knowledge graph completion. In Findings of the Association for Computational Linguistics: EMNLP 2023 , pages 8667-8683.
- Yilin Wen, Zifeng Wang, and Jimeng Sun. 2023. Mindmap: Knowledge graph prompting sparks graph of thoughts in large language models. arXiv preprint arXiv:2308.09729 .
- Siye Wu, Jian Xie, Jiangjie Chen, Tinghui Zhu, Kai Zhang, and Yanghua Xiao. 2024. How easily do irrelevant inputs skew the responses of large language models? arXiv preprint arXiv:2404.03302 .
- Chao Yan, Monika Grabowska, Alyson Dickson, Bingshan Li, Zhexing Wen, Dan Roden, C. Stein, Peter Embí, Josh Peterson, Qiping Feng, Bradley Malin, and Wei-Qi Wei. 2024. Leveraging generative ai to prioritize drug repurposing candidates for alzheimer's disease with real-world clinical validation. npj Digital Medicine , 7.
- Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L Griffiths, Yuan Cao, and Karthik Narasimhan. 2023. Tree of thoughts: Deliberate problem solving with large language models. arXiv preprint arXiv:2305.10601 .
- Wenhao Yu, Hongming Zhang, Xiaoman Pan, Kaixin Ma, Hongwei Wang, and Dong Yu. 2023. Chain-ofnote: Enhancing robustness in retrieval-augmented language models. arXiv preprint arXiv:2311.09210 .
- Weizhe Yuan, Richard Yuanzhe Pang, Kyunghyun Cho, Sainbayar Sukhbaatar, Jing Xu, and Jason Weston. 2024. Self-rewarding language models. arXiv preprint arXiv:2401.10020 .
- Li Yunxiang, Li Zihan, Zhang Kai, Dan Ruilong, and Zhang You. 2023. Chatdoctor: A medical chat model fine-tuned on llama model using medical domain knowledge. arXiv preprint arXiv:2303.14070 .
- Cyril Zakka, Rohan Shad, Akash Chaurasia, Alex R Dalal, Jennifer L Kim, Michael Moor, Robyn Fong, Curran Phillips, Kevin Alexander, Euan Ashley, et al. 2024. Almanac-retrieval-augmented language models for clinical medicine. NEJM AI , 1(2):AIoa2300068.
- Hengyuan Zhang, Yanru Wu, Dawei Li, Zacc Yang, Rui Zhao, Yong Jiang, and Fei Tan. 2024. Balancing speciality and versatility: a coarse to fine framework for supervised fine-tuning large language model. arXiv preprint arXiv:2404.10306 .
- Hongming Zhang, Xin Liu, Haojie Pan, Yangqiu Song, and Cane Wing-Ki Leung. 2020. Aser: A large-scale eventuality knowledge graph. In Proceedings of the web conference 2020 , pages 201-211.
- Kai Zhang, Jun Yu, Zhiling Yan, Yixin Liu, Eashan Adhikarla, Sunyang Fu, Xun Chen, Chen Chen, Yuyin Zhou, Xiang Li, et al. 2023a. Biomedgpt: A unified and generalist biomedical generative pre-trained transformer for vision, language, and multimodal tasks. arXiv preprint arXiv:2305.17100 .
- Susan Zhang, Stephen Roller, Naman Goyal, Mikel Artetxe, Moya Chen, Shuohui Chen, Christopher Dewan, Mona Diab, Xian Li, Xi Victoria Lin, et al. 2022. Opt: Open pre-trained transformer language models. arXiv preprint arXiv:2205.01068 .
- Yichi Zhang, Zhuo Chen, Wen Zhang, and Huajun Chen. 2023b. Making large language models perform better in knowledge graph completion. arXiv preprint arXiv:2310.06671 .

## A Details of LLMs for KG

Table 7 and 8 present examples of our two KG construction methods respectively. For both methods, we adopt a select-or-generate prompt to instruct the LLM whether to choose a relation from hetionet (Himmelstein et al., 2017), a well-built general medical KG, or generate a new one to describe the relationship between two entities. In the RE construction method, we also conduct a type matching (Table 9) for each entity from type name of PubTator to that of Hetionet and ask the LLM to choose from the relation set that corresponds to the two entities' types (Table 10).

Table 7: An example to extract knowledge triples using generative construction method.

| Input   | Read the following abstract, extract the relationships between each entity.You can choose the relation from: (covaries, interacts, regulates, resembles, downregulates, upregulates, associates, binds, treats, palliates), or generate a new predicate to describe the relationship between the two entities. Output all the extract triples in the format of "head | relation | tail". For example: "Alzheimer's disease | associates | memory deficits" Abstract: Thiamine pyrophosphate (TPP) and the activities of thiamine-dependent enzymes are reduced in Alzheimer's disease (AD) patients. In this study, we analyzed the relationship between thiamine deficiency (TD) and amyloid precursor protein (APP) processing in both cellular and animal models of TD. In SH-SY5Y neuroblastoma cells overexpressing APP, TD promoted maturation of beta-site APP cleaving enzyme 1 (BACE1) and increased beta-secretase activity which resulted in elevated levels of beta-amyloid (Abeta) as well as beta-secretase cleaved C-terminal fragment (beta-CTF). An inhibitor of beta-secretase efficiently reduced TD-induced up-regulation of Abeta and beta-CTF. Importantly, thiamine supplementation reversed the TD-induced alterations. Furthermore, TD treatment caused a significant accumulation of reactive oxygen species (ROS); antioxidants suppressed ROS production and maturation of BACE1, as well as TD-induced Abeta accumulation. On the other hand, exogenous Abeta(1-40) enhanced TD- induced production of ROS. A study on mice indicated that TD also caused Abeta accumulation in the brain, which was reversed by thiamine supplementation. Taken together, our study suggests that TD could enhance Abeta generation by promoting beta-secretase activity, and the accumulation of Abeta subsequently exacerbated TD-induced oxidative stress.Entity: Thiamine (thiamine), deficiency increases beta- secretase, TPP (Thiamine pyrophosphate), Alzheimer's disease (AD), patients, amyloid precursor protein (beta-amyloid (Abeta)), neuroblastoma, BACE1 (beta-site APPcleaving enzyme 1), Abeta, ROS(reactive oxygen species), Abeta accumulation,   |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Output  | Thiamine deficiency | downregulates | TPP, Thiamine deficiency | regulates | Alzheimer's disease, Alzheimer's disease | involves | beta-secretase, Amyloid precur- sor protein | produces | beta-amyloid, Amyloid precursor protein | in | neuroblastoma, BACE1 | is | beta-secretase, BACE1 | regulates | beta-amyloid, Abeta | is | beta- amyloid, Abeta | in | mice, Abeta | causes | reactive oxygen species, Abeta | regulates | ROS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

Input

Read the following abstract, answer the following question. Abstract: Thiamine pyrophosphate (TPP) and the activities of thiamine-dependent enzymes are reduced in Alzheimer's disease (AD) patients. In this study, we analyzed the relationship between thiamine deficiency (TD) and amyloid precursor protein (APP) processing in both cellular and animal models of TD. In SH-SY5Y neuroblastoma cells overexpressing APP, TD promoted maturation of beta-site APP cleaving enzyme 1 (BACE1) and increased beta-secretase activity which resulted in elevated levels of beta-amyloid (Abeta) as well as beta-secretase cleaved C-terminal fragment (betaCTF). An inhibitor of beta-secretase efficiently reduced TD-induced up-regulation of Abeta and beta-CTF. Importantly, thiamine supplementation reversed the TDinduced alterations. Furthermore, TD treatment caused a significant accumulation of reactive oxygen species (ROS); antioxidants suppressed ROS production and maturation of BACE1, as well as TD-induced Abeta accumulation. On the other hand, exogenous Abeta(1-40) enhanced TD-induced production of ROS. A study on mice indicated that TD also caused Abeta accumulation in the brain, which was reversed by thiamine supplementation. Taken together, our study suggests that TD could enhance Abeta generation by promoting beta-secretase activity, and the accumulation of Abeta subsequently exacerbated TD-induced oxidative stress.Entity: Thiamine (thiamine), deficiency increases beta-secretase, TPP (Thiamine pyrophosphate), Alzheimer's disease (AD), patients, amyloid precursor protein (beta-amyloid (Abeta)), neuroblastoma, BACE1 (beta-site APP cleaving enzyme 1), Abeta, ROS (reactive oxygen species), Abeta accumulation, mice. Question: predict the relationship between Disease entity "sclerosis" and Disease entity "multiple sclerosis", first choose from the following options: A. resembles B. no-relation C. others, please specify by generating a short predicate in 5 words. Answer: Let's think step by step:

Output 1. Sclerosis is a disease of the central nervous system. 2. Multiple sclerosis is the most common form of sclerosis. 3. So the relationship between sclerosis and multiple sclerosis should be "sclerosis is a kind of multiple sclerosis". So the answer is: A. resembles. So the answer is: A. resembles

Table 8: An example to extract the relationship between 'sclerosis' and 'multiple sclerosis' using RE construction method.

Table 9: Entity type match from PubTator to Hetionet.

| PubTator Type   | Hetionet Type   |
|-----------------|-----------------|
| Gene            | genes           |
| Chemical        | compounds       |
| Disease         | diseases        |

Table 10: Type-type to relation match in Hetionet.

| Type-Type                                                                                         | Relations                                                                                                                                                                         |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| genes-genes disease-disease compounds-compounds genes-diseases genes-compounds compounds-diseases | ["covaries", "interacts", "regulates"] ["resembles"] ["resembles"] ["downregulates","associates","upregulates"] ["binds", "upregulates", "downregulates"] ["treats", "palliates"] |

## B Details of KG for LLMs

In this section, we provide detailed input and output for adopting KG to augment LLMs, including path-based and neighbor-based sub-graph sampling results (Table 11), self-aware knowledge retrieval (Table 12), describing sub-graphs with LLMs (Table 13) and inference with sampled knowledge (Table 14). The question we showcase here is 'The area of the brain resistant to Neurofibrillary tangles of Alzheimer's disease is: A. Visual association areas B. Entorhinal coex C. Temporal lobe D.Lateral geniculate body', which same as the one we use in Section 5.4.

Table 11: An example of path-based and neighbor-based sub-graph for the question.

| Path-based Sub-graph     | neurofibrillary tangles->FORM BY->microtubule-associated protein tau->BINDS-> (18)F-THK-5117->ADMINISTERED TO->rats->has->Alzheimer's disease -> Alzheimer's disease ->affects->human->has->AD->DISEASE OF->Brain entorhinal cortex->is a part of->brain->ASSOCIATES-> mouse with Alzheimer's disease->brain region->temporal lobe   |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Neighbor-based Sub-graph | neurofibrillary tangles->FORM BY->microtubule-associated protein tau Alzheimer's disease ->causes->neuronal death Alzheimer's disease ->associates->cognitive decline Alzheimer's disease ->affects->human Alzheimer's disease ->has subtype->neurodegenerative diseases                                                             |

There is a question and some knowledge graph. The knowledge graphs follow entity-&gt;relationship -&gt;entity list format.

## Graph:

neurofibrillary tangles-&gt;FORM BY-&gt;microtubule-associated protein tau-&gt;BINDS-&gt; (18)F-THK-5117-&gt;ADMINISTERED TO-&gt;rats-&gt;has-&gt;Alzheimer's disease -&gt;Alzheimer's disease -&gt; affects-&gt;human-&gt;has-&gt;AD-&gt;DISEASE OF-&gt;Brain entorhinal cortex-&gt;is a part of-&gt;brain-&gt;ASSOCIATES-&gt; mouse with Alzheimer's disease-&gt;brain region-&gt;temporal lobe}

## Question:

The area of the brain resistant to Neurofibrillary tangles of Alzheimer's disease is:

A. Visual association areas

B. Entorhinal coex

C. Temporal lobe

D.Lateral geniculate body

Please rerank the knowledge graph and output at most 5 important and relevant triples for solving the given question. Output the reranked knowledge in the following format:

Reranked Triple1: xxx --&gt;xxx

Reranked Triple2: xxx --&gt;xxx

Reranked Triple3: xxx --&gt;xxx

Reranked Triple4: xxx --&gt;xxx

Reranked Triple5: xxx --&gt;xxx

## Answer:

Table 12: An example of our self-aware knowledge retrieval in path-based sub-graph.

| Output   | Reranked Triples1: entorhinal cortex ->is a part of ->brain Reranked Triples2: entorhinal cortex ->associates ->mouse with Alzheimer's disease Reranked Triples3: temporal lobe ->affected by ->Alzheimer's disease   |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

Input

Input

Output

There are some knowledge graph paths. They follow entity-&gt;relationship-&gt;entity format.

Reranked Triples1: entorhinal cortex -&gt;is a part of -&gt;brain

Reranked Triples2: entorhinal cortex -&gt;associates -&gt;mouse with Alzheimer's disease

Reranked Triples3: temporal lobe -&gt;affected by -&gt;Alzheimer's disease

Use the knowledge graph information. Try to convert them to natural language, respectively. Use single quotation marks for entity name and relation name.

And name them as Path-based Evidence 1, Path-based Evidence 2,...

## Output:

Path-based Evidence 1: 'Entorhinal cortex' is a part of 'brain'.

Path-based Evidence 2: 'Entorhinal cortex' associates 'mouse' with 'Alzheimer's disease'.

Path-based Evidence 3: 'Temporal lobe' is affected by 'Alzheimer's disease'.

Table 13: An example to describe the self-retrieved path-based sub-graph with the LLM.

Question: The area of the brain resistant to Neurofibrillary tangles of Alzheimer's disease is: A.Visual association areas

B.Entorhinal coex

C.Temporal lobe

D.Lateral geniculate body

You have some medical knowledge information in the following:

###Path-based Evidence 1: 'Entorhinal cortex' is a part of 'brain'.

Path-based Evidence 2: 'Entorhinal cortex' associates 'mouse' with 'Alzheimer's disease'.

Path-based Evidence 3: 'Temporal lobe' is affected by 'Alzheimer's disease'.

###Neighbor-based Evidence 1: 'neurofibrillary tangles' are 'FORMED BY' '

microtubule-associated protein tau'.

Neighbor-based Evidence 2: 'Alzheimer's disease' 'CAUSES' 'neuronal death'.

Neighbor-based Evidence 3: 'Alzheimer's disease' 'ASSOCIATES' with 'cognitive decline'.

Neighbor-based Evidence 4: 'Alzheimer's disease' 'AFFECTS' 'human'.

Neighbor-based Evidence 5: 'Alzheimer's disease' 'HAS SUBTYPE' 'neurodegenerative diseases'."

Answer: Let's think step by step:

In Alzheimer's disease, neurofibrillary tangles are composed of abnormal aggregations of tau protein within neurons, leading to neuronal dysfunction and eventual cell death. The lateral geniculate body is a relay center in the thalamus that processes visual information from the retina to the visual cortex. Since the lateral geniculate body is not directly involved in memory and cognitive function, it is less likely to be affected by neurofibrillary tangles in Alzheimer's disease compared to other brain regions such as the entorhinal cortex and temporal lobe which play crucial roles in memory and cognitive processing. Therefore, the area of the brain resistant to neurofibrillary tangles of Alzheimer's disease is the lateral geniculate body (option D)

Input

Output

Table 14: An example of inference with selected knowledge

## C ADQA Benchmark

Table 15 shows the detailed prompt of our self-sample method to construct ADQA benchmark. Table 16 gives the statistics of our ADQA benchmark.

Table 15: An example from MedMCQA to self-sample AD-related QA sample with LLMs.

| Input   | Judge whether the question below is related to Alzheimer's Disease. Please answer yes or no. Question: Treatable causes of dementia are ___. a).AD b).Hypothyroidism c).Multi-infarct dementia d).SDH e).Hydrocephalus Is the question related to Alzheimer's Disease? Answer:   |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Output  | Yes                                                                                                                                                                                                                                                                              |

Table 16: Statistics of our ADQA benchmark.

| Dataset   |   MedQA |   MedMCQA |   MMLU |   QA4MRE |   Total |
|-----------|---------|-----------|--------|----------|---------|
| Number    |     152 |       210 |     49 |       35 |     446 |

## D Further Experiment for RAG

Table 17: Further experiment in RAG methods with different hyper-parameter settings.

|                             |   MedQA |   MedMCQA |   NMMLU |   QA4MRE |   AVG |
|-----------------------------|---------|-----------|---------|----------|-------|
| Almanac w/ 256 chunk size   |    50   |      69   |    67.3 |     62.9 |  62.3 |
| Almanac w/ top 10 docuemnt  |    48.7 |      68.6 |    65.3 |     62.9 |  61.4 |
| Almanac w/ CoT              |    50   |      65.7 |    77.6 |     65.7 |  64.7 |
| Clinfo.ai w/ 256 chunk size |    48.6 |      66.7 |    81.6 |     65.7 |  65.7 |
| Clinfo.ai w/ top 5 docuemnt |    43.4 |      68.1 |    77.6 |     68.6 |  64.4 |
| Clinfo.ai w/ CoT            |    48.7 |      68.6 |    79.6 |     68.6 |  65   |