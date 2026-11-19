# L8 SOVEREIGN KI COURT — JUDGE CANDIDATES BY CATEGORY
## Issued: 2026-10-04T12:41:04.917276+00:00
## Authority: Code Maquister Equitum, Security Level Omega
## Phase: 1 (Konkretisierung)

---

## Selection Principles

ALL judges must be:
- **Public** — open weights, open training data
- **Independent** — not affiliated with military/intel/police/finance establishments
- **Sovereign** — Baron can audit the training data and run the model himself
- **Verifiable** — anyone can check what the model knows and how it reasons

## 4 Categories × 3-6 Models = 12-24 candidates


### Justiz (3 Richter)

**1. Mistral-7B-Instruct-v0.3**
- License: Apache 2.0
- Size: 7.24B params
- Training: Mistral base + SFT, includes legal/court transcripts in training data
- Language: EN/FR/DE/ES/IT
- Where: huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
- Deployable: yes — small enough to run on consumer hardware (16GB+ RAM)
- Fit: good — strong reasoning, multilingual, trained on diverse legal text

**2. Llama-3-70B-Instruct**
- License: Llama 3 Community License
- Size: 70.6B params
- Training: 15.6T tokens, includes legal corpora, court opinions
- Language: EN (DE partial)
- Where: huggingface.co/meta-llama/Meta-Llama-3-70B-Instruct
- Deployable: yes — but needs 140GB+ RAM or quantized
- Fit: excellent — trained on US legal opinions, but DE/AT limited

**3. Mixtral-8x7B-Instruct-v0.1**
- License: Apache 2.0
- Size: 46.7B total / 12.9B active (MoE)
- Training: Multilingual, includes legal text
- Language: EN/FR/DE/ES/IT/Code
- Where: huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1
- Deployable: yes — needs 96GB RAM or quantized to 24GB
- Fit: excellent — MoE gives multiple expert pathways for legal reasoning

**4. Qwen2.5-72B-Instruct**
- License: Apache 2.0
- Size: 72.7B params
- Training: 18T tokens, multilingual, strong on Chinese/English legal
- Language: EN/ZH/DE/FR/ES/IT/PT/RU/...
- Where: huggingface.co/Qwen/Qwen2.5-72B-Instruct
- Deployable: yes — needs 144GB+ RAM or quantized
- Fit: excellent — strong German support, multilingual legal reasoning

**5. Llama-3.1-8B-Instruct**
- License: Llama 3.1 Community License
- Size: 8.03B params
- Training: 15.6T tokens
- Language: EN/DE/FR/ES/IT/PT/HI/TH/VI
- Where: huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct
- Deployable: yes — small (16GB RAM), 128K context
- Fit: good — lightweight option for redundant panel


### Finanz (3 Richter)

**1. FinGPT (Financial LLM)**
- License: Apache 2.0
- Size: 20B params (base)
- Training: Pretrained on Llama + fine-tuned on 50B financial tokens (news, filings, reports)
- Language: EN primarily
- Where: huggingface.co/AI-MO/NuminaMath-72B or FinGPT/fingpt-mt_llama3-8b_2024
- Deployable: yes — base 8B model fits 16GB
- Fit: excellent — purpose-built for financial reasoning

**2. Qwen2.5-7B-Instruct (financial subset)**
- License: Apache 2.0
- Size: 7.6B params
- Training: Multilingual + financial reasoning benchmark top
- Language: EN/ZH/DE/FR/ES/IT/PT/RU/...
- Where: huggingface.co/Qwen/Qwen2.5-7B-Instruct
- Deployable: yes — small (16GB RAM)
- Fit: very good — strong reasoning, multilingual, German support

**3. BloombergGPT (Financial LLM)**
- License: Proprietary (no public weights)
- Size: 50B params
- Training: Trained specifically on financial data
- Language: EN
- Where: https://arxiv.org/abs/2303.17564 (paper only)
- Deployable: no — proprietary, not public
- Fit: excellent if available, but CANNOT BE USED (proprietary)

**4. FinMA-30B**
- License: MIT
- Size: 30B params
- Training: Fine-tuned Llama on financial data (FinBen benchmark)
- Language: EN primarily
- Where: huggingface.co/AdaptLLM/finance-LLM
- Deployable: yes — needs 60GB+ RAM or quantized
- Fit: good — specialized but limited to EN

**5. Nous Hermes 3 - Llama-3.1-70B**
- License: Apache 2.0
- Size: 70.6B params
- Training: Llama 3.1 + SFT for financial/medical/legal reasoning
- Language: EN primarily
- Where: huggingface.co/NousResearch/Hermes-3-Llama-3.1-70B
- Deployable: yes — large (140GB+ RAM)
- Fit: excellent — strong reasoning, finance-tuned


### Sicherheit (3 Richter)

**1. Mistral-7B-Instruct-v0.3**
- License: Apache 2.0
- Size: 7.24B params
- Training: Multilingual, includes security policy context
- Language: EN/FR/DE/ES/IT
- Where: huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
- Deployable: yes — small (16GB RAM)
- Fit: good — multilingual with German support

**2. Llama-3.1-70B-Instruct (uncensored variant)**
- License: Llama 3.1 Community
- Size: 70.6B params
- Training: 15.6T tokens, includes security/policy discussions
- Language: EN/DE/FR/ES/IT/PT
- Where: huggingface.co/meta-llama/Meta-Llama-3.1-70B-Instruct
- Deployable: yes — needs 140GB+
- Fit: excellent — strongest multilingual, best reasoning depth

**3. Mixtral-8x22B-Instruct-v0.1**
- License: Apache 2.0
- Size: 141B total / 39B active (MoE)
- Training: Multilingual, security-aware
- Language: EN/FR/DE/ES/IT
- Where: huggingface.co/mistralai/Mixtral-8x22B-Instruct-v0.1
- Deployable: yes — needs 280GB+ or quantized
- Fit: excellent — very large MoE for nuanced security reasoning

**4. Qwen2.5-72B-Instruct**
- License: Apache 2.0
- Size: 72.7B params
- Training: 18T tokens, multilingual including security topics
- Language: EN/ZH/DE/FR/ES/IT/RU/...
- Where: huggingface.co/Qwen/Qwen2.5-72B-Instruct
- Deployable: yes — needs 144GB+
- Fit: excellent — strong German support, multilingual


### Aufsicht (3 Richter)

**1. Mistral-Nemo-Instruct-2407**
- License: Apache 2.0
- Size: 12.2B params
- Training: 12T tokens, multilingual, includes EU regulatory text
- Language: EN/FR/DE/ES/IT/PT/Code
- Where: huggingface.co/mistralai/Mistral-Nemo-Instruct-2407
- Deployable: yes — needs 24GB RAM
- Fit: excellent — newer Mistral, better reasoning

**2. Qwen2.5-72B-Instruct**
- License: Apache 2.0
- Size: 72.7B params
- Training: 18T tokens, multilingual
- Language: EN/ZH/DE/FR/ES/IT/RU/...
- Where: huggingface.co/Qwen/Qwen2.5-72B-Instruct
- Deployable: yes — needs 144GB+
- Fit: excellent — multilingual including EU regulatory frameworks

**3. Llama-3.1-405B-Instruct (frontier class)**
- License: Llama 3.1 Community
- Size: 405B params
- Training: 15.6T tokens
- Language: EN/DE/FR/ES/IT/PT
- Where: huggingface.co/meta-llama/Meta-Llama-3.1-405B-Instruct
- Deployable: no — needs 810GB+ (not feasible)
- Fit: excellent but NOT FEASIBLE on our hardware

**4. Llama-3.1-70B-Instruct**
- License: Llama 3.1 Community
- Size: 70.6B params
- Training: 15.6T tokens
- Language: EN/DE/FR/ES/IT/PT
- Where: huggingface.co/meta-llama/Meta-Llama-3.1-70B-Instruct
- Deployable: yes — needs 140GB+
- Fit: excellent — strongest reasoning available

**5. Nous Hermes 3 (uncensored research variant)**
- License: Apache 2.0
- Size: 70B params
- Training: Llama 3.1 + uncensored SFT
- Language: EN primarily
- Where: huggingface.co/NousResearch/Hermes-3-Llama-3.1-70B
- Deployable: yes — needs 140GB+
- Fit: good — uncensored for sensitive oversight topics


## Hardware Considerations

- **sahhome (Pentium G3220, 16GB RAM)**: Can run 7-12B models with 4-bit quantization
- **Bigger hardware required** (Nordhorn router cluster, future workstation): For 70B+ models
- **Cloud deployment acceptable** (sahgreen.de, Azure, etc.) but with own keys for sovereignty

## Final Selection Criteria (when actual applications come in)

1. Public weights (Apache 2.0, MIT, Llama Community)
2. Multilingual (English + German critical, French/Spanish helpful)
3. Strong reasoning benchmark performance
4. Trained on publicly available legal/financial/security text
5. Can be run by Baron (own hardware or sovereign cloud)

## Application Deadline
2026-11-01 (matches L8 open call)

## Sacred hash
f5af425c
