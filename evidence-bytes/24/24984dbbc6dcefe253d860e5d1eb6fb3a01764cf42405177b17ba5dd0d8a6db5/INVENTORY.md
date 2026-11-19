# SAH Vault — Key Inventory
# Generated 2026-08-29 from /home/sah/Downloads/API Key/
# DO NOT PUT ACTUAL KEY VALUES IN THIS FILE. Use it as an index.

## Active keys (chmod 600, originals at ~/.config/sah-vault/*.legacy)

| Provider | File | Env Var | Notes |
|---|---|---|---|
| OpenAI (multi) | API Key Openai.txt | OPENAI_API_KEY | sk-pro / sk-svc / sk-adm — at least 3 active production keys |
| xAI / Grok | API KeyGrokDatcenter.txt | XAI_API_KEY / GROK_API_KEY | xai-dN…peQ2, datacenter tier |
| Ollama | Ollama API +ssh key.txt | OLLAMA_API_KEY | ollama.com turbo key, baronki account |
| Ubuntu Pro | UbuntuPro Token.txt + Tokenubuntupro.txt | — | Pro subscription token C1wf…25T |
| SSH (mheydtcs) | SSH Key.txt | — | ED25519, fingerprint SHA256:z4ggIT+9…Y2k, account mheydtcs |

## Migrated references
- Tailscale keys: ~/.config/tailscale/ (machine-managed)
- GitHub PAT: present in ~/.bashrc / env — see `gh auth status` and GITHUB_PERSONAL_ACCESS_TOKEN
- HF token: see HuggingfaceTokenandloginData.md (~/Dokumente)
- TDAI bridge token: kiswarm-knowledge.md (in ~/.hermes)

## Rotation recommendation
Old hardware broke → assume ALL keys on this machine are compromised.
1. Rotate OpenAI keys first (most cost-critical)
2. Rotate xAI, then Ollama
3. Re-issue Ubuntu Pro token
4. Re-generate SSH key and re-distribute to authorized hostsAdded Flint3 router entry
