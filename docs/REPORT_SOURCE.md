<!--
  EDIT THIS FILE, then run:  python scripts/generate_report_docx.py
  Sections must start with a single # heading (exact names below).
  Title Page: first paragraph = report title; next paragraphs = author, institution, date (each centered in Word).
  Use blank lines between paragraphs. For References, use bullet lines starting with "- ".
  In Results, you can include a markdown table (| col | col | then |---|---| then rows).
-->

# Title Page

An AI-Assisted Multi-Agent System for Enterprise ESG Monitoring, Compliance Assessment, and Explainable Risk Scoring

Mahek Bhatia

ESG Intelligence Platform (HackAvensis26 — AI/ML Track). Replace with your institution if applicable.

April 11, 2026

# Abstract

Enterprises increasingly require timely, traceable environmental, social, and governance (ESG) insights rather than retrospective spreadsheets. This report describes the design and implementation of an ESG intelligence platform that ingests firm-level records, executes a sequential multi-agent analytics pipeline (operational standardization, financial aggregation, rule-based compliance, consolidated risk scoring with alert tiers), and augments outputs with supervised machine learning and SHAP-based explanations. Data are sourced from structured firm-year panels and MongoDB-backed storage; services are exposed via FastAPI with optional real-time channels. A random forest classifier trained on engineered high-risk labels achieves 99.4% holdout accuracy on a 1,000-row sample but exhibits low minority-class recall (40%), highlighting severe class imbalance and the need for external validation labels. The system demonstrates a practical architecture for modular ESG analytics while surfacing methodological caveats around threshold rules and label coupling. Conclusions emphasize governance-grade evaluation, temporal validation, and richer regulatory rule encodings as next steps.

# Introduction

ESG reporting and assurance are under pressure from investors, regulators, and civil society. Organizations struggle with fragmented data, delayed signals, and limited transparency into why risk indicators change. Artificial intelligence and multi-agent decomposition offer a path to scalable monitoring if combined with interpretability and auditable rules.

This report documents the ESG Intelligence Platform: a software system that operationalizes a pipeline from raw firm records to compliance flags, aggregate risk scores, and model-driven explanations.

**Research question:** How can a modular multi-agent architecture, paired with tree-based supervised learning and SHAP explanations, support enterprise ESG monitoring and compliance-oriented risk communication?

# Literature Review

Prior work spans ESG measurement and materiality (voluntary frameworks and mandatory disclosure regimes), machine learning for credit and sustainability risk from structured panels, and explainable AI for high-stakes decisions. Multi-agent and microservice patterns are widely used in industry to separate data ingestion, analytics, and presentation layers.

Gaps this project engages with include: (i) integrating rule-based compliance checks with ML risk layers in one deployable stack; (ii) exposing explanations (SHAP) alongside discrete alert tiers for non-technical stakeholders; and (iii) documenting an end-to-end reference implementation rather than a purely theoretical model. The literature also cautions against evaluating models on labels derived from the same engineered scores used as features—a limitation noted in the Discussion.

# Methodology

**Data collection and storage.** Firm-year records include E, S, and G pillar scores, financial ratios (ROA, ROE, net profit margin), industry type, year, and optional board independence. MongoDB stores raw and derived firm data; environment variables configure database and firm scope.

**Multi-agent pipeline.** Agent 1 synchronizes and standardizes columns, sorts by year and industry, and writes operational output. Agent 2 computes ESG_Score as the mean of pillar scores and a discrete financial_risk_score from sub-threshold pillar counts. Agent 3 applies deterministic threshold rules (for example, pillar score below 60; governance violations include low board independence) to produce pillar and overall compliance labels. Agent 4 maps violations to final_esg_risk_score and assigns alert_level (Low, Warning, Critical).

**Machine learning.** Labels define high risk when final_esg_risk_score is at least 66. Features are numeric columns from the training table (excluding the raw score and label). A RandomForestClassifier (100 estimators, stratified 80/20 split, random_state=42) is trained, evaluated with accuracy and a classification report, and serialized to risk_model.pkl.

**Explainability.** Agent 5 loads the forest and uses SHAP TreeExplainer to rank contributions and generate short textual rationales for top factors.

**Software integration.** FastAPI serves REST endpoints for agents; Socket.IO supports streaming-style updates; CORS is enabled for dashboard clients.

# Results

The training corpus (ML/ESG4_output.csv via models/train.py) contained 1,000 labeled rows after preprocessing. Holdout accuracy was 0.994. Per-class performance was asymmetric: the majority class (non–high-risk) achieved precision and recall of 1.00 (support 995), while the high-risk class achieved precision 0.40, recall 0.40, and F1 0.40 (support 5). Macro-averaged precision, recall, and F1 were 0.70; weighted averages tracked overall accuracy closely.

Global feature importance from the fitted forest ranked ESG_Score highest (approximately 0.89), followed by Year (approximately 0.11), indicating the model leans heavily on the composite ESG signal relative to the available numeric fields in this training slice.

| Metric | Value | Notes | Source |
| --- | --- | --- | --- |
| Holdout accuracy | 0.994 | Stratified 80/20 split | models/train.py |
| High-risk class F1 | 0.40 | 5 positive samples in test partition | Classification report output |

*(Add figures or charts here after export; Word allows paste into this section after generation.)*

# Discussion

The high overall accuracy primarily reflects class imbalance and alignment between rule-derived risk scores and the supervised target. The low F1 on the minority class shows that headline accuracy is misleading for rare-risk detection; practitioners should prioritize PR-AUC, cost-sensitive learning, or resampling, and ideally external outcome labels (for example, controversies or enforcement).

The multi-agent decomposition improves maintainability: compliance thresholds can evolve without rewriting ingestion, and explanations can be toggled when SHAP is unavailable. Limitations include simplified legal mapping (numeric thresholds versus full regulatory texts), potential label-feature leakage in the current training recipe, and the need for production hardening (authentication, audit logs, data lineage).

Implications: the architecture suits mid-market enterprises piloting continuous ESG monitoring with IT-friendly APIs, provided governance reviews threshold policies and validation protocols.

# Conclusion

This report described an implemented ESG intelligence platform combining MongoDB-backed ingestion, a four-stage rule pipeline, alert-based risk communication, random forest risk classification, and SHAP explanations, integrated through FastAPI. Empirical training results demonstrate strong aggregate accuracy but weak detection of rare high-risk rows, underscoring rigorous evaluation requirements. Future work should incorporate temporal validation, jurisdiction-specific rule packs (for example, BRSR, CSRD), multilingual disclosure NLP, and decoupled supervision targets.

# References

- Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32.
- Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS*.
- Task Force on Climate-related Financial Disclosures (TCFD). (2017). Recommendations report.
- European Commission. (2022). Corporate Sustainability Reporting Directive (CSRD) — regulatory context.
- Securities and Exchange Board of India. (2021). Business Responsibility and Sustainability Reporting (BRSR) guidance.

# Appendix (Optional)

Repository layout (abbreviated): API/ (FastAPI, agent routes, MongoDB handler), agents/ (agent1.py through agent5.py, premium ingestion), models/ (train.py, risk_model.pkl after training), ML/ (notebooks and ESG4_output.csv).

Environment variables: MONGO_URI, MONGO_DB_NAME, MONGO_FIRM_ID, MONGO_COLLECTION as documented in README deployment notes.

Reproducing model metrics: from the repository root, run `python models/train.py` (expects ML/ESG4_output.csv relative to models/). Results may vary if the dataset is updated.
